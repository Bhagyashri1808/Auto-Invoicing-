# Tasks: Enhanced Image Processing with Local LLM Integration

**Input**: Design documents from `/specs/002-enhanced-image-processing/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 [P] Install OpenCV dependencies in backend/requirements.txt
- [x] T002 [P] Add LLM client dependencies (httpx, aiohttp) to backend/requirements.txt
- [x] T003 [P] Create storage directory structure for temporary preprocessed images
- [x] T004 [P] Configure environment variables for LLM integration (LLM_BASE_URL, MODEL_NAME)
- [x] T005 [P] Setup TypeScript types for preprocessing in frontend/src/types/preprocessing.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Create database migrations for new tables in backend/src/database/migrations/
  - preprocessing_configurations table
  - llm_processing_jobs table  
  - processing_performance_metrics table
- [x] T007 Extend extracted_data table with new LLM fields in database migration
- [x] T008 [P] Create base Pydantic models for preprocessing in backend/src/models/preprocessing.py
- [x] T009 [P] Create base Pydantic models for LLM processing in backend/src/models/llm_processing.py
- [x] T010 [P] Create base Pydantic models for performance metrics in backend/src/models/performance.py
- [x] T011 Setup error handling framework for preprocessing failures in backend/src/services/error_handler.py
- [x] T012 [P] Configure timeout management utilities in backend/src/services/timeout_manager.py
- [x] T013 [P] Setup temporary file cleanup service in backend/src/services/file_cleanup.py
  - General temporary file management
  - Preprocessed image file cleanup after processing completion
  - Configurable retention policies
  - Background cleanup scheduling

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Improved Invoice Data Extraction from Poor Quality Images (Priority: P1) 🎯 MVP

**Goal**: Process poor quality images with OpenCV preprocessing and LLM extraction to achieve 25% accuracy improvement

**Independent Test**: Upload blurry/skewed invoice images and verify accuracy improvement over current OCR

### Tests for User Story 1 ⚠️

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T014 [P] [US1] Contract test for enhanced invoice processing in backend/tests/contract/test_enhanced_processing.py
- [x] T015 [P] [US1] Integration test for preprocessing pipeline in backend/tests/integration/test_preprocessing_pipeline.py
- [x] T016 [P] [US1] Component test for ProcessingStatus component in frontend/tests/components/ProcessingStatus.test.tsx

### Implementation for User Story 1

- [x] T017 [P] [US1] Create PreprocessingConfiguration model in backend/src/models/preprocessing.py
- [x] T018 [P] [US1] Create LLMProcessingJob model in backend/src/models/llm_processing.py
- [x] T019 [P] [US1] Create EnhancedExtractedData model extending existing in backend/src/models/extracted_data.py
- [x] T020 [US1] Implement OpenCV image preprocessor service in backend/src/services/image_preprocessor.py
  - Adaptive thresholding functionality
  - Image deskewing functionality
  - Target width upscaling functionality
  - Bilateral filtering for noise reduction
- [x] T021 [US1] Implement Llama 3.2 REST API client in backend/src/services/llm_client.py
  - HTTP client for Ollama API integration
  - Request/response handling with timeout
  - Model availability checking
- [x] T022 [US1] Create enhanced extraction orchestrator in backend/src/services/enhanced_extractor.py
  - Preprocessing + LLM pipeline coordination
  - Fallback to OCR on timeout/failure
  - Confidence score generation
- [x] T023 [US1] Implement confidence score calculation service in backend/src/services/confidence_calculator.py
  - LLM response confidence parsing
  - OCR confidence aggregation
  - Comparative scoring between methods
  - Field-level confidence mapping
- [x] T024 [US1] Extend existing /invoices POST endpoint in backend/src/api/routes/documents.py
  - Add preprocessing parameters
  - Add LLM processing options
  - Integrate enhanced extraction pipeline
- [x] T025 [US1] Extend existing /invoices/{id} GET endpoint in backend/src/api/routes/documents.py
  - Include LLM processing job details
  - Include preprocessing metadata
- [x] T026 [US1] Update invoice processing status display in frontend/src/components/ProcessingStatus.tsx
  - Show preprocessing progress
  - Show LLM processing status
  - Display confidence scores
- [x] T027 [US1] Create quality indicator component in frontend/src/components/QualityIndicator.tsx
  - Visual confidence score representation
  - Method comparison (OCR vs LLM)
- [x] T028 [US1] Update document detail page in frontend/src/pages/DocumentDetailPage.tsx
  - Display enhanced extraction results
  - Show processing method used
  - Include confidence metadata

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Fallback Processing for Complex Invoice Layouts (Priority: P2)

**Goal**: Handle complex table structures and multi-page documents with intelligent LLM context understanding

**Independent Test**: Upload invoices with complex tables and verify structured data extraction from relationships

### Tests for User Story 2 ⚠️

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T029 [P] [US2] Contract test for reprocessing endpoint in backend/tests/contract/test_reprocessing.py
- [ ] T030 [P] [US2] Integration test for complex layout handling in backend/tests/integration/test_complex_layouts.py

### Implementation for User Story 2

- [ ] T031 [US2] Enhance image preprocessor in backend/src/services/image_preprocessor.py
  - Multi-page document combination functionality
  - Complex layout detection
- [ ] T032 [US2] Extend LLM client in backend/src/services/llm_client.py
  - Enhanced prompt engineering for complex layouts
  - Context-aware field relationship extraction
- [ ] T033 [US2] Create reprocessing endpoint in backend/src/api/routes/processing.py
  - /invoices/{id}/reprocess POST endpoint
  - Different configuration options
  - Force reprocessing capability
- [ ] T034 [US2] Extend enhanced extractor in backend/src/services/enhanced_extractor.py
  - Complex layout handling logic
  - Multi-page processing coordination
  - Table structure recognition
- [ ] T035 [US2] Update document list page in frontend/src/pages/DocumentListPage.tsx
  - Show processing method indicators
  - Add reprocessing action buttons
- [ ] T036 [US2] Create reprocessing dialog in frontend/src/components/ReprocessingDialog.tsx
  - Configuration selection interface
  - Processing options
- [ ] T037 [US2] Update review page in frontend/src/pages/ReviewPage.tsx
  - Enhanced line item display for complex extractions
  - Context highlighting for LLM decisions

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Processing Configuration and Quality Control (Priority: P3)

**Goal**: Provide user control over preprocessing parameters and quality thresholds for optimization

**Independent Test**: Adjust preprocessing parameters and verify improved results for specific document types

### Tests for User Story 3 ⚠️

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T038 [P] [US3] Contract test for configuration endpoints in backend/tests/contract/test_preprocessing_config.py
- [ ] T039 [P] [US3] Component test for PreprocessingConfig UI in frontend/tests/components/PreprocessingConfig.test.tsx

### Implementation for User Story 3

- [ ] T040 [P] [US3] Create preprocessing configuration endpoints in backend/src/api/routes/preprocessing.py
  - GET /preprocessing/configurations endpoint
  - POST /preprocessing/configurations endpoint
  - PUT /preprocessing/configurations/{id} endpoint
- [ ] T041 [P] [US3] Create LLM health check endpoints in backend/src/api/routes/llm.py
  - GET /llm/health endpoint
  - GET /llm/models endpoint
- [ ] T042 [P] [US3] Create performance metrics endpoints in backend/src/api/routes/metrics.py
  - GET /processing/metrics endpoint
  - Processing job detail endpoint
- [ ] T043 [US3] Implement preprocessing configuration service in backend/src/services/preprocessing_config.py
  - Configuration validation
  - Default configuration management
  - User preference handling
- [ ] T044 [US3] Create preprocessing configuration UI in frontend/src/components/PreprocessingConfig.tsx
  - Parameter adjustment controls
  - Real-time validation
  - Preview functionality
- [ ] T045 [US3] Create performance metrics dashboard in frontend/src/components/MetricsDashboard.tsx
  - Processing time charts
  - Accuracy trend visualization
  - Method comparison statistics
- [ ] T046 [US3] Integrate configuration options in frontend/src/components/Navigation.tsx
  - Settings menu access
  - Configuration management

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T047 [P] Add comprehensive error handling across all preprocessing services
- [ ] T048 [P] Implement memory monitoring and cleanup in backend/src/services/memory_monitor.py
- [ ] T049 [P] Add circuit breaker pattern for LLM service reliability
- [ ] T050 [P] Create preprocessing configuration validation in frontend/src/hooks/usePreprocessingValidation.ts
- [ ] T051 [P] Add performance metrics collection throughout pipeline
- [ ] T052 [P] Implement automated temporary file cleanup job
- [ ] T053 Code cleanup and refactoring across preprocessing services
- [ ] T054 Performance optimization for large image processing
- [ ] T055 Security hardening for file upload and temporary storage
- [ ] T056 Run quickstart.md validation and update setup instructions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Extends US1 services but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May use US1/US2 but independently testable

### Within Each User Story

- Models before services (T014-T016 before T017-T019)
- Services before endpoints (T017-T019 before T020-T021)
- Backend endpoints before frontend components (T020-T021 before T022-T024)
- Core implementation before integration

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Models within each story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Create PreprocessingConfiguration model in backend/src/models/preprocessing.py"
Task: "Create LLMProcessingJob model in backend/src/models/llm_processing.py"
Task: "Create EnhancedExtractedData model extending existing in backend/src/models/extracted_data.py"

# After models complete, launch core services in sequence:
Task: "Implement OpenCV image preprocessor service in backend/src/services/image_preprocessor.py"
Task: "Implement Llama 3.2 REST API client in backend/src/services/llm_client.py"
Task: "Create enhanced extraction orchestrator in backend/src/services/enhanced_extractor.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently with poor quality invoice images
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP with basic preprocessing and LLM extraction!)
3. Add User Story 2 → Test independently → Deploy/Demo (Complex layout handling added)
4. Add User Story 3 → Test independently → Deploy/Demo (Full configuration and control)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (preprocessing pipeline)
   - Developer B: User Story 2 (complex layout handling)
   - Developer C: User Story 3 (configuration interface)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Focus on image preprocessing accuracy improvements for MVP
- LLM integration provides intelligent fallback beyond simple OCR
- Configuration options enable user optimization for their document types