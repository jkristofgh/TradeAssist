# Generate Phase Requirements

## Usage: generate-phase-requirements [phase_numbers...]

Generate detailed PHASE[N]_REQUIREMENTS.md files based on existing PROJECT_PHASE_PLAN.md. Can generate all phases or specific phases incrementally to avoid timeout issues.

## Purpose

This focused command creates detailed phase requirements files that:
- Uses existing PROJECT_PHASE_PLAN.md as the foundation
- Generates individual PHASE[N]_REQUIREMENTS.md files incrementally
- Enables fault-tolerant phase generation (retry individual phases if needed)
- Provides progressive workflow with better user control
- Eliminates API timeout issues through incremental processing

## Usage Examples
```bash
# Generate all phase requirements files
/generate-phase-requirements

# Generate specific phases only
/generate-phase-requirements 1 2
/generate-phase-requirements 3
/generate-phase-requirements 1 3 5

# Generate remaining phases after partial failure
/generate-phase-requirements 4 5 6
```

## Prerequisites Validation
Before executing this command, validate that:
- [ ] PROJECT_PHASE_PLAN.md exists and is complete
- [ ] PHASE_DEPENDENCY_MAP.md exists (from /plan-project-overview)
- [ ] templates/prp/TEMPLATE_PHASE_REQUIREMENTS.md exists
- [ ] Write permissions to PRP-PLANNING/ directory
- [ ] Phase numbers are valid (exist in PROJECT_PHASE_PLAN.md)

## Generation Process

### 1. Master Plan Analysis
```bash
# Read and parse PROJECT_PHASE_PLAN.md
- Extract phase breakdown summary
- Parse phase dependencies and integration points
- Load success metrics and validation criteria
- Identify API contracts and database evolution plans
```

### 2. Template Processing
```bash
# For each requested phase number:
- Copy templates/prp/TEMPLATE_PHASE_REQUIREMENTS.md
- Populate phase-specific information from master plan
- Add dependencies from previous phases
- Define integration requirements for next phases
- Include performance benchmarks and success criteria
```

### 3. Cross-Reference Integration
```bash
# Ensure proper cross-referencing between phases:
- Phase N references completion summary from Phase N-1
- Phase N defines integration points for Phase N+1
- All phases reference master project architecture
- Performance baselines cascade through phases
- Database schema evolution is properly sequenced
```

### 4. Phase-Specific Content Generation

#### Foundation Phase (Usually Phase 1)
```bash
# Foundation components with no dependencies
- Database schema and initial data models
- Core business logic and services
- Authentication and security foundation
- Basic API structure and routing
- Initial testing framework setup
```

#### Feature Phases (Middle phases)
```bash
# Feature implementation phases
- User interface components and interactions
- Business logic extensions and integrations
- API endpoints and data processing
- Real-time features and WebSocket handling
- Integration with external services
```

#### Optimization Phase (Final phase)
```bash
# Performance and production readiness
- Performance tuning and optimization
- Production deployment configuration
- Monitoring and logging systems
- Documentation finalization
- Load testing and stress testing
```

### 5. Integration Point Definition

#### API Contract Specification
```bash
# Define exact API interfaces between phases
For Phase N → Phase N+1:
- Endpoint signatures and request/response formats
- Authentication and authorization requirements
- WebSocket message formats and protocols
- Event hooks and extension points
- Error handling and circuit breaker patterns
```

#### Database Evolution Planning
```bash
# Plan schema changes between phases
- Initial schema for foundation phase
- Migration scripts for each subsequent phase
- Index optimization and performance tuning
- Backup and recovery procedures
- Data seeding and test data management
```

### 6. Performance and Success Criteria

#### Performance Benchmarks
```bash
# Phase-specific performance targets
- Response time requirements (API endpoints)
- Memory usage constraints and optimization
- Database query performance targets
- Real-time processing latency requirements
- Concurrent user support thresholds
```

#### Success Validation
```bash
# Measurable success criteria for each phase
- Functional requirement completion checklist
- Performance benchmark achievement
- Integration test passing criteria
- Security validation and penetration testing
- User acceptance testing scenarios
```

## Phase Requirements File Structure

### Generated PHASE[N]_REQUIREMENTS.md Template
```markdown
# Phase [N]: [Phase Name]

## Phase Overview
- **Phase Number**: [N]
- **Phase Name**: [Descriptive Name]
- **Dependencies**: [Previous Phase Numbers]
- **Estimated Effort**: [Time Estimate]
- **Success Criteria**: [Specific Measurable Goals]

## Business Requirements from BRD
[Phase-specific business requirements extracted from master plan]

## Technical Requirements from Architecture
[Phase-specific technical requirements and components]

## Dependencies and Prerequisites
### From Previous Phases
[Specific outputs and APIs needed from previous phases]

### Integration Points
[APIs and interfaces this phase must provide for future phases]

## Implementation Scope
### Core Components
[Primary development tasks and deliverables]

### API Specifications
[Detailed API contracts and interfaces]

### Database Changes
[Schema modifications and data migration requirements]

## Performance Requirements
[Specific performance targets and benchmarks]

## Testing Strategy
[Phase-specific testing approach and validation]

## Success Validation
[Completion criteria and acceptance tests]

## Integration Preparation
[Preparation for next phase integration points]
```

