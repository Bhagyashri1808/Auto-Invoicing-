/**
 * TypeScript types for enhanced image preprocessing functionality
 */

export interface PreprocessingConfiguration {
  id: string;
  user_id: string;
  operation_type: PreprocessingOperation;
  target_width: number;
  threshold_block_size: number;
  threshold_constant: number;
  bilateral_filter_d: number;
  bilateral_sigma_color: number;
  bilateral_sigma_space: number;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export type PreprocessingOperation = 'THRESHOLD' | 'DESKEW' | 'COMBINED';

export type ExtractionMethod = 'OCR_ONLY' | 'LLM_PRIMARY' | 'LLM_FALLBACK';

export interface LLMProcessingJob {
  id: string;
  invoice_document_id: string;
  preprocessing_config_id: string | null;
  llm_model_name: string;
  preprocessed_image_path: string | null;
  processing_started_at: string;
  llm_started_at: string | null;
  llm_completed_at: string | null;
  processing_completed_at: string | null;
  timeout_occurred: boolean;
  fallback_triggered: boolean;
  error_message: string | null;
  retry_count: number;
  max_retries: number;
  memory_peak_mb: number | null;
  processing_duration_ms: number | null;
}

export interface EnhancedExtractedData {
  // Existing OCR fields
  vendor_name: string | null;
  vendor_address: string | null;
  invoice_number: string | null;
  invoice_date: string | null;
  due_date: string | null;
  total_amount: number | null;
  tax_amount: number | null;
  subtotal_amount: number | null;
  currency: string;
  
  // Enhanced LLM fields
  extraction_method: ExtractionMethod;
  llm_processing_job_id: string | null;
  ocr_confidence_avg: number | null;
  llm_confidence_score: number | null;
  field_confidence_scores: Record<string, number>;
  preprocessing_applied: boolean;
  preprocessing_method: string | null;
  validation_errors: Record<string, any> | null;
  has_manual_corrections: boolean;
}

export interface ProcessingPerformanceMetric {
  id: string;
  invoice_document_id: string;
  processing_date: string;
  extraction_method: ExtractionMethod;
  preprocessing_duration_ms: number | null;
  ocr_duration_ms: number | null;
  llm_duration_ms: number | null;
  total_duration_ms: number;
  memory_peak_mb: number;
  file_size_mb: number;
  image_dimensions: string;
  preprocessing_applied: boolean;
  timeout_occurred: boolean;
  error_occurred: boolean;
  accuracy_score: number | null;
  user_corrections_count: number;
}

export interface LLMHealthStatus {
  status: 'healthy' | 'degraded' | 'unavailable';
  model_loaded: string | null;
  response_time_ms: number | null;
  memory_usage_mb: number | null;
  last_check: string;
  error_message: string | null;
}

export interface PreprocessingConfigurationCreate {
  operation_type: PreprocessingOperation;
  target_width?: number;
  threshold_block_size?: number;
  threshold_constant?: number;
  bilateral_filter_d?: number;
  bilateral_sigma_color?: number;
  bilateral_sigma_space?: number;
  is_default?: boolean;
}

export interface PreprocessingConfigurationUpdate {
  operation_type?: PreprocessingOperation;
  target_width?: number;
  threshold_block_size?: number;
  threshold_constant?: number;
  bilateral_filter_d?: number;
  bilateral_sigma_color?: number;
  bilateral_sigma_space?: number;
  is_default?: boolean;
}

export interface ReprocessingRequest {
  preprocessing_config_id?: string;
  enable_preprocessing?: boolean;
  enable_llm_processing?: boolean;
  force_reprocess?: boolean;
}

export interface ProcessingJobResponse {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  estimated_completion_time: string | null;
}