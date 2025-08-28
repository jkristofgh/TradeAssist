# Update Phase Plans

## Usage: update-phase-plans [PHASE_NUMBER]

Dynamically adapt future phase plans based on actual implementation learnings from completed phases. This command analyzes completion summaries to update remaining phase requirements files with real integration points, performance baselines, and adjusted requirements.

## Purpose

This command enables adaptive phase planning by:
- Analyzing actual vs planned implementation from completion summaries
- Identifying integration points that differed from original plans
- Updating future phase requirements based on real implementation details
- Adjusting scope and dependencies of remaining phases
- Maintaining context continuity with accurate, up-to-date information

## Usage Examples
```bash
/update-phase-plans 1  # Update plans after completing Phase 1
/update-phase-plans 2  # Update plans after completing Phase 2  
/update-phase-plans 3  # Update plans after completing Phase 3
```

## Prerequisites Validation
Before executing this command, validate that:
- [ ] ../PRP-PLANNING/PRPs/PHASE[N]_COMPLETION_SUMMARY.md exists for the specified phase
- [ ] templates/prp/TEMPLATE_PHASE_REQUIREMENTS.md exists for template updates
- [ ] Future phase ../PRP-PLANNING/PRPs/PHASE[N+1]_REQUIREMENTS.md files exist to be updated
- [ ] ../PRP-PLANNING/PRPs/PROJECT_PHASE_PLAN.md exists and is writable

## Analysis & Adaptation Process

### 1. Completion Summary Analysis

#### Extract Actual Implementation Details
```bash
# Analyze PHASE[N]_COMPLETION_SUMMARY.md for real implementation
Actual Components Built:
- File structures and their actual purposes
- API endpoints with real request/response formats
- Database schema as actually implemented
- Performance metrics actually achieved
- Integration patterns actually used

Deviations from Plan:
- Components that were different than planned
- APIs that changed during implementation
- Performance that differed from targets
- Integration points that evolved during development
```

#### Integration Reality Check
```bash
# Compare planned vs actual integration points
Planned Integration Points:
- What was planned in original INITIAL_PHASE[N].md
- Expected API contracts and formats
- Anticipated performance characteristics
- Planned database schema evolution

Actual Integration Points:
- What was actually built and how it works
- Real API signatures and response formats
- Actual performance characteristics achieved
- Real database schema implemented
```

### 2. Impact Assessment on Future Phases

#### Dependency Impact Analysis
```bash
# Analyze how actual implementation affects future phases
Direct Dependencies:
- Which future phases directly depend on completed phase
- How changes affect their planned implementation
- What integration points need updating

Indirect Dependencies:
- Which phases are indirectly affected
- How architectural changes propagate
- What performance assumptions need updating
```

#### Scope Adjustment Analysis
```bash
# Determine if future phase scope needs adjustment
Scope Expansion Needed:
- Additional integration work required
- New requirements discovered during implementation
- Performance optimization needs identified

Scope Reduction Opportunities:
- Features completed as planned
- Integration simpler than anticipated
- Components that can be combined
```

### 3. Performance Baseline Updates

#### Real Performance Metrics
```bash
# Update future phases with actual performance baselines
Achieved Baselines:
- Response times actually measured
- Throughput actually achieved
- Memory usage patterns observed
- Database performance characteristics

Updated Targets:
- Realistic performance targets for future phases
- Updated optimization priorities
- Revised performance testing strategies
```

#### Performance Impact Chain
```bash
# Track how performance affects subsequent phases
Performance Chain Analysis:
- How Phase N performance affects Phase N+1 requirements
- What performance optimizations are now needed
- Which phases need performance testing updates
- What monitoring needs to be added
```

### 4. Integration Point Evolution

#### API Contract Updates
```bash
# Update future phases with actual API contracts
Real API Signatures:
- Actual endpoint paths and methods
- Real request/response formats with examples
- Actual authentication patterns
- Real error handling approaches

Updated Integration Patterns:
- How future phases should integrate with real APIs
- Updated usage examples and patterns
- Real WebSocket message formats
- Actual event handling patterns
```

#### Database Schema Evolution
```bash
# Update database evolution plans based on reality
Actual Schema:
- Tables and columns actually implemented
- Indexes and constraints actually created
- Performance characteristics actually achieved
- Migration patterns actually used

Updated Evolution Plan:
- How schema should evolve in future phases
- What migration strategies work best
- Performance optimization opportunities identified
- Data integrity patterns to maintain
```

### 5. Phase Requirements File Updates

#### Update Future Phase Files
```bash
# Update INITIAL_PHASE[N+1], INITIAL_PHASE[N+2], etc.
Previous Phase Context Section:
- Replace planned details with actual implementation
- Update with real file paths and component names
- Include actual API endpoints and usage examples
- Reference real performance metrics achieved

Integration Requirements Section:
- Update with actual integration points available
- Include real API signatures and examples
- Update with actual database schema evolution
- Include real performance baselines to maintain

Technical Specifications Section:
- Update based on actual technology stack used
- Include actual performance characteristics
- Update with real error handling patterns
- Include actual deployment and configuration patterns
```

#### Maintain Context Continuity
```bash
# Ensure seamless context transfer to future phases
Updated Context Elements:
- Specific file paths and their actual purposes
- Real class names and method signatures
- Actual API usage examples that work
- Real database query patterns and performance
- Actual configuration and deployment patterns
```

