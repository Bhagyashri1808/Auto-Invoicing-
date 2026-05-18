"""API routes for document management."""

import uuid
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks, Form
from sqlalchemy.orm import Session

from api.dependencies import get_db
from models.schemas import (
    InvoiceDocumentCreate, InvoiceDocumentResponse,
    ProcessingJobCreate, ProcessingJobResponse
)
from models import InvoiceDocument, ProcessingJob
from models.enums import ProcessingStatus, FileType, ProcessingMode
from services.file_upload import FileUploadService
from services.ocr_processor import OCRProcessor
from services.data_extractor import DataExtractor
from services.llm_extractor import LLMExtractor
from services.hybrid_extractor import HybridExtractor
from services.simple_ocr_extractor import SimpleOCRExtractor
from services.fast_extractor import FastExtractor
from services.enhanced_extractor import enhanced_extractor
from services.error_handler import error_handler

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
file_upload_service = FileUploadService()
ocr_processor = OCRProcessor()
data_extractor = DataExtractor()
llm_extractor = LLMExtractor()
hybrid_extractor = HybridExtractor()
simple_extractor = SimpleOCRExtractor()
fast_extractor = FastExtractor()  # Non-hanging extractor


@router.post("/upload", response_model=InvoiceDocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    processing_mode: ProcessingMode = ProcessingMode.SEQUENTIAL,
    enable_preprocessing: bool = Form(False),  # Disabled: THRESHOLD destroys handwriting details
    preprocessing_config_id: Optional[str] = Form(None),
    enable_llm_processing: bool = Form(True),
    fallback_to_ocr: bool = Form(True),
    db: Session = Depends(get_db)
):
    """
    Upload an invoice document for processing.
    
    Args:
        file: Invoice file (PDF, JPG, PNG, TIFF)
        processing_mode: Sequential or parallel processing mode
        db: Database session
        
    Returns:
        InvoiceDocumentResponse with upload details
    """
    try:
        # Process file upload
        storage_path, file_size, file_type = await file_upload_service.process_upload(file)
        
        # Create invoice document record
        invoice_doc = InvoiceDocument(
            filename=file.filename or f"upload_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            file_path=storage_path,
            file_size=file_size,
            file_type=file_type,
            processing_status=ProcessingStatus.PENDING,
            upload_date=datetime.utcnow(),
            uploaded_at=datetime.utcnow()
        )
        
        db.add(invoice_doc)
        db.commit()
        db.refresh(invoice_doc)
        
        # Create processing job
        processing_job = ProcessingJob(
            invoice_document_id=invoice_doc.id,
            processing_mode=processing_mode,
            status=ProcessingStatus.PENDING,
            queue_position=1  # Simple queue position - in real implementation, this would be calculated
        )
        
        db.add(processing_job)
        db.commit()
        db.refresh(processing_job)
        
        # Queue enhanced background processing
        background_tasks.add_task(
            process_document_enhanced_async,
            invoice_doc.id,
            processing_job.id,
            storage_path,
            enable_preprocessing,
            preprocessing_config_id,
            enable_llm_processing,
            fallback_to_ocr
        )
        
        logger.info(f"Document uploaded successfully: {invoice_doc.id}")
        
        return InvoiceDocumentResponse.from_orm(invoice_doc)
        
    except HTTPException:
        # Re-raise HTTP exceptions from services
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/{document_id}", response_model=InvoiceDocumentResponse)
async def get_document(
    document_id: str,
    include_processing_details: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get document details by ID.
    
    Args:
        document_id: UUID of the document
        include_processing_details: Include LLM processing job details
        db: Database session
        
    Returns:
        InvoiceDocumentResponse with document details and optional processing info
    """
    try:
        # Convert string to UUID
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid document ID format"
        )
    
    document = db.query(InvoiceDocument).filter(
        InvoiceDocument.id == doc_uuid
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )
    
    return InvoiceDocumentResponse.from_orm(document)


@router.get("/", response_model=List[InvoiceDocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    status: ProcessingStatus = None,
    db: Session = Depends(get_db)
):
    """
    List documents with optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by processing status
        db: Database session
        
    Returns:
        List of InvoiceDocumentResponse objects
    """
    query = db.query(InvoiceDocument)
    
    if status:
        query = query.filter(InvoiceDocument.processing_status == status)
    
    documents = query.offset(skip).limit(limit).all()
    
    return [InvoiceDocumentResponse.from_orm(doc) for doc in documents]


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a document and its associated data.
    
    Args:
        document_id: UUID of the document
        db: Database session
        
    Returns:
        Success message
    """
    try:
        # Convert string to UUID
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid document ID format"
        )
    
    document = db.query(InvoiceDocument).filter(
        InvoiceDocument.id == doc_uuid
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )
    
    try:
        # Delete physical file
        if document.file_path:
            file_upload_service.delete_file(document.file_path)
        
        # Delete database record (cascading will handle related records)
        db.delete(document)
        db.commit()
        
        logger.info(f"Document deleted successfully: {document_id}")
        
        return {"message": "Document deleted successfully"}
        
    except Exception as e:
        logger.error(f"Delete failed for {document_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Delete failed: {str(e)}"
        )


