/**
 * Component tests for ProcessingStatus component with enhanced LLM processing display
 */

import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ProcessingStatus from '../../src/components/ProcessingStatus';
import type { ProcessingStatus as ProcessingStatusType, LLMProcessingJob } from '../../src/types/preprocessing';

// Mock the API service
vi.mock('../../src/services/api', () => ({
  getProcessingStatus: vi.fn(),
  getLLMProcessingJob: vi.fn(),
}));

describe('ProcessingStatus Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should display preprocessing progress when enabled', () => {
    // This test should FAIL initially - component doesn't exist yet
    
    const mockStatus: ProcessingStatusType = {
      id: 'test-doc-123',
      status: 'PROCESSING',
      preprocessing_applied: true,
      preprocessing_method: 'threshold+deskew',
      extraction_method: 'LLM_PRIMARY',
      progress_percentage: 45,
      current_step: 'preprocessing',
      estimated_completion_time: '2025-01-23T12:05:00Z'
    };

    render(<ProcessingStatus documentId="test-doc-123" initialStatus={mockStatus} />);

    // Should show preprocessing step
    expect(screen.getByText(/preprocessing/i)).toBeInTheDocument();
    expect(screen.getByText(/45%/)).toBeInTheDocument();
    expect(screen.getByText(/threshold\+deskew/i)).toBeInTheDocument();
  });

  it('should display LLM processing status and progress', () => {
    // This test should FAIL initially
    
    const mockStatus: ProcessingStatusType = {
      id: 'test-doc-123',
      status: 'PROCESSING',
      preprocessing_applied: true,
      extraction_method: 'LLM_PRIMARY',
      progress_percentage: 75,
      current_step: 'llm_processing',
      estimated_completion_time: '2025-01-23T12:03:00Z'
    };

    const mockLLMJob: LLMProcessingJob = {
      id: 'llm-job-123',
      invoice_document_id: 'test-doc-123',
      preprocessing_config_id: 'config-123',
      llm_model_name: 'llama3.2:3b',
      preprocessed_image_path: '/path/to/processed.png',
      processing_started_at: '2025-01-23T12:00:00Z',
      llm_started_at: '2025-01-23T12:01:00Z',
      llm_completed_at: null,
      processing_completed_at: null,
      timeout_occurred: false,
      fallback_triggered: false,
      error_message: null,
      retry_count: 0,
      max_retries: 3,
      memory_peak_mb: 512,
      processing_duration_ms: null
    };

    render(
      <ProcessingStatus 
        documentId="test-doc-123" 
        initialStatus={mockStatus}
        llmJob={mockLLMJob}
      />
    );

    // Should show LLM processing details
    expect(screen.getByText(/llm processing/i)).toBeInTheDocument();
    expect(screen.getByText(/llama3\.2:3b/i)).toBeInTheDocument();
    expect(screen.getByText(/75%/)).toBeInTheDocument();
    expect(screen.getByText(/memory.*512.*mb/i)).toBeInTheDocument();
  });

  it('should display confidence scores when processing is complete', () => {
    // This test should FAIL initially
    
    const mockStatus: ProcessingStatusType = {
      id: 'test-doc-123',
      status: 'COMPLETED',
      preprocessing_applied: true,
      extraction_method: 'LLM_PRIMARY',
      progress_percentage: 100,
      current_step: 'completed',
      ocr_confidence_avg: 0.85,
      llm_confidence_score: 0.92,
      field_confidence_scores: {
        vendor_name: 0.95,
        total_amount: 0.88,
        invoice_date: 0.91
      }
    };

    render(<ProcessingStatus documentId="test-doc-123" initialStatus={mockStatus} />);

    // Should show confidence scores
    expect(screen.getByText(/confidence/i)).toBeInTheDocument();
    expect(screen.getByText(/92%/)).toBeInTheDocument(); // LLM confidence
    expect(screen.getByText(/85%/)).toBeInTheDocument(); // OCR confidence
    
    // Should show field-level confidence
    expect(screen.getByText(/vendor.*95%/i)).toBeInTheDocument();
    expect(screen.getByText(/amount.*88%/i)).toBeInTheDocument();
    expect(screen.getByText(/date.*91%/i)).toBeInTheDocument();
  });

  it('should show fallback indicator when LLM processing fails', () => {
    // This test should FAIL initially
    
    const mockStatus: ProcessingStatusType = {
      id: 'test-doc-123',
      status: 'COMPLETED',
      preprocessing_applied: true,
      extraction_method: 'LLM_FALLBACK',
      progress_percentage: 100,
      current_step: 'completed'
    };

    const mockLLMJob: LLMProcessingJob = {
      id: 'llm-job-123',
      invoice_document_id: 'test-doc-123',
      preprocessing_config_id: null,
      llm_model_name: 'llama3.2:3b',
      preprocessed_image_path: null,
      processing_started_at: '2025-01-23T12:00:00Z',
      llm_started_at: '2025-01-23T12:01:00Z',
      llm_completed_at: '2025-01-23T12:01:30Z',
      processing_completed_at: '2025-01-23T12:02:00Z',
      timeout_occurred: true,
      fallback_triggered: true,
      error_message: 'LLM request timeout after 60 seconds',
      retry_count: 3,
      max_retries: 3,
      memory_peak_mb: null,
      processing_duration_ms: 60000
    };

    render(
      <ProcessingStatus 
        documentId="test-doc-123" 
        initialStatus={mockStatus}
        llmJob={mockLLMJob}
      />
    );

    // Should show fallback indicator
    expect(screen.getByText(/fallback/i)).toBeInTheDocument();
    expect(screen.getByText(/timeout/i)).toBeInTheDocument();
    expect(screen.getByText(/ocr.*used/i)).toBeInTheDocument();
  });

  it('should display error states appropriately', () => {
    // This test should FAIL initially
    
    const mockStatus: ProcessingStatusType = {
      id: 'test-doc-123',
      status: 'FAILED',
      preprocessing_applied: false,
      extraction_method: 'OCR_ONLY',
      progress_percentage: 0,
      current_step: 'error',
      error_message: 'Memory limit exceeded during preprocessing'
    };

    render(<ProcessingStatus documentId="test-doc-123" initialStatus={mockStatus} />);

    // Should show error state
    expect(screen.getByText(/error/i)).toBeInTheDocument();
    expect(screen.getByText(/memory limit exceeded/i)).toBeInTheDocument();
    expect(screen.getByText(/preprocessing.*failed/i)).toBeInTheDocument();
  });

  it('should update status in real-time', async () => {
    // This test should FAIL initially
    
    const { getProcessingStatus } = await import('../../src/services/api');
    
    const initialStatus: ProcessingStatusType = {
      id: 'test-doc-123',
      status: 'PROCESSING',
      preprocessing_applied: true,
      extraction_method: 'LLM_PRIMARY',
      progress_percentage: 25,
      current_step: 'preprocessing'
    };

    const updatedStatus: ProcessingStatusType = {
      ...initialStatus,
      progress_percentage: 75,
      current_step: 'llm_processing'
    };

    // Mock API to return updated status
    vi.mocked(getProcessingStatus).mockResolvedValueOnce(updatedStatus);

    render(<ProcessingStatus documentId="test-doc-123" initialStatus={initialStatus} />);

    // Initially shows 25%
    expect(screen.getByText(/25%/)).toBeInTheDocument();

    // Wait for status update
    await waitFor(() => {
      expect(screen.getByText(/75%/)).toBeInTheDocument();
      expect(screen.getByText(/llm processing/i)).toBeInTheDocument();
    });

    expect(getProcessingStatus).toHaveBeenCalledWith('test-doc-123');
  });

  it('should show processing time estimates', () => {
    // This test should FAIL initially
    
    const mockStatus: ProcessingStatusType = {
      id: 'test-doc-123',
      status: 'PROCESSING',
      preprocessing_applied: true,
      extraction_method: 'LLM_PRIMARY',
      progress_percentage: 60,
      current_step: 'llm_processing',
      estimated_completion_time: '2025-01-23T12:05:00Z',
      elapsed_time_ms: 45000
    };

    render(<ProcessingStatus documentId="test-doc-123" initialStatus={mockStatus} />);

    // Should show time estimates
    expect(screen.getByText(/estimated.*time/i)).toBeInTheDocument();
    expect(screen.getByText(/elapsed.*45s/i)).toBeInTheDocument();
  });

  it('should handle method comparison display', () => {
    // This test should FAIL initially
    
    const mockStatus: ProcessingStatusType = {
      id: 'test-doc-123',
      status: 'COMPLETED',
      preprocessing_applied: true,
      extraction_method: 'LLM_PRIMARY',
      progress_percentage: 100,
      current_step: 'completed',
      ocr_confidence_avg: 0.72,
      llm_confidence_score: 0.89,
      method_comparison: {
        llm_better: true,
        confidence_improvement: 0.17,
        fields_improved: ['vendor_name', 'total_amount']
      }
    };

    render(<ProcessingStatus documentId="test-doc-123" initialStatus={mockStatus} />);

    // Should show method comparison
    expect(screen.getByText(/improvement/i)).toBeInTheDocument();
    expect(screen.getByText(/17%.*better/i)).toBeInTheDocument();
    expect(screen.getByText(/vendor.*amount.*improved/i)).toBeInTheDocument();
  });
});

// Additional test types that extend the base interface for testing
interface ProcessingStatus extends ProcessingStatusType {
  error_message?: string;
  elapsed_time_ms?: number;
  method_comparison?: {
    llm_better: boolean;
    confidence_improvement: number;
    fields_improved: string[];
  };
}