# Plan Project Overview

## Usage: plan-project-overview [BRD_FILE] [ARCHITECTURE_FILE]

Generate master planning documents (PROJECT_PHASE_PLAN.md + PHASE_DEPENDENCY_MAP.md) by analyzing Business Requirements Document and Architecture without creating individual phase requirements files.

## Purpose

This focused command creates the high-level project planning documents that:
- Analyzes project complexity from BRD and architecture documents
- Applies dependency mapping algorithms to determine optimal phases
- Creates master phase plan with dependency visualization
- Establishes foundation for subsequent detailed phase generation
- Eliminates API timeout issues by reducing context size

## Usage Examples
```bash
/plan-project-overview PLANNING/BRD_TradeAssist.md PLANNING/Architecture_TradeAssist.md
/plan-project-overview requirements/business_requirements.md docs/system_architecture.md
/plan-project-overview BRD.md ARCHITECTURE.md
```

## Prerequisites Validation
Before executing this command, validate that:
- [ ] BRD document exists and is readable
- [ ] Architecture document exists and is readable
- [ ] templates/planning/PROJECT_PHASE_PLAN.md exists
- [ ] templates/planning/PHASE_DEPENDENCY_MAP.md exists
- [ ] Write permissions to PRP-PLANNING/ directory

## Analysis Process

### 1. Document Analysis & Requirements Extraction

#### BRD Analysis
```bash
# Extract key project elements from BRD
- Business objectives and success criteria
- User stories and functional requirements
- Performance requirements and constraints
- Integration requirements (APIs, services, external systems)
- Scope boundaries and non-functional requirements
- Delivery scope and expectations
```

#### Architecture Analysis  
```bash
# Extract technical complexity indicators
- System components and their relationships
- Technology stack and dependencies
- Data flow patterns and integration points
- Performance bottlenecks and critical paths
- Security requirements and compliance needs
- Scalability and deployment requirements
```

### 2. Complexity Assessment & Component Identification

#### Component Categorization
```bash
# Classify components by type and complexity
Foundation Components (Must be first):
- Database schema and data models
- Core business logic and services
- Authentication and security foundation
- Basic API structure

User Interface Components (Depend on foundation):
- Frontend applications
- User interaction patterns
- Dashboard and reporting interfaces
- Real-time UI updates

Integration Components (Depend on foundation + UI):
- External API integrations
- Third-party service connections
- Notification systems
- Monitoring and logging

Optimization Components (Depend on working system):
- Performance tuning
- Caching and optimization
- Production deployment
- Documentation finalization
```

#### Dependency Mapping
```bash
# Create dependency graph between components
1. Identify hard dependencies (A must exist before B)
2. Identify soft dependencies (A should exist before B for efficiency)
3. Identify parallel opportunities (A and B can develop simultaneously)
4. Identify integration bottlenecks (components that many others depend on)
```

### 3. Phase Optimization Algorithm

#### Dependency-Driven Sequencing
```bash
# Create optimal phase sequence
1. Start with foundation components that have no dependencies
2. Group components with similar dependency levels
3. Minimize cross-phase dependencies
4. Balance phase scope and complexity
5. Identify critical path and optimize for it
```

### 4. Integration Point Planning

#### API Contract Design
```bash
# Plan API interfaces between phases
Phase N APIs for Phase N+1:
- Define exact endpoint signatures
- Document request/response formats
- Plan authentication and authorization
- Design WebSocket message formats
- Plan event hooks and extension points
```

#### Database Evolution Planning
```bash
# Plan database schema evolution
- Design initial schema for foundation phase
- Plan schema extensions for each subsequent phase
- Design migration strategy between phases
- Plan performance optimization points
- Design backup and recovery strategy
```

## Output Files Generated

### Primary Outputs
- **PROJECT_PHASE_PLAN.md**: Master phase planning document with:
  - Project overview from BRD and Architecture analysis
  - Complete phase breakdown summary
  - Phase dependencies and sequencing
  - Integration points and API planning
  - Success metrics and validation criteria

- **PHASE_DEPENDENCY_MAP.md**: Visual dependency mapping with:
  - Component dependency graph
  - Critical path analysis
  - Parallel development opportunities
  - Integration bottlenecks identification

