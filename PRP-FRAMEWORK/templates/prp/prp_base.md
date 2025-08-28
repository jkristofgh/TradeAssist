name: "Enhanced PRP Template v3 - Complex Multi-Phase Aware"
description: |

## Purpose
Template optimized for both simple features and complex multi-phase implementations with phase-aware validation, system-level integration, and performance focus. Scales from single components to entire system phases.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Phase Awareness**: Adapt validation and requirements based on project complexity
3. **Validation Loops**: Multi-level testing from unit to system integration
4. **Information Dense**: Use keywords and patterns from the codebase
5. **Progressive Success**: Start simple, validate, then enhance
6. **Global rules**: Be sure to follow all rules in CLAUDE.md
7. **Integration Focus**: Ensure seamless integration with previous/next phases

---

## Project Context (Auto-populated by generate-prp)
```yaml
PROJECT_TYPE: [simple_feature | complex_multi_phase]
PHASE_INFO:
  number: [N]
  total_phases: [X] 
  phase_type: [foundation | integration | optimization]
  previous_phases: [list of completed phases]
  template_source: PROJECT_PHASE_PLAN.md
  complexity_level: [low | medium | high]
```

## Goal
[What needs to be built - be specific about the end state and desires]

### For Complex Multi-Phase Projects:
- [System-level objectives and architecture goals]
- [Performance targets and scalability requirements]
- [Integration requirements with other phases]
- [Long-term maintainability and extensibility goals]

## Why
- [Business value and user impact]
- [Integration with existing features]
- [Problems this solves and for whom]
- [Strategic importance in overall system architecture]

## What
[User-visible behavior and technical requirements]

### Success Criteria
- [ ] [Specific measurable outcomes]
- [ ] [Performance benchmarks (for complex projects)]
- [ ] [Integration validation (for complex projects)]
- [ ] [Forward compatibility requirements (for complex projects)]

## All Needed Context

### Previous Phase Integration (for complex multi-phase projects)
```yaml
# Integration context from previous phases
previous_phase_outputs:
  - phase: [N-1]
    completion_summary: PRPs/PHASE[N-1]_COMPLETION_SUMMARY.md
    apis_available:
      - endpoint: [API endpoint from previous phase]
        usage: [How this phase will consume it]
        example: [Working request/response example]
    websocket_available:
      - endpoint: [WebSocket endpoint]
        message_format: [Expected message structure]
      
performance_baselines:
  - metric: response_time
    current: [X]ms
    target: [maintain or improve]
  - metric: throughput  
    current: [Y] req/sec
    target: [maintain or improve]
  - metric: memory_usage
    current: [Z]MB
    growth_limit: [acceptable % increase]

integration_points_ready:
  - database_schema: [Tables and relationships available]
  - event_system: [Events available to subscribe to]
  - configuration: [Config values and interfaces available]
```

### Documentation & References (list all context needed to implement the feature)
```yaml
# MUST READ - Include these in your context window
- url: [Official API docs URL]
  why: [Specific sections/methods you'll need]
  
- file: [path/to/example.py]
  why: [Pattern to follow, gotchas to avoid]
  
- doc: [Library documentation URL] 
  section: [Specific section about common pitfalls]
  critical: [Key insight that prevents common errors]

- docfile: [PRPs/ai_docs/file.md]
  why: [docs that the user has pasted in to the project]

# For complex projects - additional context
- completion_summary: PRPs/PHASE[N-1]_COMPLETION_SUMMARY.md
  why: [Understanding what was built in previous phases]
- phase_plan: PRPs/PROJECT_PHASE_PLAN.md
  why: [Understanding overall project architecture and phase dependencies]
- dependency_map: PRPs/PHASE_DEPENDENCY_MAP.md
  why: [Understanding integration requirements and critical paths]
```

### Current Codebase tree (run `tree` in the root of the project) to get an overview of the codebase
```bash

```

