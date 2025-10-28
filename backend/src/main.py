"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import documents, processing
from database.config import engine, Base

# Import all models so SQLAlchemy knows about them before creating tables
# Order matters - import LLMProcessingJobDB and PreprocessingConfigurationDB before using relationships
from models.preprocessing import PreprocessingConfigurationDB
from models.llm_processing import LLMProcessingJobDB
from models.performance import ProcessingPerformanceMetricDB
from models.invoice_document import InvoiceDocument
from models.extracted_data import ExtractedData
from models.line_item import LineItem
from models.processing_job import ProcessingJob
from models.review_session import ReviewSession
from models.field_correction import FieldCorrection
from models.configuration import Configuration

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Invoice Automation API",
    description="Invoice processing API with OCR and HITL review",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server (default)
        "http://localhost:5173",  # Vite dev server (default)
        "http://localhost:5174",  # Vite dev server (alternate)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(processing.router, prefix="/api/v1/processing", tags=["processing"])

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Invoice Automation API", "status": "healthy"}

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}