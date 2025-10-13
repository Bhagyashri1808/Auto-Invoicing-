# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Spec-Kit is a structured software development framework based on the Specify methodology. It provides a complete workflow for feature specification, planning, and implementation using template-driven development with AI assistance.

## Commands for Development

### Core SpecKit Commands (via .claude/commands/)

**Feature Specification**:
```bash
/speckit.specify [feature description]
```
Creates a new feature branch and generates a complete specification from natural language input.

**Implementation Planning**:
```bash
/speckit.plan
```
Generates technical implementation plan, data models, API contracts, and research documentation.

**Task Generation**:
```bash
/speckit.tasks
```
Creates detailed task breakdown for implementation from the plan.

**Implementation Execution**:
```bash
/speckit.implement
```
Executes the implementation plan by processing tasks sequentially.

**Constitution Management**:
```bash
/speckit.constitution [principles]
```
Creates or updates project constitution with development principles and constraints.

**Clarification Workflow**:
```bash
/speckit.clarify
```
Resolves specification ambiguities through interactive clarification.

**Analysis Tools**:
```bash
/speckit.analyze [scope]
```
Analyzes codebase structure, dependencies, and technical decisions.

**Checklist Management**:
```bash
/speckit.checklist [type]
```
Generates validation checklists for requirements, testing, security, etc.

### Project Structure

**Specification Documents** (`.specify/`):
- `memory/constitution.md` - Project principles and development constraints
- `templates/` - Templates for specs, plans, tasks, and checklists
- `scripts/bash/` - Automation scripts for branch management and setup

**Feature Documentation** (`specs/[###-feature]/`):
- `spec.md` - Feature specification (business requirements)
- `plan.md` - Implementation plan (technical design)
- `research.md` - Technical research and decisions
- `data-model.md` - Entity definitions and relationships
- `contracts/` - API specifications and schemas
- `tasks.md` - Detailed implementation tasks
- `checklists/` - Validation checklists

**Claude Commands** (`.claude/commands/`):
- Command definitions for the SpecKit workflow
- Each command includes detailed execution instructions and validation rules

## Architecture

### Development Workflow

1. **Specify** - Convert feature ideas into structured specifications
2. **Plan** - Generate technical implementation plans and contracts
3. **Tasks** - Break down plans into executable development tasks
4. **Implement** - Execute tasks following TDD principles
5. **Validate** - Use checklists to ensure quality and completeness

### Key Principles

- **Template-driven**: All artifacts follow standardized templates
- **AI-assisted**: Commands are designed for AI agents to execute autonomously
- **Test-first**: TDD approach with contract and integration testing
- **Constitution-based**: Development follows project-specific principles
- **Incremental**: Features developed as independent, testable slices

### File Organization

The framework uses a clear separation between:
- **Business specifications** (what to build) in `specs/`
- **Implementation artifacts** (how to build) in source directories
- **Process templates** (how to work) in `.specify/`
- **AI commands** (automation) in `.claude/`

## Working with SpecKit

### Starting a New Feature
1. Use `/speckit.specify` with a natural language description
2. Review generated specification for completeness
3. Use `/speckit.clarify` if clarification questions arise
4. Proceed to `/speckit.plan` for technical design

### Implementation Flow
1. Run `/speckit.plan` to generate technical artifacts
2. Use `/speckit.tasks` to create implementation tasks
3. Execute with `/speckit.implement` following TDD approach
4. Validate using generated checklists

### Constitution and Constraints
- Check `constitution.md` for project-specific development principles
- Constitution gates must pass before proceeding with implementation
- Complex features may require violation justification

## Important Notes

- All commands expect to be run from repository root
- Feature branches are automatically created and managed
- Scripts use JSON output for programmatic parsing
- Templates contain placeholder tokens (e.g., `[FEATURE_NAME]`) that get replaced
- Validation checklists ensure quality gates are met before proceeding