### Desired Codebase tree with files to be added and responsibility of file
```bash

```

### Known Gotchas of our codebase & Library Quirks
```python
# CRITICAL: [Library name] requires [specific setup]
# Example: FastAPI requires async functions for endpoints
# Example: This ORM doesn't support batch inserts over 1000 records
# Example: We use pydantic v2 and  
```

## Implementation Blueprint

### System Architecture (for complex multi-phase projects)
```yaml
component_relationships:
  - component: [ComponentA]
    depends_on: [ComponentB from Phase N-1]
    provides: [Interface for Phase N+1]
    integration_pattern: [API calls | WebSocket | Event-driven]
    
data_flow:
  - source: [External API / Previous Phase Component]
    processing: [Business logic transformation]
    destination: [Database / WebSocket / Next Phase Interface]
    performance_target: [Processing time limit]

performance_critical_paths:
  - path: [User request → Business logic → Response]
    target: [<Xms end-to-end]
    optimization_strategy: [Specific approach to achieve target]
    monitoring: [Metrics to track for this path]
```

### Phase-Specific Architecture Patterns
```yaml
# FOUNDATION_PHASE (Phase 1 patterns):
FOUNDATION_PHASE:
  focus:
    - external_integrations: [APIs, services to integrate]
    - database_design: [Schema, indexing strategy, performance optimization]
    - performance_targets: [Specific benchmarks to establish]
    - interfaces_to_expose: [APIs and WebSocket endpoints for next phases]
  validation_priority:
    - external_api_integration: [Connection stability, error handling]
    - database_performance: [Query optimization, indexing effectiveness]
    - baseline_establishment: [Performance metrics to measure and document]

# INTEGRATION_PHASE (Phase 2+ patterns):
INTEGRATION_PHASE:
  focus:
    - previous_phase_consumption: [How to consume Phase N-1 outputs effectively]
    - cross_component_testing: [Integration test strategy between phases]
    - backward_compatibility: [Maintain existing functionality while adding new]
    - forward_interfaces: [Prepare APIs and interfaces for Phase N+1]
  validation_priority:
    - integration_testing: [Verify seamless connection with previous phases]
    - performance_maintenance: [Ensure no degradation from previous phases]
    - api_contract_compliance: [Validate all interfaces work as documented]

# OPTIMIZATION_PHASE (Final phase patterns):
OPTIMIZATION_PHASE:
  focus:
    - performance_improvements: [System-wide optimizations and tuning]
    - production_readiness: [Deployment, monitoring, scaling strategies]
    - final_integration_validation: [End-to-end system testing]
    - operational_excellence: [Logging, monitoring, alerting, backup strategies]
  validation_priority:
    - system_performance: [End-to-end performance validation]
    - production_deployment: [Deployment process and rollback procedures]
    - monitoring_and_alerting: [Comprehensive system observability]
```

### Data models and structure

Create the core data models, ensuring type safety and consistency.
```python
# Examples for different phase types:
# FOUNDATION_PHASE:
#  - External API response models
#  - Database ORM models
#  - Core business logic models
#  - WebSocket message models

# INTEGRATION_PHASE:
#  - API request/response models for consuming previous phases
#  - UI state management models (for frontend phases)
#  - Integration event models
#  - Cross-component data transfer models

# OPTIMIZATION_PHASE:
#  - Monitoring and metrics models
#  - Configuration and deployment models
#  - Performance optimization models
```

### list of tasks to be completed to fullfill the PRP in the order they should be completed

```yaml
Task 1:
MODIFY src/existing_module.py:
  - FIND pattern: "class OldImplementation"
  - INJECT after line containing "def __init__"
  - PRESERVE existing method signatures

CREATE src/new_feature.py:
  - MIRROR pattern from: src/similar_feature.py
  - MODIFY class name and core logic
  - KEEP error handling pattern identical

...(...)

Task N:
...

```


