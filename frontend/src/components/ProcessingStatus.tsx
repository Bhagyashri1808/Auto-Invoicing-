/**
 * Enhanced processing status component with LLM and preprocessing progress display
 */

import React, { useState, useEffect } from 'react';
import type { 
  ProcessingStatus as ProcessingStatusType, 
  LLMProcessingJob, 
  ExtractionMethod 
} from '../types/preprocessing';

interface ProcessingStatusProps {
  documentId: string;
  initialStatus?: Partial<ProcessingStatusType>;
  llmJob?: LLMProcessingJob;
  refreshInterval?: number;
}

interface ProcessingProgress {
  step: string;
  percentage: number;
  description: string;
}

const ProcessingStatus: React.FC<ProcessingStatusProps> = ({
  documentId,
  initialStatus = {},
  llmJob,
  refreshInterval = 2000
}) => {
  const [status, setStatus] = useState<Partial<ProcessingStatusType>>(initialStatus);
  const [currentJob, setCurrentJob] = useState<LLMProcessingJob | undefined>(llmJob);
  const [isPolling, setIsPolling] = useState(false);

  // Mock progress calculation based on status
  const calculateProgress = (): ProcessingProgress => {
    const extractionMethod = status.extraction_method || 'OCR_ONLY';
    const currentStep = status.current_step || 'queued';
    
    switch (currentStep) {
      case 'preprocessing':
        return {
          step: 'Image Preprocessing',
          percentage: 25,
          description: `Applying ${status.preprocessing_method || 'threshold'} preprocessing...`
        };
      case 'llm_processing':
        return {
          step: 'LLM Extraction',
          percentage: 65,
          description: `Processing with ${currentJob?.llm_model_name || 'Llama 3.2'}...`
        };
      case 'ocr_fallback':
        return {
          step: 'OCR Fallback',
          percentage: 80,
          description: 'LLM failed, using OCR extraction...'
        };
      case 'completed':
        return {
          step: 'Completed',
          percentage: 100,
          description: `Extraction completed using ${extractionMethod}`
        };
      case 'error':
        return {
          step: 'Error',
          percentage: 0,
          description: status.error_message || 'Processing failed'
        };
      default:
        return {
          step: 'Queued',
          percentage: 0,
          description: 'Waiting to start processing...'
        };
    }
  };

  const progress = calculateProgress();

  // Get status color based on current state
  const getStatusColor = (): string => {
    if (status.status === 'COMPLETED') return 'text-green-600';
    if (status.status === 'FAILED') return 'text-red-600';
    if (status.status === 'PROCESSING') return 'text-blue-600';
    return 'text-gray-600';
  };

  // Get extraction method badge color
  const getMethodBadgeColor = (method: ExtractionMethod): string => {
    switch (method) {
      case 'LLM_PRIMARY': return 'bg-green-100 text-green-800';
      case 'LLM_FALLBACK': return 'bg-yellow-100 text-yellow-800';
      case 'OCR_ONLY': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Format confidence score as percentage
  const formatConfidence = (score: number | null | undefined): string => {
    if (score === null || score === undefined) return 'N/A';
    return `${Math.round(score * 100)}%`;
  };

  // Render confidence scores section
  const renderConfidenceScores = () => {
    if (status.status !== 'COMPLETED') return null;

    const hasConfidenceData = status.ocr_confidence_avg !== null || 
                             status.llm_confidence_score !== null;

    if (!hasConfidenceData) return null;

    return (
      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Confidence Scores</h4>
        
        <div className="grid grid-cols-2 gap-4">
          {status.llm_confidence_score !== null && (
            <div>
              <span className="text-xs text-gray-500">LLM Confidence</span>
              <div className="text-lg font-semibold text-blue-600">
                {formatConfidence(status.llm_confidence_score)}
              </div>
            </div>
          )}
          
          {status.ocr_confidence_avg !== null && (
            <div>
              <span className="text-xs text-gray-500">OCR Confidence</span>
              <div className="text-lg font-semibold text-gray-600">
                {formatConfidence(status.ocr_confidence_avg)}
              </div>
            </div>
          )}
        </div>

        {/* Field-level confidence */}
        {status.field_confidence_scores && Object.keys(status.field_confidence_scores).length > 0 && (
          <div className="mt-3">
            <span className="text-xs text-gray-500">Field Confidence</span>
            <div className="grid grid-cols-3 gap-2 mt-1">
              {Object.entries(status.field_confidence_scores).map(([field, score]) => (
                <div key={field} className="text-xs">
                  <span className="text-gray-600 capitalize">
                    {field.replace('_', ' ')}:
                  </span>
                  <span className="ml-1 font-medium">
                    {formatConfidence(score)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  // Render processing details
  const renderProcessingDetails = () => {
    if (!currentJob) return null;

    return (
      <div className="mt-4 p-3 bg-blue-50 rounded-lg">
        <h4 className="text-sm font-medium text-blue-700 mb-2">Processing Details</h4>
        
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Model:</span>
            <span className="font-medium">{currentJob.llm_model_name}</span>
          </div>
          
          {currentJob.memory_peak_mb && (
            <div className="flex justify-between">
              <span className="text-gray-600">Memory Usage:</span>
              <span className="font-medium">{currentJob.memory_peak_mb} MB</span>
            </div>
          )}
          
          {currentJob.processing_duration_ms && (
            <div className="flex justify-between">
              <span className="text-gray-600">Duration:</span>
              <span className="font-medium">{currentJob.processing_duration_ms}ms</span>
            </div>
          )}
          
          {currentJob.retry_count > 0 && (
            <div className="flex justify-between">
              <span className="text-gray-600">Retries:</span>
              <span className="font-medium">{currentJob.retry_count}/{currentJob.max_retries}</span>
            </div>
          )}
        </div>

        {/* Error information */}
        {(currentJob.timeout_occurred || currentJob.fallback_triggered) && (
          <div className="mt-3 p-2 bg-yellow-100 rounded">
            <div className="text-sm text-yellow-800">
              {currentJob.timeout_occurred && (
                <div>⚠️ LLM processing timeout occurred</div>
              )}
              {currentJob.fallback_triggered && (
                <div>🔄 Fallback to OCR was used</div>
              )}
              {currentJob.error_message && (
                <div className="mt-1 text-xs">{currentJob.error_message}</div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="bg-white p-4 rounded-lg border">
      {/* Header with status and method */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Processing Status</h3>
        
        {status.extraction_method && (
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getMethodBadgeColor(status.extraction_method)}`}>
            {status.extraction_method.replace('_', ' ')}
          </span>
        )}
      </div>

      {/* Progress bar */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <span className={`text-sm font-medium ${getStatusColor()}`}>
            {progress.step}
          </span>
          <span className="text-sm text-gray-500">
            {progress.percentage}%
          </span>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-500 ${
              status.status === 'FAILED' ? 'bg-red-500' :
              status.status === 'COMPLETED' ? 'bg-green-500' : 'bg-blue-500'
            }`}
            style={{ width: `${progress.percentage}%` }}
          />
        </div>
        
        <p className="text-sm text-gray-600 mt-2">
          {progress.description}
        </p>
      </div>

      {/* Preprocessing information */}
      {status.preprocessing_applied && (
        <div className="mb-4 p-3 bg-green-50 rounded-lg">
          <div className="flex items-center">
            <span className="text-green-600 mr-2">✓</span>
            <span className="text-sm font-medium text-green-700">
              Preprocessing Applied
            </span>
          </div>
          {status.preprocessing_method && (
            <p className="text-sm text-green-600 mt-1">
              Method: {status.preprocessing_method}
            </p>
          )}
        </div>
      )}

      {/* Processing details */}
      {renderProcessingDetails()}

      {/* Confidence scores */}
      {renderConfidenceScores()}

      {/* Time information */}
      {status.elapsed_time_ms && (
        <div className="mt-4 text-sm text-gray-500">
          Elapsed: {Math.round(status.elapsed_time_ms / 1000)}s
          {status.estimated_completion_time && (
            <span className="ml-4">
              ETA: {new Date(status.estimated_completion_time).toLocaleTimeString()}
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default ProcessingStatus;