"""API routes for document management."""

import uuid
import logging
from datetime import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
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

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
file_upload_service = FileUploadService()
ocr_processor = OCRProcessor()
data_extractor = DataExtractor()


@router.post("/upload", response_model=InvoiceDocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    processing_mode: ProcessingMode = ProcessingMode.SEQUENTIAL,
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
        
        # Queue background processing
        background_tasks.add_task(
            process_document_async,
            invoice_doc.id,
            processing_job.id,
            storage_path
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
    db: Session = Depends(get_db)
):
    """
    Get document details by ID.
    
    Args:
        document_id: UUID of the document
        db: Database session
        
    Returns:
        InvoiceDocumentResponse with document details
    """
    document = db.query(InvoiceDocument).filter(
        InvoiceDocument.id == document_id
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
    document = db.query(InvoiceDocument).filter(
        InvoiceDocument.id == document_id
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
    Background task to process document with OCR and data extraction.
    
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
        
        # Perform OCR
        ocr_result = ocr_processor.process_document(file_path)
        
        if ocr_result.error:
            # OCR failed
            db.query(InvoiceDocument).filter(
                InvoiceDocument.id == document_id
            ).update({
                "processing_status": ProcessingStatus.FAILED,
                "error_message": f"OCR failed: {ocr_result.error}",
                "processing_completed_at": datetime.utcnow()
            })
            
            db.query(ProcessingJob).filter(
                ProcessingJob.id == job_id
            ).update({
                "status": ProcessingStatus.FAILED,
                "error_message": f"OCR failed: {ocr_result.error}",
                "completed_at": datetime.utcnow()
            })
            db.commit()
            return
        
        # Extract structured data
        extracted_data_schema = data_extractor.extract_structured_data(
            ocr_result.text,
            document_id,
            ocr_result.confidence
        )
        
        # Save extracted data
        from models import ExtractedData, LineItem
        
        extracted_data = ExtractedData(**extracted_data_schema.dict())
        db.add(extracted_data)
        db.flush()  # Get ID for line items
        
        # Save line items if any
        if hasattr(extracted_data_schema, 'line_items') and extracted_data_schema.line_items:
            for item_data in extracted_data_schema.line_items:
                line_item = LineItem(
                    id=str(uuid.uuid4()),
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