### Per task pseudocode as needed added to each task
```python

# Task 1
# Pseudocode with CRITICAL details dont write entire code
async def new_feature(param: str) -> Result:
    # PATTERN: Always validate input first (see src/validators.py)
    validated = validate_input(param)  # raises ValidationError
    
    # GOTCHA: This library requires connection pooling
    async with get_connection() as conn:  # see src/db/pool.py
        # PATTERN: Use existing retry decorator
        @retry(attempts=3, backoff=exponential)
        async def _inner():
            # CRITICAL: API returns 429 if >10 req/sec
            await rate_limiter.acquire()
            return await external_api.call(validated)
        
        result = await _inner()
    
    # PATTERN: Standardized response format
    return format_response(result)  # see src/utils/responses.py
```

### Integration Points
```yaml
DATABASE:
  - migration: "Add column 'feature_enabled' to users table"
  - index: "CREATE INDEX idx_feature_lookup ON users(feature_id)"
  
CONFIG:
  - add to: config/settings.py
  - pattern: "FEATURE_TIMEOUT = int(os.getenv('FEATURE_TIMEOUT', '30'))"
  
ROUTES:
  - add to: src/api/routes.py  
  - pattern: "router.include_router(feature_router, prefix='/feature')"
```

## Validation Loop (Phase-Aware Multi-Level Testing)

### Level 1: Component Validation (Always Required)
```bash
# Run these FIRST - fix any errors before proceeding
ruff check src/ --fix                # Auto-fix what's possible
mypy src/                           # Type checking
pytest tests/unit/ -v --cov=src --cov-report=term-missing  # Unit tests with coverage

# Expected: No errors, >90% coverage. If errors, READ the error and fix.
```

### Level 2: Integration Validation (Complex Multi-Phase Projects)
```bash
# Test integration with previous phases (if any)
pytest tests/integration/phase_N/ -v

# Validate API contracts against previous phases
python scripts/validate_api_contracts.py --phase=[N-1]

# Test WebSocket message handling (if applicable)
python scripts/test_websocket_integration.py

# Database integration and performance
python scripts/test_database_integration.py --performance-check
```

### Level 3: Performance Validation (Complex Multi-Phase Projects)  
```bash
# Performance regression testing against previous phase baselines
python scripts/performance_benchmark.py --baseline=phase_[N-1] --target-phase=[N]

# Load testing (if applicable to this phase)
python scripts/load_test.py --target-rps=[expected_throughput] --duration=60s

# Memory usage validation (no leaks, acceptable growth)
python scripts/memory_profile.py --max-growth=[acceptable_%_increase]

# Response time validation for critical paths
python scripts/response_time_test.py --target=[<Xms] --critical-paths
```

### Level 4: System Integration (Complex Multi-Phase Projects)
```bash
# End-to-end workflow testing across all implemented phases
pytest tests/e2e/workflows/ -v

# Cross-phase integration testing
pytest tests/integration/cross_phase/ -v

# Production simulation testing
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Error handling and recovery testing
python scripts/test_error_scenarios.py --simulate-failures
```

### Level 5: Forward Compatibility (Complex Multi-Phase Projects - Non-Final Phases)
```bash
# Validate interfaces ready for next phase consumption
python scripts/validate_next_phase_interfaces.py --phase=[N+1]

# Generate API documentation for next phase integration
python scripts/generate_api_docs.py --phase=[N] --format=next-phase-integration

# Create integration examples and usage patterns for next phase
python scripts/create_integration_examples.py --target-phase=[N+1]

# Validate performance baselines are documented for next phase
python scripts/document_performance_baselines.py --phase=[N]
```

### Level 2: Unit Tests each new feature/file/function use existing test patterns
```python
# CREATE test_new_feature.py with these test cases:
def test_happy_path():
    """Basic functionality works"""
    result = new_feature("valid_input")
    assert result.status == "success"

def test_validation_error():
    """Invalid input raises ValidationError"""
    with pytest.raises(ValidationError):
        new_feature("")

def test_external_api_timeout():
    """Handles timeouts gracefully"""
    with mock.patch('external_api.call', side_effect=TimeoutError):
        result = new_feature("valid")
        assert result.status == "error"
        assert "timeout" in result.message
```