### Master Phase Plan Document Structure
```markdown
# PROJECT_PHASE_PLAN.md Contents
## Project Overview
- Business objectives from BRD
- Technical approach from Architecture
- Overall project milestones

## Phase Breakdown Summary
Phase 1: [Name] - [Scope] - [Dependencies: None] - [Estimated Effort]
Phase 2: [Name] - [Scope] - [Dependencies: Phase 1] - [Estimated Effort]
Phase 3: [Name] - [Scope] - [Dependencies: Phase 1, 2] - [Estimated Effort]
...

## Dependency Analysis
- Critical path components
- Parallel development opportunities
- Integration bottlenecks
- Risk mitigation strategies

## Integration Strategy
- API contract design across phases
- Database evolution plan
- Performance baseline establishment
- Testing and validation approach

## Success Metrics
- Phase completion criteria
- Performance benchmarks
- Quality gates
- Integration validation points
```

## Advanced Planning Strategies

### Project Type Patterns

#### Trading/Financial Applications
```bash
# Typical phase pattern for trading systems
Phase 1: Data ingestion + Core business logic
Phase 2: User interface + Dashboard
Phase 3: Notifications + Integrations  
Phase 4: Performance optimization + Production
```

#### E-commerce Applications
```bash
# Typical phase pattern for e-commerce
Phase 1: Product catalog + User management
Phase 2: Shopping cart + Checkout flow
Phase 3: Payment processing + Order management
Phase 4: Advanced features + Analytics
```

#### SaaS Applications
```bash
# Typical phase pattern for SaaS
Phase 1: Core functionality + Basic UI
Phase 2: Multi-tenancy + User management
Phase 3: Billing + Advanced features
Phase 4: Scaling + Enterprise features
```

### Performance-Driven Planning
```bash
# When performance is critical (like sub-second requirements)
- Start with performance-critical components first
- Design optimization phases early in the plan
- Include performance validation in every phase
- Plan load testing as early as possible
```

### Integration-Heavy Planning
```bash
# When many external integrations exist
- Group integration components together
- Plan integration phases after stable foundation
- Design circuit breaker and error handling early
- Include integration testing in every relevant phase
```

## Quality Checklist

### Planning Completeness
- [ ] All BRD requirements mapped to phases
- [ ] All architecture components addressed
- [ ] Dependencies properly sequenced
- [ ] Integration points clearly defined
- [ ] Performance requirements distributed appropriately

### Phase Quality
- [ ] Each phase has clear, measurable objectives
- [ ] Phase scope is appropriate for complexity
- [ ] Integration requirements are well-defined
- [ ] Success criteria are specific and testable

### Documentation Quality
- [ ] Master plan document is complete and accurate
- [ ] Dependency map is clear and actionable
- [ ] Technical specifications are detailed enough
- [ ] Integration examples are provided where needed

## Command Execution Flow

### Step 1: Document Ingestion
- Read and parse BRD document
- Read and parse Architecture document
- Extract requirements, constraints, and technical details

### Step 2: Analysis Engine
- Apply complexity analysis algorithms
- Create dependency mapping
- Determine optimal phase breakdown
- Calculate phase sizing and sequencing

### Step 3: Master Plan Generation
- Generate PROJECT_PHASE_PLAN.md with complete overview
- Create PHASE_DEPENDENCY_MAP.md with visual dependencies
- Include integration strategy and success metrics
- Provide phase numbering and naming conventions

### Step 4: Validation & Output
- Validate generated phase plan for completeness
- Check dependency logic and sequencing
- Provide planning summary and next step recommendations
- Output list of generated planning files

## Integration with Enhanced Workflow

This command becomes **Step 0A** in the split Complex PRP workflow:

**Step 0A**: `/plan-project-overview [BRD] [ARCHITECTURE]` - Generate master planning documents  
**Step 0B**: `/generate-phase-requirements` - Generate detailed phase requirements  
**Step 1.1**: Skip manual phase planning - use generated files  
**Step 1.2**: Use generated PHASE1_REQUIREMENTS.md directly  
**Step 1.3**: Execute `/generate-prp PHASE1_REQUIREMENTS.md`  

## Success Metrics

A successful project overview should achieve:
- **Comprehensive Coverage**: All BRD requirements analyzed and mapped
- **Optimal Dependencies**: Phases properly sequenced with minimal cross-dependencies  
- **Realistic Scope**: Phase breakdown appropriately sized for complexity
- **Clear Strategy**: Integration and performance strategy well-defined
- **Actionable Plan**: Ready foundation for detailed phase requirements generation

The resulting master plan should enable focused, efficient generation of individual phase requirements without API timeout issues.