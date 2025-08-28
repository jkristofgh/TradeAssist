# Plan Project Phases

## Usage: plan-project-phases [BRD_FILE] [ARCHITECTURE_FILE]

Systematically analyze Business Requirements Document (BRD) and Architecture document to create optimal phase breakdown and generate all PHASE[N]_REQUIREMENTS.md files for a Complex Multi-Phase PRP project.

## Purpose

This command transforms ad hoc phase planning into a systematic, data-driven process that:
- Analyzes project complexity from BRD and architecture documents
- Applies dependency mapping algorithms to determine optimal phases
- Creates properly sequenced phase requirements files with correct integration context
- Establishes phase dependencies and integration points upfront

## Usage Examples
```bash
/plan-project-phases PLANNING/BRD_TradeAssist.md PLANNING/Architecture_TradeAssist.md
/plan-project-phases requirements/business_requirements.md docs/system_architecture.md
/plan-project-phases BRD.md ARCHITECTURE.md
```

## Prerequisites Validation
Before executing this command, validate that:
- [ ] BRD document exists and is readable
- [ ] Architecture document exists and is readable
- [ ] templates/prp/TEMPLATE_PHASE_REQUIREMENTS.md exists
- [ ] templates/planning/PROJECT_PHASE_PLAN.md exists
- [ ] templates/planning/PHASE_DEPENDENCY_MAP.md exists
- [ ] Write permissions to PRPs/ directory for file generation

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

### 5. Phase Requirements File Generation

#### Create Phase Files
```bash
# Generate PHASE[N]_REQUIREMENTS.md files for each planned phase
For each phase 1 through N:
- Copy templates/prp/TEMPLATE_PHASE_REQUIREMENTS.md to ../PRP-PLANNING/PRPs/PHASE[N]_REQUIREMENTS.md
- Populate phase-specific information
- Add dependencies from previous phases
- Define integration requirements for next phases
- Include performance benchmarks and success criteria
```

#### Cross-Reference Integration
```bash
# Ensure proper cross-referencing between phases
- Phase N references completion summary from Phase N-1
- Phase N defines integration points for Phase N+1
- All phases reference master project architecture
- Performance baselines cascade through phases
```

### 6. Master Phase Plan Creation

#### Create PROJECT_PHASE_PLAN.md
```markdown
# Master Phase Plan Document Structure
## Project Overview
- Business objectives from BRD
- Technical approach from Architecture
- Overall project milestones

## Phase Breakdown Summary
Phase 1: [Name] - [Scope] - [Dependencies: None]
Phase 2: [Name] - [Scope] - [Dependencies: Phase 1]
Phase 3: [Name] - [Scope] - [Dependencies: Phase 1, 2]
...

## Dependency Map
[Visual representation of phase dependencies]

## Integration Points
[Critical integration points and their phases]


## Success Metrics
[How to measure project success across phases]
```

### 7. Validation & Quality Assurance

#### Phase Plan Validation
```bash
# Validate the generated phase plan
- Check that all BRD requirements are covered
- Verify all architecture components are addressed
- Ensure no circular dependencies exist
- Validate phase sizing is appropriate
- Check integration points are well-defined
```

#### Completeness Check
```bash
# Ensure all deliverables are created
- PROJECT_PHASE_PLAN.md exists and is complete
- All PHASE[N]_REQUIREMENTS.md files are created
- PHASE_DEPENDENCY_MAP.md is created
- Cross-references between files are correct
- All success criteria are measurable
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

## Output Files Generated

### Primary Outputs
- **PROJECT_PHASE_PLAN.md**: Master phase planning document
- **PHASE1_REQUIREMENTS.md**: First phase detailed requirements
- **PHASE2_REQUIREMENTS.md**: Second phase detailed requirements  
- **PHASE[N]_REQUIREMENTS.md**: Subsequent phase files as needed
- **PHASE_DEPENDENCY_MAP.md**: Visual dependency mapping

### Supporting Documents
- **PHASE_INTEGRATION_PLAN.md**: Integration strategy across phases
- **PERFORMANCE_BASELINE_PLAN.md**: Performance targets by phase

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
- [ ] All generated files are complete and accurate
- [ ] Cross-references between phases are correct
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

### Step 3: File Generation
- Generate PROJECT_PHASE_PLAN.md with overview
- Create all PHASE[N]_REQUIREMENTS.md files
- Generate dependency mapping document
- Create integration planning documents

### Step 4: Validation & Output
- Validate generated phase plan for completeness
- Check cross-references and integration points
- Provide phase plan summary and recommendations
- Output list of all generated files

## Integration with Existing Complex PRP Workflow

This command becomes **Step 0** in the enhanced Complex PRP workflow:

**Step 0**: `/plan-project-phases [BRD] [ARCHITECTURE]` - Generate systematic phase plan  
**Step 1.1**: Skip manual phase planning - use generated files  
**Step 1.2**: Use generated PHASE1_REQUIREMENTS.md directly  
**Step 1.3**: Execute `/generate-prp PHASE1_REQUIREMENTS.md`  
**Step 1.4**: Execute `/update-phase-completion 1`  
**Step N.1**: Use pre-generated PHASE[N]_REQUIREMENTS.md files  

## Success Metrics

A successful phase plan should achieve:
- **Comprehensive Coverage**: All BRD requirements addressed across phases
- **Optimal Dependencies**: Phases properly sequenced with minimal cross-dependencies  
- **Realistic Scope**: Each phase appropriately sized for complexity and dependencies
- **Clear Integration**: Integration points well-defined with concrete examples
- **Measurable Success**: Each phase has specific, testable success criteria

The resulting phase plan should enable seamless execution of the entire Complex PRP workflow with minimal integration issues and maximum development velocity.