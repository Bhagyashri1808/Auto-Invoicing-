"""API routes for processing management."""

import uuid
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from api.dependencies import get_db
from models.schemas import (
    ProcessingJobResponse, ExtractedDataResponse,
    ReviewSessionCreate, ReviewSessionResponse
)
from models import ProcessingJob, ExtractedData, ReviewSession, InvoiceDocument
from models.enums import ProcessingStatus, ProcessingMode

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/jobs", response_model=List[ProcessingJobResponse])
async def list_processing_jobs(
    skip: int = 0,
    limit: int = 100,
    status: ProcessingStatus = None,
    db: Session = Depends(get_db)
):
    """
    List processing jobs with optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by processing status
        db: Database session
        
    Returns:
        List of ProcessingJobResponse objects
    """
    query = db.query(ProcessingJob)
    
    if status:
        query = query.filter(ProcessingJob.status == status)
    
    jobs = query.offset(skip).limit(limit).all()
    
    return [ProcessingJobResponse.from_orm(job) for job in jobs]


@router.get("/jobs/{job_id}", response_model=ProcessingJobResponse)
async def get_processing_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get processing job details by ID.
    
    Args:
        job_id: UUID of the processing job
        db: Database session
        
    Returns:
        ProcessingJobResponse with job details
    """
    job = db.query(ProcessingJob).filter(
        ProcessingJob.id == job_id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail="Processing job not found"
        )
    
    return ProcessingJobResponse.from_orm(job)


@router.post("/jobs/{job_id}/retry")
async def retry_processing_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Retry a failed processing job.
    
    Args:
        job_id: UUID of the processing job
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        Success message
    """
    job = db.query(ProcessingJob).filter(
        ProcessingJob.id == job_id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail="Processing job not found"
        )
    
    if job.status != ProcessingStatus.FAILED:
        raise HTTPException(
            status_code=400,
            detail="Only failed jobs can be retried"
        )
    
    # Get associated document
    document = db.query(InvoiceDocument).filter(
        InvoiceDocument.id == job.invoice_document_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=404,
            detail="Associated document not found"
        )
    
    try:
        # Reset job status
        job.status = ProcessingStatus.PENDING
        job.error_message = None
        job.started_at = None
        job.completed_at = None
        
        # Reset document status
        document.processing_status = ProcessingStatus.PENDING
        document.error_message = None
        document.processing_started_at = None
        document.processing_completed_at = None
        
        db.commit()
        
        # Queue background processing
        from api.routes.documents import process_document_async
        background_tasks.add_task(
            process_document_async,
            document.id,
            job.id,
            document.file_path
        )
        
        logger.info(f"Processing job retry queued: {job_id}")
        
        return {"message": "Processing job retry queued successfully"}
        
    except Exception as e:
        logger.error(f"Retry failed for job {job_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Retry failed: {str(e)}"
        )


@router.get("/extracted-data", response_model=List[ExtractedDataResponse])
async def list_extracted_data(
    skip: int = 0,
    limit: int = 100,
    min_confidence: float = None,
    db: Session = Depends(get_db)
):
    """
    List extracted data with optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        min_confidence: Filter by minimum confidence score
        db: Database session
        
    Returns:
        List of ExtractedDataResponse objects
    """
    query = db.query(ExtractedData)
    
    if min_confidence is not None:
        query = query.filter(ExtractedData.extraction_confidence >= min_confidence)
    
    extracted_data = query.offset(skip).limit(limit).all()
    
    return [ExtractedDataResponse.from_orm(data) for data in extracted_data]


@router.get("/extracted-data/{data_id}", response_model=ExtractedDataResponse)
async def get_extracted_data(
    data_id: str,
    db: Session = Depends(get_db)
):
    """
    Get extracted data details by ID.
    
    Args:
        data_id: UUID of the extracted data
        db: Database session
        
    Returns:
        ExtractedDataResponse with data details
    """
    data = db.query(ExtractedData).filter(
        ExtractedData.id == data_id
    ).first()
    
    if not data:
        raise HTTPException(
            status_code=404,
            detail="Extracted data not found"
        )
    
    return ExtractedDataResponse.from_orm(data)


@router.get("/documents/{document_id}/extracted-data", response_model=ExtractedDataResponse)
async def get_document_extracted_data(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Get extracted data for a specific document.
    
    Args:
        document_id: UUID of the document
        db: Database session
        
    Returns:
        ExtractedDataResponse with data details
    """
    try:
        # Convert string to UUID
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid document ID format"
        )
    
    # Verify document exists
    document = db.query(InvoiceDocument).filter(
        InvoiceDocument.id == doc_uuid
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )
    
    # Get extracted data
    extracted_data = db.query(ExtractedData).filter(
        ExtractedData.invoice_document_id == doc_uuid
    ).first()
    
    if not extracted_data:
        raise HTTPException(
            status_code=404,
            detail="No extracted data found for this document"
        )
    
    return ExtractedDataResponse.from_orm(extracted_data)


@router.post("/documents/{document_id}/review", response_model=ReviewSessionResponse)
async def start_review_session(
    document_id: str,
    session_data: ReviewSessionCreate,
    db: Session = Depends(get_db)
):
    """
    Start a review session for a document.
    
    Args:
        document_id: UUID of the document
        session_data: Review session creation data
        db: Database session
        
    Returns:
        ReviewSessionResponse with session details
    """
    try:
        # Convert string to UUID
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid document ID format"
        )
    
    # Verify document exists and has extracted data
    document = db.query(InvoiceDocument).filter(
        InvoiceDocument.id == doc_uuid
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )
    
    if document.processing_status != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Document must be processed before review"
        )
    
    extracted_data = db.query(ExtractedData).filter(
        ExtractedData.invoice_document_id == doc_uuid
    ).first()
    
    if not extracted_data:
        raise HTTPException(
            status_code=404,
            detail="No extracted data found for review"
        )
    
    try:
        # Create review session
        review_session = ReviewSession(
            **session_data.dict(),
            invoice_document_id=doc_uuid,
            extracted_data_id=extracted_data.id
        )
        
        db.add(review_session)
        db.commit()
        db.refresh(review_session)
        
        logger.info(f"Review session started: {review_session.id}")
        
        return ReviewSessionResponse.from_orm(review_session)
        
    except Exception as e:
        logger.error(f"Failed to start review session for {document_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start review session: {str(e)}"
        )


@router.get("/review-sessions", response_model=List[ReviewSessionResponse])
async def list_review_sessions(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db)
):
    """
    List review sessions with optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by review status
        db: Database session
        
    Returns:
        List of ReviewSessionResponse objects
    """
    query = db.query(ReviewSession)
    
    if status:
        query = query.filter(ReviewSession.status == status)
    
    sessions = query.offset(skip).limit(limit).all()
    
    return [ReviewSessionResponse.from_orm(session) for session in sessions]


@router.get("/review-sessions/{session_id}", response_model=ReviewSessionResponse)
async def get_review_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get review session details by ID.
    
    Args:
        session_id: UUID of the review session
        db: Database session
        
    Returns:
        ReviewSessionResponse with session details
    """
    session = db.query(ReviewSession).filter(
        ReviewSession.id == session_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Review session not found"
        )
    
    return ReviewSessionResponse.from_orm(session)