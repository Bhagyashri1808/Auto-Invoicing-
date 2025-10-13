/**
 * TypeScript interfaces generated from backend Pydantic schemas
 * These interfaces ensure type safety between frontend and backend
 */

// Enums
export enum ProcessingStatus {
  PENDING = "PENDING",
  PROCESSING = "PROCESSING", 
  COMPLETED = "COMPLETED",
  FAILED = "FAILED",
  REVIEWING = "REVIEWING",
  APPROVED = "APPROVED",
  REJECTED = "REJECTED"
}

export enum FileType {
  PDF = "PDF",
  JPG = "JPG", 
  PNG = "PNG",
  TIFF = "TIFF"
}

export enum ProcessingMode {
  SEQUENTIAL = "SEQUENTIAL",
  PARALLEL = "PARALLEL"
}

export enum ReviewDecision {
  APPROVED = "APPROVED",
  REJECTED = "REJECTED", 
  REQUIRES_REPROCESSING = "REQUIRES_REPROCESSING"
}

export enum ConfigDataType {
  STRING = "STRING",
  INTEGER = "INTEGER",
  FLOAT = "FLOAT",
  BOOLEAN = "BOOLEAN"
}

// Base interfaces
export interface BaseTimestamped {
  id: string;
  created_at: string;
  updated_at: string;
}

// Invoice Document interfaces
export interface InvoiceDocument extends BaseTimestamped {
  filename: string;
  file_type: FileType;
  file_size: number;
  upload_date: string;
  processing_status: ProcessingStatus;
}

export interface InvoiceDocumentDetail extends InvoiceDocument {
  extracted_data?: ExtractedData;
  review_session?: ReviewSession;
  processing_job?: ProcessingJob;
}

// Extracted Data interfaces
export interface ExtractedData extends BaseTimestamped {
  invoice_document_id: string;
  vendor_name?: string;
  vendor_address?: string;
  invoice_number?: string;
  invoice_date?: string; // ISO date string
  due_date?: string; // ISO date string
  total_amount?: number;
  tax_amount?: number;
  subtotal_amount?: number;
  currency: string;
  extraction_confidence: number;
  extracted_at: string;
  is_human_verified: boolean;
}

export interface ExtractedDataDetail extends ExtractedData {
  line_items: LineItem[];
}

export interface ExtractedDataUpdate {
  vendor_name?: string;
  vendor_address?: string;
  invoice_number?: string;
  invoice_date?: string;
  due_date?: string;
  total_amount?: number;
  tax_amount?: number;
  subtotal_amount?: number;
  currency?: string;
  line_items?: LineItemUpdate[];
}

// Line Item interfaces
export interface LineItem extends BaseTimestamped {
  extracted_data_id: string;
  description?: string;
  quantity?: number;
  unit_price?: number;
  total_price?: number;
  line_number: number;
  confidence_score: number;
}

export interface LineItemUpdate {
  id?: string;
  description?: string;
  quantity?: number;
  unit_price?: number;
  total_price?: number;
}

// Processing Job interfaces
export interface ProcessingJob extends BaseTimestamped {
  invoice_document_id: string;
  queue_position: number;
  processing_mode: ProcessingMode;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  retry_count: number;
  max_retries: number;
}

// Review Session interfaces
export interface ReviewSession extends BaseTimestamped {
  invoice_document_id: string;
  review_started_at: string;
  review_completed_at?: string;
  time_spent_seconds?: number;
  corrections_made: number;
  final_decision?: ReviewDecision;
  reviewer_notes?: string;
}

export interface ReviewCompletion {
  final_decision: ReviewDecision;
  reviewer_notes?: string;
}

// Field Correction interfaces
export interface FieldCorrection extends BaseTimestamped {
  review_session_id: string;
  field_name: string;
  original_value?: string;
  corrected_value?: string;
  original_confidence: number;
  correction_timestamp: string;
}

// Configuration interfaces
export interface Configuration extends BaseTimestamped {
  key: string;
  value: string;
  data_type: ConfigDataType;
}

export interface ProcessingConfig {
  ocr_confidence_threshold: number;
  processing_mode: ProcessingMode;
  max_file_size_mb: number;
  auto_save_corrections: boolean;
}

export interface ProcessingConfigUpdate {
  ocr_confidence_threshold?: number;
  processing_mode?: ProcessingMode;
  max_file_size_mb?: number;
  auto_save_corrections?: boolean;
}

// Response interfaces
export interface ErrorResponse {
  error: string;
  message: string;
  details?: Record<string, any>;
}

export interface PaginatedResponse {
  total: number;
  page: number;
  limit: number;
}

export interface InvoiceDocumentList extends PaginatedResponse {
  invoices: InvoiceDocument[];
}

export interface ProcessingQueue {
  queue: ProcessingJob[];
  total_pending: number;
  current_processing: number;
}

// Export interfaces
export interface ExportRequest {
  format: "csv" | "json";
  invoice_ids: string[];
  include_line_items: boolean;
}

// File upload interfaces (frontend specific)
export interface FileUploadProgress {
  file: File;
  progress: number;
  status: "uploading" | "processing" | "completed" | "error";
  error?: string;
}

// API response wrapper
export interface ApiResponse<T = any> {
  data?: T;
  error?: ErrorResponse;
}

// Form interfaces for components
export interface DocumentUploadForm {
  files: FileList;
}

export interface ReviewForm extends ExtractedDataUpdate {
  // Additional frontend-specific fields
  reviewer_notes?: string;
}

// UI state interfaces
export interface UIState {
  loading: boolean;
  error?: string;
  success?: string;
}