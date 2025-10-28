# Implementation Plan: Enhanced Image Processing with Local LLM Integration

**Branch**: `002-enhanced-image-processing` | **Date**: 2025-01-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-enhanced-image-processing/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Enhance the existing invoice automation application with advanced image preprocessing (thresholding, deskewing) and local Llama 3.2 LLM integration to improve data extraction accuracy for poor quality invoice images. Core architecture integrates OpenCV preprocessing pipeline with REST API calls to local LLM, maintaining fallback to existing OCR processing with 60-second timeout and 2GB memory limits.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.11+ (backend), TypeScript 5.0+ (frontend)  
**Primary Dependencies**: FastAPI, OpenCV, Llama 3.2 REST API, Pydantic, React 18, Vite 5  
**Storage**: SQLite database (existing), local filesystem (temporary preprocessed images)  
**Testing**: pytest (backend), Vitest (frontend), contract testing for LLM API integration  
**Target Platform**: Desktop web application (cross-platform via browser)
**Project Type**: Web application with frontend and backend separation  
**Performance Goals**: 60-second LLM timeout, 25% accuracy improvement, 95% pipeline success rate  
**Constraints**: 2GB memory limit per operation, local-only processing, offline-capable  
**Scale/Scope**: Single user, ~1000 documents, configurable preprocessing parameters

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Monorepo Structure ✅
- Enhancement integrates into existing `backend/src/services/` for preprocessing and LLM integration
- Frontend updates in `frontend/src/components/` for preprocessing configuration UI
- Shared temporary file storage coordinated between layers
- Cross-cutting concerns (error handling, timeout management) coordinated between frontend and backend

### II. API-First Development ✅
- New API endpoints for preprocessing configuration and LLM processing status
- Extended existing invoice processing contracts with LLM integration fields
- Contract tests validate LLM API integration and preprocessing pipeline
- Database models extended from existing Pydantic schemas

### III. Test-First Methodology ✅
- Backend: pytest with contract tests for LLM API integration, integration tests for preprocessing pipeline
- Frontend: Vitest with component tests for configuration UI and status displays
- TDD cycle: tests for preprocessing operations → implementation → refactor
- All new API endpoints and React components require tests

### IV. Type Safety ✅
- Backend: Python with Pydantic models for preprocessing configurations and LLM responses
- Frontend: TypeScript with strict configuration for new preprocessing interfaces
- API contracts ensure type compatibility for enhanced processing pipeline
- No `any` types except for LLM response handling with proper validation

### V. Developer Experience ✅
- Vite hot module replacement for frontend preprocessing UI development
- FastAPI auto-reload for backend LLM integration development
- Automated linting (ESLint, Ruff) and formatting (Prettier, Black)
- Clear error messages for preprocessing failures and LLM timeouts

**GATE STATUS: PASS** - All constitutional requirements satisfied for enhancement

**Post-Design Re-evaluation** (Phase 1 Complete):

### I. Monorepo Structure ✅  
- API contracts defined in `contracts/api.yaml` maintain separation of concerns
- Database models extended via migration strategy preserving existing structure
- Shared preprocessing configurations coordinate frontend/backend without tight coupling

### II. API-First Development ✅
- Complete OpenAPI 3.0 specification generated with enhanced endpoints
- Pydantic models defined for all new entities with validation rules
- Contract-driven development enables parallel frontend/backend work
- Backward compatibility maintained with existing invoice processing API

### III. Test-First Methodology ✅
- Testing strategy documented in quickstart guide with specific test files
- Contract tests identified for LLM API integration points
- Integration tests planned for complete preprocessing → LLM → fallback pipeline
- Component tests specified for all new React preprocessing UI components

### IV. Type Safety ✅
- Complete TypeScript interfaces derivable from Pydantic schemas
- JSON schema validation for LLM responses with fallback error handling
- Strict typing for preprocessing configuration parameters
- No untyped dynamic content except validated LLM response parsing

### V. Developer Experience ✅
- Comprehensive quickstart guide with step-by-step setup
- Environment configuration documented with all required variables
- Error handling patterns include debugging context and fallback information
- Hot reload development workflow preserved for both frontend and backend

**FINAL GATE STATUS: PASS** - Design maintains all constitutional principles

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```
backend/
├── src/
│   ├── models/          # Extended Pydantic schemas for preprocessing configs
│   ├── services/        # Enhanced image preprocessing and LLM integration
│   │   ├── image_preprocessor.py    # OpenCV thresholding and deskewing
│   │   ├── llm_client.py           # Llama 3.2 REST API integration
│   │   ├── enhanced_extractor.py   # Orchestrates preprocessing + LLM
│   │   └── fallback_manager.py     # Timeout and fallback handling
│   ├── api/             # Extended endpoints for preprocessing configuration
│   └── database/        # Database configuration (existing)
├── tests/
│   ├── contract/        # LLM API integration tests
│   ├── integration/     # Preprocessing pipeline tests
│   └── unit/            # Individual service tests
└── requirements.txt     # Updated with OpenCV and LLM dependencies

frontend/
├── src/
│   ├── components/      # Enhanced processing configuration UI
│   │   ├── PreprocessingConfig.tsx  # Parameter configuration
│   │   ├── ProcessingStatus.tsx     # Enhanced status with LLM progress
│   │   └── QualityIndicator.tsx     # Confidence score visualization
│   ├── pages/           # Updated review pages with LLM data
│   ├── services/        # Extended API client for preprocessing
│   ├── types/           # TypeScript interfaces for preprocessing
│   └── hooks/           # Custom hooks for processing status
├── tests/
│   ├── components/      # Component unit tests
│   └── integration/     # End-to-end testing
├── package.json         # Node dependencies (existing)
└── vite.config.ts       # Vite configuration (existing)

shared/
├── storage/            # Local file storage for temporary preprocessed images
└── database/           # SQLite database files (existing)
```

**Structure Decision**: Web application structure selected as enhancement to existing invoice automation system. Backend preprocessing services integrate with existing FastAPI structure, frontend configuration components extend existing React architecture. Shared storage manages temporary preprocessed images alongside existing document storage.

## Complexity Tracking

*No constitutional violations detected - all requirements align with established principles.*