@router.get("/{document_id}/processing-jobs", response_model=List[ProcessingJobResponse])
async def get_document_processing_jobs(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Get processing jobs for a document.
    
    Args:
        document_id: UUID of the document
        db: Database session
        
    Returns:
        List of ProcessingJobResponse objects
    """
    # Verify document exists
    document = db.query(InvoiceDocument).filter(
        InvoiceDocument.id == document_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )
    
    jobs = db.query(ProcessingJob).filter(
        ProcessingJob.invoice_document_id == document_id
    ).all()
    
    return [ProcessingJobResponse.from_orm(job) for job in jobs]


async def process_document_async(
    document_id: str,
    job_id: str,
    file_path: str
):
    """
    Background task to process document with fast extraction (no hanging).
    
    Args:
        document_id: UUID of invoice document
        job_id: UUID of processing job
        file_path: Path to uploaded file
    """
    from database.config import SessionLocal
    
    db = SessionLocal()
    try:
        # Update status to processing
        db.query(InvoiceDocument).filter(
            InvoiceDocument.id == document_id
        ).update({
            "processing_status": ProcessingStatus.PROCESSING,
            "processing_started_at": datetime.utcnow()
        })
        
        db.query(ProcessingJob).filter(
            ProcessingJob.id == job_id
        ).update({
            "status": ProcessingStatus.PROCESSING,
            "started_at": datetime.utcnow()
        })
        db.commit()
        
        # Use Fast Extractor to avoid hanging issues
        try:
            extracted_data_schema = fast_extractor.extract_structured_data(
                file_path,
                document_id
            )
            
            # Check if extraction failed
            if extracted_data_schema.extraction_confidence == 0.0 and not any([
                extracted_data_schema.vendor_name,
                extracted_data_schema.invoice_number,
                extracted_data_schema.total_amount
            ]):
                # LLM extraction failed, fall back to OCR + regex
                logger.warning("LLM extraction failed, falling back to OCR + regex")
                
                ocr_result = ocr_processor.process_document(file_path)
                
                if ocr_result.error:
                    raise Exception(f"Both LLM and OCR failed. OCR error: {ocr_result.error}")
                
                extracted_data_schema = data_extractor.extract_structured_data(
                    ocr_result.text,
                    document_id,
                    ocr_result.confidence
                )
            
        except Exception as extraction_error:
            # Both LLM and OCR failed
            error_message = f"Data extraction failed: {str(extraction_error)}"
            logger.error(error_message)
            
            db.query(InvoiceDocument).filter(
                InvoiceDocument.id == document_id
            ).update({
                "processing_status": ProcessingStatus.FAILED,
                "error_message": error_message,
                "processing_completed_at": datetime.utcnow()
            })
            
            db.query(ProcessingJob).filter(
                ProcessingJob.id == job_id
            ).update({
                "status": ProcessingStatus.FAILED,
                "error_message": error_message,
                "completed_at": datetime.utcnow()
            })
            db.commit()
            return
        
        # Save extracted data
        from models import ExtractedData, LineItem
        from uuid import UUID as UUIDType
        from models.extracted_data import ExtractedData as ExtractedDataModel

        # Convert document_id to UUID if needed
        if isinstance(document_id, str):
            document_uuid = UUIDType(document_id)
        else:
            document_uuid = document_id

        # Build extracted data dict with only known database fields
        schema_dict = extracted_data_schema.dict()
        extracted_data_create = {
            "id": uuid.uuid4(),
            "invoice_document_id": document_uuid,
            "vendor_name": schema_dict.get("vendor_name"),
            "vendor_address": schema_dict.get("vendor_address"),
            "invoice_number": schema_dict.get("invoice_number"),
            "invoice_date": schema_dict.get("invoice_date"),
            "due_date": schema_dict.get("due_date"),
            "total_amount": schema_dict.get("total_amount"),
            "tax_amount": schema_dict.get("tax_amount"),
            "subtotal_amount": schema_dict.get("subtotal_amount"),
            "currency": schema_dict.get("currency", "USD"),
            "extraction_confidence": schema_dict.get("extraction_confidence", 0.5),
            "extracted_at": datetime.utcnow(),
            "is_human_verified": False,
            # Enhanced fields with defaults for old processing path
            "extraction_method": "OCR_ONLY",
            "llm_processing_job_id": None,
            "ocr_confidence_avg": schema_dict.get("extraction_confidence"),
            "llm_confidence_score": None,
            "field_confidence_scores": {},
            "preprocessing_applied": False,
            "preprocessing_method": None,
            "validation_errors": None,
            "has_manual_corrections": False
        }

        # Filter to only include valid column names (StackOverflow solution)
        column_names = set(ExtractedDataModel.__table__.columns.keys())
        logger.info(f"Valid column names: {column_names}")
        logger.info(f"Keys in extracted_data_create: {set(extracted_data_create.keys())}")

        # Filter and log what gets removed
        filtered_data = {k: v for k, v in extracted_data_create.items() if k in column_names}
        removed_keys = set(extracted_data_create.keys()) - set(filtered_data.keys())
        if removed_keys:
            logger.warning(f"Filtered out non-column keys: {removed_keys}")

        extracted_data = ExtractedData(**filtered_data)
        db.add(extracted_data)
        db.flush()  # Get ID for line items
        
        # Save line items if any
        if hasattr(extracted_data_schema, 'line_items') and extracted_data_schema.line_items:
            for item_data in extracted_data_schema.line_items:
                line_item = LineItem(
                    id=uuid.uuid4(),  # UUID object, not string
                    extracted_data_id=extracted_data.id,
                    description=item_data.get('description'),
                    quantity=item_data.get('quantity'),
                    unit_price=item_data.get('unit_price'),
                    total_price=item_data.get('total_price'),
                    line_number=item_data.get('line_number'),
                    confidence_score=item_data.get('confidence_score', 0.0)
                )
                db.add(line_item)
        
        # Update completion status
        db.query(InvoiceDocument).filter(
            InvoiceDocument.id == document_id
        ).update({
            "processing_status": ProcessingStatus.COMPLETED,
            "processing_completed_at": datetime.utcnow()
        })
        
        db.query(ProcessingJob).filter(
            ProcessingJob.id == job_id
        ).update({
            "status": ProcessingStatus.COMPLETED,
            "completed_at": datetime.utcnow()
        })
        
        db.commit()
        logger.info(f"Document processing completed successfully: {document_id}")
        
    except Exception as e:
        # Handle processing failure
        logger.error(f"Document processing failed for {document_id}: {str(e)}")
        
        db.query(InvoiceDocument).filter(
            InvoiceDocument.id == document_id
        ).update({
            "processing_status": ProcessingStatus.FAILED,
            "error_message": str(e),
            "processing_completed_at": datetime.utcnow()
        })
        
        db.query(ProcessingJob).filter(
            ProcessingJob.id == job_id
        ).update({
            "status": ProcessingStatus.FAILED,
            "error_message": str(e),
            "completed_at": datetime.utcnow()
        })
        
        db.commit()
        
    finally:
        db.close()


async def process_document_enhanced_async(
    document_id: str,
    job_id: str,
    file_path: str,
    enable_preprocessing: bool = True,
    preprocessing_config_id: Optional[str] = None,
    enable_llm_processing: bool = True,
    fallback_to_ocr: bool = True
):
    """
    Enhanced background task to process document with preprocessing and LLM integration.
    
    Args:
        document_id: UUID of invoice document
        job_id: UUID of processing job
        file_path: Path to uploaded file
        enable_preprocessing: Whether to apply image preprocessing
        preprocessing_config_id: Optional custom preprocessing configuration
        enable_llm_processing: Whether to use LLM for extraction
        fallback_to_ocr: Whether to fallback to OCR on LLM failure
    """
    from database.config import SessionLocal
    
    db = SessionLocal()
    try:
        # Update status to processing
        db.query(InvoiceDocument).filter(
            InvoiceDocument.id == document_id
        ).update({
            "processing_status": ProcessingStatus.PROCESSING,
            "processing_started_at": datetime.utcnow()
        })
        
        db.query(ProcessingJob).filter(
            ProcessingJob.id == job_id
        ).update({
            "status": ProcessingStatus.PROCESSING,
            "started_at": datetime.utcnow()
        })
        db.commit()
        
        # Prepare preprocessing configuration
        preprocessing_config = None
        if preprocessing_config_id:
            # TODO: Load custom preprocessing configuration from database
            pass
        
        # Use enhanced extractor for processing
        try:
            result = await enhanced_extractor.extract_data(
                image_path=file_path,
                enable_preprocessing=enable_preprocessing,
                enable_llm_processing=enable_llm_processing,
                fallback_to_ocr=fallback_to_ocr,
                preprocessing_config=preprocessing_config
            )
            
            extracted_data_dict = result["extracted_data"]
            processing_metadata = result["processing_metadata"]

            # DEBUG: Print what we got from enhanced_extractor
            print("\n" + "="*80)
            print("DEBUG: Result from enhanced_extractor")
            print("="*80)
            print(f"extracted_data_dict keys: {list(extracted_data_dict.keys())}")
            print(f"Has processing_time_ms? {'processing_time_ms' in extracted_data_dict}")
            print(f"\nFull extracted_data_dict:")
            for key, value in extracted_data_dict.items():
                print(f"  {key}: {value}")
            print("="*80 + "\n")

        except Exception as extraction_error:
            # Enhanced extraction failed
            error_context = error_handler.create_error_response(extraction_error)
            error_message = f"Enhanced extraction failed: {error_context['message']}"
            logger.error(error_message)
            
            db.query(InvoiceDocument).filter(
                InvoiceDocument.id == document_id
            ).update({
                "processing_status": ProcessingStatus.FAILED,
                "error_message": error_message,
                "processing_completed_at": datetime.utcnow()
            })
            
            db.query(ProcessingJob).filter(
                ProcessingJob.id == job_id
            ).update({
                "status": ProcessingStatus.FAILED,
                "error_message": error_message,
                "completed_at": datetime.utcnow()
            })
            db.commit()
            return
        
        # Save enhanced extracted data
        from models import ExtractedData, LineItem
        from datetime import date

        # Helper function to convert string dates to date objects
        def parse_date(date_string):
            """Convert date string (YYYY-MM-DD) to Python date object."""
            if not date_string:
                return None
            if isinstance(date_string, date):
                return date_string
            try:
                from datetime import datetime as dt
                return dt.strptime(date_string, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                return None

        # Get confidence score - use LLM confidence if available, otherwise OCR
        confidence_score = extracted_data_dict.get("llm_confidence_score")
        if confidence_score is None:
            confidence_score = extracted_data_dict.get("ocr_confidence_avg", 0.5)

        # Ensure confidence score is a valid float between 0 and 1
        if not isinstance(confidence_score, (int, float)):
            confidence_score = 0.5
        confidence_score = max(0.0, min(1.0, float(confidence_score)))

        # Convert preprocessing_method from list to string
        def convert_preprocessing_method(method):
            """Convert preprocessing method from list/None to string."""
            if method is None:
                return None
            if isinstance(method, list):
                return "+".join(method) if method else None
            return str(method)

        # Create extracted data with enhanced fields
        from uuid import UUID as UUIDType
        from models.extracted_data import ExtractedData as ExtractedDataModel

        # Convert document_id to UUID if it's a string
        if isinstance(document_id, str):
            document_uuid = UUIDType(document_id)
        else:
            document_uuid = document_id

        extracted_data_create = {
            "id": uuid.uuid4(),  # UUID object, not string
            "invoice_document_id": document_uuid,
            "vendor_name": extracted_data_dict.get("vendor_name"),
            "vendor_address": extracted_data_dict.get("vendor_address"),
            "invoice_number": extracted_data_dict.get("invoice_number"),
            "invoice_date": parse_date(extracted_data_dict.get("invoice_date")),
            "due_date": parse_date(extracted_data_dict.get("due_date")),
            "total_amount": extracted_data_dict.get("total_amount"),
            "tax_amount": extracted_data_dict.get("tax_amount"),
            "subtotal_amount": extracted_data_dict.get("subtotal_amount"),
            "currency": extracted_data_dict.get("currency", "USD"),
            "extraction_confidence": confidence_score,
            "extracted_at": datetime.utcnow(),
            "is_human_verified": False,
            # Enhanced fields
            "extraction_method": extracted_data_dict.get("extraction_method", "OCR_ONLY"),
            "llm_processing_job_id": extracted_data_dict.get("llm_processing_job_id"),
            "ocr_confidence_avg": extracted_data_dict.get("ocr_confidence_avg"),
            "llm_confidence_score": extracted_data_dict.get("llm_confidence_score"),
            "field_confidence_scores": extracted_data_dict.get("field_confidence_scores", {}),
            "preprocessing_applied": extracted_data_dict.get("preprocessing_applied", False),
            "preprocessing_method": convert_preprocessing_method(extracted_data_dict.get("preprocessing_method")),
            "validation_errors": None,
            "has_manual_corrections": False
        }

        # Filter to only include valid column names (StackOverflow solution)
        column_names = set(ExtractedDataModel.__table__.columns.keys())
        logger.info(f"Valid column names: {column_names}")
        logger.info(f"Keys in extracted_data_create: {set(extracted_data_create.keys())}")

        # Filter and log what gets removed
        filtered_data = {k: v for k, v in extracted_data_create.items() if k in column_names}
        removed_keys = set(extracted_data_create.keys()) - set(filtered_data.keys())
        if removed_keys:
            logger.warning(f"Filtered out non-column keys: {removed_keys}")

        # DEBUG: Print what we're about to pass to ExtractedData
        print("\n" + "="*80)
        print("DEBUG: About to create ExtractedData (Enhanced Path)")
        print("="*80)
        print(f"Valid column names: {column_names}")
        print(f"\nextracted_data_create keys: {set(extracted_data_create.keys())}")
        print(f"filtered_data keys: {set(filtered_data.keys())}")
        print(f"Removed keys: {removed_keys}")
        print("="*80 + "\n")

        extracted_data = ExtractedData(**filtered_data)
        db.add(extracted_data)
        db.flush()  # Get ID for line items

        # Save line items if any
        line_items = extracted_data_dict.get("line_items", [])
        if line_items:
            for i, item_data in enumerate(line_items):
                line_item = LineItem(
                    id=uuid.uuid4(),  # UUID object, not string
                    extracted_data_id=extracted_data.id,
                    description=item_data.get("description"),
                    quantity=item_data.get("quantity"),
                    unit_price=item_data.get("unit_price"),
                    total_price=item_data.get("total_price"),
                    line_number=i + 1,
                    confidence_score=extracted_data_dict.get("field_confidence_scores", {}).get(f"line_item_{i}", 0.8)
                )
                db.add(line_item)
        
        # Update completion status with enhanced metadata
        db.query(InvoiceDocument).filter(
            InvoiceDocument.id == document_id
        ).update({
            "processing_status": ProcessingStatus.COMPLETED,
            "processing_completed_at": datetime.utcnow()
        })
        
        # Update job with enhanced processing metadata
        processing_duration = processing_metadata.get("total_processing_time_ms", 0)
        
        db.query(ProcessingJob).filter(
            ProcessingJob.id == job_id
        ).update({
            "status": ProcessingStatus.COMPLETED,
            "completed_at": datetime.utcnow()
            # Note: processing_time_ms is stored in processing_metadata, not in ProcessingJob table
        })
        
        db.commit()
        logger.info(f"Enhanced document processing completed successfully: {document_id}")
        #logger.info(f"Extraction method: {extracted_data_dict.get('extraction_method')}")
        logger.info(f"Preprocessing applied: {extracted_data_dict.get('preprocessing_applied')}")
        
    except Exception as e:
        # Handle processing failure
        logger.error(f"Enhanced document processing failed for {document_id}: {str(e)}")
        
        error_response = {"message": str(e)}
        if hasattr(e, 'error_type'):
            error_response = error_handler.create_error_response(e)
        
        db.query(InvoiceDocument).filter(
            InvoiceDocument.id == document_id
        ).update({
            "processing_status": ProcessingStatus.FAILED,
            "error_message": error_response["message"],
            "processing_completed_at": datetime.utcnow()
        })
        
        db.query(ProcessingJob).filter(
            ProcessingJob.id == job_id
        ).update({
            "status": ProcessingStatus.FAILED,
            "error_message": error_response["message"],
            "completed_at": datetime.utcnow()
        })
        
        db.commit()
        
    finally:
        db.close()