```bash
# Run and iterate until passing:
uv run pytest test_new_feature.py -v
# If failing: Read error, understand root cause, fix code, re-run (never mock to pass)
```

### Level 3: Integration Test
```bash
# Start the service
uv run python -m src.main --dev

# Test the endpoint
curl -X POST http://localhost:8000/feature \
  -H "Content-Type: application/json" \
  -d '{"param": "test_value"}'

# Expected: {"status": "success", "data": {...}}
# If error: Check logs at logs/app.log for stack trace
```

## Final Validation Checklist (Phase-Aware)

### Component Level (Always Required)
- [ ] All unit tests pass: `pytest tests/unit/ -v`
- [ ] No linting errors: `ruff check src/`
- [ ] No type errors: `mypy src/`
- [ ] Code coverage >90%: Check coverage report
- [ ] Error cases handled gracefully
- [ ] Logs are informative but not verbose
- [ ] Documentation updated if needed

### Integration Level (Complex Multi-Phase Projects)
- [ ] Integration tests pass: `pytest tests/integration/ -v`
- [ ] API contracts validated: `python scripts/validate_api_contracts.py`
- [ ] WebSocket connections tested: `python scripts/test_websocket.py`
- [ ] Database operations optimized: Query performance <50ms average
- [ ] Previous phase integration verified: All consumption points tested
- [ ] Cross-component data flow validated: End-to-end data consistency

### Performance Level (Complex Multi-Phase Projects)
- [ ] Performance targets met: Response time <[target]ms for critical paths
- [ ] No performance regression: Baseline comparison shows improvement or maintenance
- [ ] Memory usage within limits: Growth <[acceptable]% from previous phase
- [ ] Load testing passed: Handles [target] concurrent users/requests
- [ ] Performance monitoring implemented: Key metrics tracked and alerting configured
- [ ] Bottleneck analysis complete: Critical paths identified and optimized

### System Level (Complex Multi-Phase Projects)
- [ ] End-to-end workflows tested: All user scenarios work seamlessly
- [ ] Cross-phase integration tested: Data flows correctly between all phases
- [ ] Error handling validated: System degrades gracefully under failure conditions
- [ ] Monitoring and observability implemented: Comprehensive system health tracking
- [ ] Security validation complete: Input validation, authentication, authorization tested
- [ ] Production simulation passed: System behaves correctly under realistic conditions

### Forward Compatibility (Complex Multi-Phase Projects - Non-Final Phases)
- [ ] Next phase interfaces ready: APIs documented, tested, and stable
- [ ] Integration examples created: Next phase has working usage examples
- [ ] Performance baselines documented: Next phase has clear performance targets
- [ ] Handoff documentation complete: Comprehensive context for next phase development
- [ ] API versioning implemented: Backward compatibility ensured for future phases
- [ ] Extension points identified: Clear places where next phase can integrate

### Production Readiness (Final Phase / Optimization Phase)
- [ ] Deployment process validated: Automated deployment works correctly
- [ ] Rollback procedures tested: Can safely revert to previous version
- [ ] Monitoring and alerting comprehensive: All critical metrics monitored
- [ ] Backup and recovery procedures tested: Data protection and disaster recovery
- [ ] Security hardening complete: Production security requirements met
- [ ] Performance optimization complete: System meets all production performance targets

---

## Anti-Patterns to Avoid
- ❌ Don't create new patterns when existing ones work
- ❌ Don't skip validation because "it should work"  
- ❌ Don't ignore failing tests - fix them
- ❌ Don't use sync functions in async context
- ❌ Don't hardcode values that should be config
- ❌ Don't catch all exceptions - be specific