### 6. Project Plan Synchronization

#### Update Master Phase Plan
```bash
# Synchronize PROJECT_PHASE_PLAN.md with reality
Plan Updates:
- Update completed phase summary with actual results
- Adjust future phase scope based on lessons learned
- Update dependency map with real integration patterns
- Revise scope based on actual development progress

```

#### Update Dependency Map
```bash
# Synchronize PHASE_DEPENDENCY_MAP.md with actual dependencies
Dependency Updates:
- Update with actual integration patterns discovered
- Adjust dependency strengths based on real implementation
- Add new dependencies discovered during development
- Remove dependencies that weren't actually needed
```

### 7. Adaptation Strategies by Project Type

#### High-Performance Applications (Trading, Real-time)
```bash
# Adaptation focus for performance-critical systems
Performance Learning Integration:
- Update all future phases with actual performance patterns
- Adjust optimization phases based on real bottlenecks
- Update monitoring and alerting based on actual needs
- Revise load testing strategies based on real usage patterns
```

#### Integration-Heavy Applications (SaaS, E-commerce)
```bash
# Adaptation focus for integration-heavy systems
Integration Learning Integration:
- Update all integration phases with real API patterns
- Adjust error handling based on actual failure modes
- Update security implementations based on real requirements
- Revise testing strategies based on actual integration complexity
```

#### User Interface Applications (Dashboards, Tools)
```bash
# Adaptation focus for UI-heavy systems
UX Learning Integration:
- Update frontend phases with actual component patterns
- Adjust state management based on real data flow
- Update responsive design based on actual usage
- Revise testing strategies based on actual user workflows
```

### 8. Quality Assurance & Validation

#### Adaptation Quality Checks
```bash
# Ensure high-quality phase plan updates
Context Continuity Validation:
- Verify all updated integration points actually exist
- Test that API examples actually work
- Confirm performance baselines are realistic
- Validate that database evolution plans are feasible

Scope Adjustment Validation:
- Ensure scope changes maintain project objectives
- Verify scope adjustments are appropriate
- Validate that dependencies are still accurate
```

#### Future Phase Preparation
```bash
# Prepare future phases for seamless execution
Integration Readiness:
- Verify all integration examples are executable
- Confirm all API endpoints are properly documented
- Validate all database evolution scripts work
- Test all performance monitoring is in place

Documentation Quality:
- Ensure all file paths and names are accurate
- Verify all code examples are current and working
- Confirm all configuration examples are complete
- Validate all troubleshooting guidance is relevant
```

## Advanced Adaptation Patterns

### Progressive Learning Integration
```bash
# Compound learning across multiple phases
Phase 1 → Phase 2 Adaptation:
- Basic integration patterns learned
- Initial performance characteristics understood
- Core architecture patterns established

Phase 2 → Phase 3 Adaptation:
- UI/UX patterns established and refined
- End-to-end workflow patterns confirmed
- Cross-component integration patterns validated

Phase 3 → Phase 4 Adaptation:
- Production patterns and requirements clear
- Optimization opportunities well understood
- Monitoring and operational patterns established
```


### Performance Learning Integration
```bash
# Compound performance learning across phases
Performance Pattern Evolution:
- Bottlenecks actually encountered vs predicted
- Optimization strategies that proved effective
- Monitoring approaches that provided value
- Load patterns that matched or differed from expectations
```

## Output Files Modified

### Updated Files
- **PHASE[N+1]_REQUIREMENTS.md**: Next phase updated with actual context
- **PHASE[N+2]_REQUIREMENTS.md**: Subsequent phases updated as needed
- **PROJECT_PHASE_PLAN.md**: Master plan synchronized with reality
- **PHASE_DEPENDENCY_MAP.md**: Dependency map updated with actual patterns

### New Files Created
- **PHASE_ADAPTATION_LOG.md**: Log of all adaptations made and reasoning
- **INTEGRATION_LESSONS_LEARNED.md**: Key integration insights for future reference
- **PERFORMANCE_EVOLUTION_LOG.md**: Track performance learning across phases

## Integration with Complex PRP Workflow

This command enhances the existing workflow:

**Enhanced Workflow:**
- **Step 0**: `/plan-project-phases [BRD] [ARCHITECTURE]` - Initial systematic planning
- **Step 1.4**: `/update-phase-completion 1` - Document Phase 1 completion
- **Step 1.5**: `/update-phase-plans 1` - **NEW** - Adapt future plans based on Phase 1 reality
- **Step N.5**: `/update-phase-completion [N]` - Document Phase N completion  
- **Step N.6**: `/update-phase-plans [N]` - **NEW** - Adapt remaining plans based on Phase N reality

## Success Metrics

A successful phase plan adaptation should achieve:
- **Accurate Context**: All future phases have complete, accurate context from completed phases
- **Realistic Integration**: All integration examples and patterns actually work
- **Performance Alignment**: All performance targets are based on actual measurements
- **Scope Optimization**: Phase scope adjusted based on real development velocity
- **Quality Continuity**: All adaptations maintain or improve overall project quality

This adaptive approach transforms Complex PRP from a static planning methodology into a dynamic, learning system that continuously improves based on actual implementation experience.