## Advanced Generation Strategies

### Incremental Processing Benefits
```bash
# Fault-tolerant generation approach
- Generate phases individually to avoid timeouts
- Retry specific phases without regenerating entire plan
- Review individual phases before generating remaining
- Debug and adjust specific phases without full regeneration
```

### Progressive Workflow Control
```bash
# Better user control and debugging
- Review master plan before detailed generation
- Generate critical phases first (foundation phases)
- Skip phases that don't need immediate attention
- Generate phases as development progresses
```

### Context Size Management
```bash
# Manage API context efficiently
- Process smaller chunks of requirements at a time
- Focus on single phase context instead of entire project
- Reduce memory usage and processing time
- Enable longer, more detailed phase requirements
```

## Quality Assurance

### Phase Requirements Validation
```bash
# Validate each generated phase file
- All master plan requirements addressed
- Dependencies properly referenced
- Integration points clearly defined
- Performance targets are specific and measurable
- Success criteria are testable
```

### Cross-Phase Consistency
```bash
# Ensure consistency across all phases
- API contracts match between provider and consumer phases
- Database evolution is logically sequenced
- Performance baselines cascade properly
- Integration points are bidirectionally defined
```

### Completeness Verification
```bash
# Verify generation completeness
- All requested phase numbers generated successfully
- No missing phase files in sequence
- All cross-references resolved correctly
- Template placeholders properly populated
```

## Error Handling and Recovery

### Common Generation Issues
```bash
# Handle typical problems gracefully
- Missing or incomplete PROJECT_PHASE_PLAN.md
- Invalid phase numbers requested
- Template file access issues
- Write permission problems
- Cross-reference resolution failures
```

### Recovery Strategies
```bash
# Fault recovery approaches
- Retry individual failed phases
- Skip problematic phases and continue with others
- Provide detailed error messages for debugging
- Suggest corrections for common issues
- Enable partial completion with manual fixes
```

## Command Execution Flow

### Step 1: Prerequisites Check
- Validate PROJECT_PHASE_PLAN.md exists and is readable
- Check requested phase numbers are valid
- Verify template files are accessible
- Confirm write permissions for output directory

### Step 2: Master Plan Processing
- Parse PROJECT_PHASE_PLAN.md for phase definitions
- Extract dependency relationships and integration points
- Load performance requirements and success criteria
- Prepare cross-reference mapping for phase generation

### Step 3: Incremental Phase Generation
- For each requested phase number:
  - Load phase-specific requirements from master plan
  - Populate template with phase details
  - Add dependencies and integration specifications
  - Include performance benchmarks and validation criteria
  - Write PHASE[N]_REQUIREMENTS.md file

### Step 4: Validation and Cross-Reference
- Validate all generated files for completeness
- Check cross-references between phases are correct
- Verify integration points are bidirectionally defined
- Confirm all success criteria are measurable

### Step 5: Output Summary
- List all successfully generated phase files
- Report any generation failures with specific error details
- Provide next steps for using generated requirements
- Suggest phase generation sequence if not all generated

## Integration with Enhanced Workflow

This command becomes **Step 0B** in the split Complex PRP workflow:

**Step 0A**: `/plan-project-overview [BRD] [ARCHITECTURE]` - Generate master planning documents  
**Step 0B**: `/generate-phase-requirements [phase_numbers]` - Generate detailed phase requirements  
**Step 1.1**: Skip manual phase planning - use generated files  
**Step 1.2**: Use generated PHASE1_REQUIREMENTS.md directly  
**Step 1.3**: Execute `/generate-prp PHASE1_REQUIREMENTS.md`  
**Step 1.4**: Execute `/update-phase-completion 1`  
**Step N.1**: Use pre-generated PHASE[N]_REQUIREMENTS.md files  

## Success Metrics

Successful phase requirements generation should achieve:
- **Complete Coverage**: All requested phases generated successfully
- **Consistent Integration**: Cross-phase references are accurate and complete
- **Actionable Content**: Each phase file contains specific, implementable requirements
- **Performance Clarity**: All performance targets are measurable and achievable
- **Fault Tolerance**: Generation failures can be recovered incrementally

The resulting phase requirements files should enable seamless execution of individual phase PRPs with full context continuity and integration compatibility.