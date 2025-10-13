<!--
Sync Impact Report - Constitution v1.0.0
========================================
Version change: Template → 1.0.0 (Initial constitution)
Modified principles: All principles defined (was template placeholders)
Added sections: Technical Standards, Development Workflow
Removed sections: None
Templates requiring updates:
  ✅ .specify/templates/plan-template.md (Web application structure matches React/FastAPI)
  ✅ .specify/templates/spec-template.md (No changes needed - technology agnostic)
  ✅ Command files (No changes needed - generic guidance maintained)
Follow-up TODOs: None - all placeholders resolved
-->

# Spec-Kit Constitution

## Core Principles

### I. Monorepo Structure
Every feature development MUST respect the clear separation between frontend and backend while maintaining shared tooling and standards. Frontend code resides in `frontend/` using React/Vite, backend code resides in `backend/` using Python/FastAPI. Shared configurations, documentation, and tooling exist at the repository root. Cross-cutting concerns like authentication, logging, and error handling MUST be coordinated between frontend and backend but implemented according to platform conventions.

### II. API-First Development
All feature development MUST begin with API contract definition using OpenAPI/FastAPI schemas. Frontend development follows the established API contracts. Database models derive from API schemas using Pydantic. Contract tests validate both sides of the API boundary. No frontend implementation begins until API contracts are defined and validated.

### III. Test-First Methodology (NON-NEGOTIABLE)
TDD is mandatory across the entire stack. Backend tests use pytest with contract, integration, and unit test layers. Frontend tests use Vitest with component, integration, and unit test layers. Tests MUST be written before implementation. Red-Green-Refactor cycle is strictly enforced. All API endpoints require contract tests. All React components require unit tests.

### IV. Type Safety
Type safety is enforced across the entire application stack. Frontend uses TypeScript with strict configuration. Backend uses Python with Pydantic models for all data validation. API contracts ensure type compatibility between frontend and backend. No `any` types in TypeScript except for legitimate dynamic content. No untyped data structures in Python except for validated external inputs.

### V. Developer Experience
Development environment MUST provide instant feedback and minimal friction. Frontend uses Vite hot module replacement for instant updates. Backend uses FastAPI auto-reload for development. Automated linting and formatting with pre-commit hooks. Clear error messages and debugging capabilities. Comprehensive documentation for setup, development, and deployment processes.

## Technical Standards

All code MUST pass automated quality checks before merge. Frontend linting uses ESLint with TypeScript rules, formatting uses Prettier. Backend linting uses Ruff, formatting uses Black, type checking uses mypy. Test coverage MUST be maintained above 80% for new code. Performance budgets enforce frontend bundle size limits and backend response time requirements. Security scanning runs on all dependencies and code changes.

## Development Workflow

Feature development follows the SpecKit workflow: specification → planning → implementation → validation. All features require approval of both API contracts and frontend mockups before implementation begins. Code reviews MUST verify compliance with type safety, test coverage, and performance requirements. Deployment requires passing all automated tests and manual QA approval. Breaking changes require migration planning and backward compatibility consideration.

## Governance

This constitution supersedes all other development practices and tools. All pull requests MUST verify compliance with these principles through automated checks and human review. Complexity that violates these principles MUST be justified with documented rationale and approval. Constitution amendments require documentation of impact, migration plan, and team approval. Runtime development guidance is maintained in `CLAUDE.md` for AI agent integration.

**Version**: 1.0.0 | **Ratified**: 2025-01-10 | **Last Amended**: 2025-01-10