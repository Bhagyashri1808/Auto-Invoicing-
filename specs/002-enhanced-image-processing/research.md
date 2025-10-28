# Research and Technical Decisions

**Feature**: Enhanced Image Processing with Local LLM Integration  
**Date**: 2025-01-23  
**Status**: Complete

## LLM Integration Strategy

### Decision: Ollama with Llama 3.2 3B via REST API
**Rationale**: Ollama provides the simplest setup with built-in REST API server, OpenAI-compatible endpoints, and excellent model management. Given the 8GB RAM constraint, Llama 3.2 3B (~3GB RAM requirement) provides the best balance of accuracy and resource usage. The REST API approach provides loose coupling and better error handling compared to direct library integration.

**Alternatives considered**:
- Llama 3.2 11B (rejected - requires 22-30GB RAM, exceeds system requirements)
- vLLM (rejected - overkill for single-user application, higher resource overhead)
- llama.cpp server (rejected - more complex setup, similar performance to Ollama)
- Direct Python library integration (rejected - tight coupling, harder timeout management)

### Decision: Structured JSON Output with Pydantic Validation
**Rationale**: Using JSON schema-constrained output from the LLM with Pydantic model validation ensures type safety and data consistency. This approach provides better error handling and integration with the existing FastAPI/Pydantic architecture.

**Implementation approach**:
- JSON schema definition for invoice structure
- Pydantic models for runtime validation
- Fallback to OCR when LLM output validation fails
- Confidence scoring based on field completeness and validation success

## Image Preprocessing Strategy

### Decision: Enhanced Adaptive Thresholding with Bilateral Filtering
**Rationale**: Adaptive thresholding performs better than OTSU for invoices with varying lighting conditions. Bilateral filtering preserves edges while reducing noise, critical for maintaining text readability. The combination provides superior results for poor-quality invoice images.

**Alternatives considered**:
- OTSU thresholding only (current approach - limited performance on varied lighting)
- Simple Gaussian blur (rejected - loses text edge definition)
- Morphological operations only (rejected - insufficient for complex noise patterns)

### Decision: MinAreaRect-based Deskewing with Contour Analysis
**Rationale**: Using contour analysis to identify text blocks and calculating rotation angle via minAreaRect provides more robust deskewing than single-line detection. The median angle approach handles documents with multiple text orientations.

**Implementation approach**:
- Dilate text into blocks for better contour detection
- Filter contours by area to avoid noise
- Use median angle for robust rotation calculation
- Apply rotation with border padding to avoid cropping

### Decision: Memory-Efficient Tiled Processing
**Rationale**: For large images approaching the 2GB memory limit, tiled processing with overlap ensures memory compliance while maintaining processing quality. This approach allows handling of high-resolution PDF pages without system crashes.

**Implementation approach**:
- Estimate memory requirements before processing
- Use 2048x2048 tiles with 128-pixel overlap
- Stitch results with overlap blending
- Monitor memory usage during processing

## Integration Architecture

### Decision: Service Layer Extension Pattern
**Rationale**: Extend the existing service architecture with new preprocessing and LLM services rather than modifying core OCR functionality. This maintains backward compatibility and allows gradual rollout.

**Service structure**:
- `ImagePreprocessor`: OpenCV operations with configurable parameters
- `LLMClient`: REST API integration with timeout and retry logic
- `EnhancedExtractor`: Orchestrates preprocessing → LLM → fallback workflow
- `FallbackManager`: Handles timeouts and error scenarios

### Decision: Circuit Breaker Pattern for LLM Reliability
**Rationale**: Implement circuit breaker pattern to handle LLM service failures gracefully. This prevents cascade failures and provides automatic recovery when the service becomes available again.

**Configuration**:
- 3 failure threshold before opening circuit
- 60-second recovery timeout
- Automatic fallback to OCR when circuit is open

## Performance and Resource Management

### Decision: Aggressive Memory Monitoring
**Rationale**: With 2GB memory limit per operation, proactive memory monitoring prevents system instability. Early detection allows switching to tiled processing or triggering garbage collection.

**Monitoring approach**:
- psutil-based memory tracking
- 1.8GB threshold for switching to emergency processing mode
- Automatic garbage collection after large operations
- Memory usage logging for optimization insights

### Decision: 60-Second Hard Timeout with Exponential Backoff
**Rationale**: 60-second timeout balances processing quality with user experience. Exponential backoff on retries prevents overwhelming a struggling LLM service while providing resilience to temporary failures.

**Retry configuration**:
- Maximum 3 retry attempts
- Exponential backoff: 4, 8, 16 seconds
- Circuit breaker integration for failure management
- Immediate fallback after timeout

## Hardware and Deployment Considerations

### Decision: CPU-Optimized Deployment
**Rationale**: Given 8GB RAM constraint, optimize for CPU processing rather than GPU acceleration. This approach ensures broader deployment compatibility and predictable resource usage.

**Optimization settings**:
- OpenCV multi-threading enabled
- CPU-only LLM inference
- Memory-mapped model loading where possible
- Process-level resource limits

### Decision: Local File Storage with Cleanup
**Rationale**: Use temporary file storage for preprocessed images with automatic cleanup. This approach provides debugging capabilities while preventing disk space accumulation.

**Storage management**:
- Temporary directory for preprocessed images
- Unique filenames to prevent conflicts
- Automatic cleanup after processing completion
- Configurable retention for debugging

## API Design Decisions

### Decision: Extend Existing Invoice Processing Endpoints
**Rationale**: Enhance existing `/invoices` endpoints rather than creating separate preprocessing endpoints. This maintains API consistency and simplifies client integration.

**Endpoint extensions**:
- Add preprocessing options to upload endpoint
- Extend processing status with LLM progress
- Include preprocessing metadata in response
- Maintain backward compatibility for existing clients

### Decision: Configurable Preprocessing Parameters
**Rationale**: Allow users to tune preprocessing parameters for their specific document types. This flexibility improves accuracy for edge cases while maintaining simple defaults.

**Configuration options**:
- Target image width (800-3200 pixels)
- Adaptive threshold block size (11-51, odd numbers)
- Threshold constant (5-20)
- Processing mode selection (threshold vs deskew)

## Testing Strategy

### Decision: Multi-Layer Testing Approach
**Rationale**: Test preprocessing, LLM integration, and end-to-end workflows separately to isolate failures and ensure reliable deployment.

**Testing layers**:
- Unit tests for individual preprocessing functions
- Contract tests for LLM API integration
- Integration tests for complete processing pipeline
- Performance tests for memory and timeout compliance

This research provides the technical foundation for implementing enhanced image processing with local LLM integration while respecting the specified constraints and requirements.