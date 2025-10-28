/**
 * Quality indicator component for confidence score visualization and method comparison
 */

import React from 'react';
import type { ExtractionMethod } from '../types/preprocessing';

interface QualityIndicatorProps {
  ocrConfidence?: number | null;
  llmConfidence?: number | null;
  extractionMethod: ExtractionMethod;
  fieldConfidenceScores?: Record<string, number>;
  showComparison?: boolean;
  className?: string;
}

interface ConfidenceBarProps {
  label: string;
  confidence: number;
  color: string;
  isActive?: boolean;
}

const ConfidenceBar: React.FC<ConfidenceBarProps> = ({ 
  label, 
  confidence, 
  color, 
  isActive = false 
}) => {
  const percentage = Math.round(confidence * 100);
  
  return (
    <div className={`${isActive ? 'ring-2 ring-blue-300 bg-blue-50' : 'bg-gray-50'} p-3 rounded-lg`}>
      <div className="flex justify-between items-center mb-2">
        <span className={`text-sm font-medium ${isActive ? 'text-blue-700' : 'text-gray-700'}`}>
          {label}
          {isActive && <span className="ml-1 text-xs">(Used)</span>}
        </span>
        <span className={`text-lg font-bold ${isActive ? 'text-blue-600' : 'text-gray-600'}`}>
          {percentage}%
        </span>
      </div>
      
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-300 ${color}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      
      {/* Quality assessment */}
      <div className="mt-2">
        <span className={`text-xs px-2 py-1 rounded ${getQualityBadgeStyle(confidence)}`}>
          {getQualityLabel(confidence)}
        </span>
      </div>
    </div>
  );
};

const getQualityLabel = (confidence: number): string => {
  if (confidence >= 0.9) return 'Excellent';
  if (confidence >= 0.8) return 'Very Good';
  if (confidence >= 0.7) return 'Good';
  if (confidence >= 0.6) return 'Fair';
  if (confidence >= 0.5) return 'Poor';
  return 'Very Poor';
};

const getQualityBadgeStyle = (confidence: number): string => {
  if (confidence >= 0.8) return 'bg-green-100 text-green-800';
  if (confidence >= 0.6) return 'bg-yellow-100 text-yellow-800';
  return 'bg-red-100 text-red-800';
};

