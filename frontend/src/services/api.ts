/**
 * API service for communicating with the backend
 */

import { 
  InvoiceDocument, 
  ExtractedData, 
  ProcessingJob, 
  ReviewSession,
  ProcessingMode,
  ProcessingStatus,
  ReviewDecision,
  ApiResponse 
} from '../types/api'

const API_BASE_URL = 'http://localhost:8000/api/v1'

class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    message: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

class ApiService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new ApiError(
        response.status,
        response.statusText,
        errorText || `HTTP ${response.status}`
      )
    }

    // Handle empty responses
    const contentType = response.headers.get('Content-Type')
    if (contentType && contentType.includes('application/json')) {
      return response.json()
    }
    
    return response.text() as unknown as T
  }

  // Document endpoints
  async uploadDocument(
    file: File,
    processingMode: ProcessingMode = ProcessingMode.SEQUENTIAL
  ): Promise<InvoiceDocument> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('processing_mode', processingMode)

    return this.request<InvoiceDocument>('/documents/upload', {
      method: 'POST',
      headers: {}, // Remove Content-Type to let browser set it for FormData
      body: formData,
    })
  }

  async getDocument(id: string): Promise<InvoiceDocument> {
    return this.request<InvoiceDocument>(`/documents/${id}`)
  }

  async listDocuments(
    skip: number = 0,
    limit: number = 100,
    status?: ProcessingStatus
  ): Promise<InvoiceDocument[]> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    })
    
    if (status) {
      params.append('status', status)
    }

    return this.request<InvoiceDocument[]>(`/documents?${params}`)
  }

  async deleteDocument(id: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/documents/${id}`, {
      method: 'DELETE',
    })
  }

  // Processing endpoints
  async getProcessingJobs(
    skip: number = 0,
    limit: number = 100,
    status?: ProcessingStatus
  ): Promise<ProcessingJob[]> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    })
    
    if (status) {
      params.append('status', status)
    }

    return this.request<ProcessingJob[]>(`/processing/jobs?${params}`)
  }

  async getProcessingJob(id: string): Promise<ProcessingJob> {
    return this.request<ProcessingJob>(`/processing/jobs/${id}`)
  }

  async retryProcessingJob(id: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/processing/jobs/${id}/retry`, {
      method: 'POST',
    })
  }

  async getDocumentProcessingJobs(documentId: string): Promise<ProcessingJob[]> {
    return this.request<ProcessingJob[]>(`/documents/${documentId}/processing-jobs`)
  }

  // Extracted data endpoints
  async getExtractedData(
    skip: number = 0,
    limit: number = 100,
    minConfidence?: number
  ): Promise<ExtractedData[]> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    })
    
    if (minConfidence !== undefined) {
      params.append('min_confidence', minConfidence.toString())
    }

    return this.request<ExtractedData[]>(`/processing/extracted-data?${params}`)
  }

  async getExtractedDataById(id: string): Promise<ExtractedData> {
    return this.request<ExtractedData>(`/processing/extracted-data/${id}`)
  }

  async getDocumentExtractedData(documentId: string): Promise<ExtractedData> {
    return this.request<ExtractedData>(`/processing/documents/${documentId}/extracted-data`)
  }

  // Review endpoints
  async startReviewSession(
    documentId: string,
    sessionData: Omit<ReviewSession, 'id' | 'created_at' | 'updated_at' | 'invoice_document_id'>
  ): Promise<ReviewSession> {
    return this.request<ReviewSession>(`/processing/documents/${documentId}/review`, {
      method: 'POST',
      body: JSON.stringify(sessionData),
    })
  }

  async getReviewSessions(
    skip: number = 0,
    limit: number = 100,
    status?: string
  ): Promise<ReviewSession[]> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    })
    
    if (status) {
      params.append('status', status)
    }

    return this.request<ReviewSession[]>(`/processing/review-sessions?${params}`)
  }

  async getReviewSession(id: string): Promise<ReviewSession> {
    return this.request<ReviewSession>(`/processing/review-sessions/${id}`)
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/health', {
      headers: {}, // Remove JSON content type for health check
    })
  }
}

export const apiService = new ApiService()
export { ApiError }