const QualityIndicator: React.FC<QualityIndicatorProps> = ({
  ocrConfidence,
  llmConfidence,
  extractionMethod,
  fieldConfidenceScores = {},
  showComparison = true,
  className = ''
}) => {
  // Determine which method was used
  const isLLMUsed = extractionMethod === 'LLM_PRIMARY';
  const isLLMFallback = extractionMethod === 'LLM_FALLBACK';
  const isOCROnly = extractionMethod === 'OCR_ONLY';

  // Calculate overall confidence based on method used
  const getOverallConfidence = (): number => {
    if (isLLMUsed && llmConfidence !== null && llmConfidence !== undefined) {
      return llmConfidence;
    }
    if (ocrConfidence !== null && ocrConfidence !== undefined) {
      return ocrConfidence;
    }
    return 0;
  };

  const overallConfidence = getOverallConfidence();

  // Calculate improvement if both methods have scores
  const calculateImprovement = (): { hasImprovement: boolean; improvement: number } => {
    if (llmConfidence !== null && llmConfidence !== undefined && 
        ocrConfidence !== null && ocrConfidence !== undefined) {
      const improvement = llmConfidence - ocrConfidence;
      return {
        hasImprovement: improvement > 0.05, // 5% threshold
        improvement: improvement
      };
    }
    return { hasImprovement: false, improvement: 0 };
  };

  const { hasImprovement, improvement } = calculateImprovement();

  // Get the best fields based on confidence scores
  const getBestFields = (): string[] => {
    return Object.entries(fieldConfidenceScores)
      .filter(([_, score]) => score >= 0.8)
      .sort(([_, a], [__, b]) => b - a)
      .slice(0, 3)
      .map(([field, _]) => field.replace('_', ' '));
  };

  const bestFields = getBestFields();

  return (
    <div className={`bg-white border rounded-lg p-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">Extraction Quality</h3>
        
        {/* Overall score badge */}
        <div className="text-right">
          <div className="text-2xl font-bold text-gray-800">
            {Math.round(overallConfidence * 100)}%
          </div>
          <div className="text-sm text-gray-500">Overall</div>
        </div>
      </div>

      {/* Method comparison */}
      {showComparison && (llmConfidence !== null || ocrConfidence !== null) && (
        <div className="space-y-3 mb-4">
          {llmConfidence !== null && llmConfidence !== undefined && (
            <ConfidenceBar
              label="LLM Extraction"
              confidence={llmConfidence}
              color="bg-blue-500"
              isActive={isLLMUsed}
            />
          )}
          
          {ocrConfidence !== null && ocrConfidence !== undefined && (
            <ConfidenceBar
              label="OCR Extraction"
              confidence={ocrConfidence}
              color="bg-gray-500"
              isActive={isOCROnly || isLLMFallback}
            />
          )}
        </div>
      )}

      {/* Improvement indicator */}
      {hasImprovement && (
        <div className="mb-4 p-3 bg-green-50 rounded-lg border border-green-200">
          <div className="flex items-center">
            <span className="text-green-600 mr-2">📈</span>
            <div>
              <div className="text-sm font-medium text-green-700">
                LLM Improved Accuracy
              </div>
              <div className="text-sm text-green-600">
                +{Math.round(improvement * 100)}% better than OCR alone
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Fallback indicator */}
      {isLLMFallback && (
        <div className="mb-4 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
          <div className="flex items-center">
            <span className="text-yellow-600 mr-2">⚠️</span>
            <div>
              <div className="text-sm font-medium text-yellow-700">
                Fallback Used
              </div>
              <div className="text-sm text-yellow-600">
                LLM processing failed, OCR was used instead
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Field-level confidence */}
      {Object.keys(fieldConfidenceScores).length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Field Confidence</h4>
          
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(fieldConfidenceScores)
              .sort(([_, a], [__, b]) => b - a)
              .slice(0, 6)
              .map(([field, score]) => (
                <div key={field} className="flex justify-between items-center text-sm">
                  <span className="text-gray-600 capitalize truncate">
                    {field.replace('_', ' ')}
                  </span>
                  <span className={`font-medium ${score >= 0.8 ? 'text-green-600' : score >= 0.6 ? 'text-yellow-600' : 'text-red-600'}`}>
                    {Math.round(score * 100)}%
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Best performing fields */}
      {bestFields.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">High Confidence Fields</h4>
          <div className="flex flex-wrap gap-1">
            {bestFields.map((field) => (
              <span
                key={field}
                className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded-full"
              >
                {field}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Quality recommendations */}
      {overallConfidence < 0.7 && (
        <div className="p-3 bg-orange-50 rounded-lg border border-orange-200">
          <div className="flex items-start">
            <span className="text-orange-600 mr-2 mt-0.5">💡</span>
            <div>
              <div className="text-sm font-medium text-orange-700">
                Quality Recommendations
              </div>
              <div className="text-sm text-orange-600 mt-1">
                {overallConfidence < 0.5 && "Consider re-uploading with higher quality image"}
                {overallConfidence >= 0.5 && overallConfidence < 0.7 && "Manual review recommended for accuracy"}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Method explanation */}
      <div className="mt-4 text-xs text-gray-500">
        <div className="flex items-center">
          <span className="mr-1">ℹ️</span>
          <span>
            {isLLMUsed && "Advanced AI model used for extraction"}
            {isLLMFallback && "OCR used after AI model timeout"}
            {isOCROnly && "Traditional OCR extraction used"}
          </span>
        </div>
      </div>
    </div>
  );
};

export default QualityIndicator;