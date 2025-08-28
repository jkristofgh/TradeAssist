# Create PRP

## Phase file: $ARGUMENTS

Generate a complete PRP for general feature implementation with thorough research. Ensure context is passed to the AI agent to enable self-validation and iterative refinement. Read the feature file first to understand what needs to be created, how the examples provided help, and any other considerations.

The AI agent only gets the context you are appending to the PRP and training data. Assuma the AI agent has access to the codebase and the same knowledge cutoff as you, so its important that your research findings are included or referenced in the PRP. The Agent has Websearch capabilities, so pass urls to documentation and examples.

## Research Process

1. **Phase Context Analysis**
   - Read ../PRP-PLANNING/PRPs/PHASE[N]_REQUIREMENTS.md to determine phase number and complexity
   - Read ../PRP-PLANNING/PRPs/PROJECT_PHASE_PLAN.md to get template assignment and project context
   - Read previous ../PRP-PLANNING/PRPs/PHASE[N-1]_COMPLETION_SUMMARY.md files (if any) for integration context
   - Analyze phase type (foundation/integration/optimization) for appropriate patterns

2. **Template Selection**
   - Extract template assignment from PROJECT_PHASE_PLAN.md for this phase
   - If no template specified, use templates/prp/prp_base.md (enhanced version)
   - Validate template exists in templates/ directory using full path templates/prp/[template_name].md or templates/planning/[template_name].md
   - If template not found, error with message: "Template not found at templates/prp/[template_name].md"
   - Note phase type and complexity for template population

3. **Codebase Analysis**
   - Search for similar features/patterns in the codebase
   - Identify files to reference in PRP
   - Note existing conventions to follow
   - Check test patterns for validation approach
   - Analyze previous phase implementations for integration patterns

4. **External Research**
   - Search for similar features/patterns online
   - Library documentation (include specific URLs)
   - Implementation examples (GitHub/StackOverflow/blogs)
   - Best practices and common pitfalls

5. **Integration Context Research** (for complex multi-phase projects)
   - Previous phase APIs and interfaces available for consumption
   - Performance baselines established in previous phases
   - Database schema evolution from previous phases
   - WebSocket endpoints and message formats available

6. **User Clarification** (if needed)
   - Specific patterns to mirror and where to find them?
   - Integration requirements and where to find them?
   - Performance targets specific to this phase?

## PRP Generation

Using assigned template from PROJECT_PHASE_PLAN.md (or prp_base.md if not specified):

### Phase Context Population (for complex multi-phase projects)
- **Project Type**: Set to complex_multi_phase if multi-phase project
- **Phase Info**: Extract phase number, total phases, phase type from planning documents
- **Previous Phases**: List completed phases and their completion summaries
- **Integration Context**: Previous phase APIs, performance baselines, database schema
- **Forward Compatibility**: Requirements for next phase preparation

### Critical Context to Include and pass to the AI agent as part of the PRP
- **Documentation**: URLs with specific sections
- **Code Examples**: Real snippets from codebase
- **Gotchas**: Library quirks, version issues
- **Patterns**: Existing approaches to follow
- **Previous Phase Context**: Completion summaries, APIs, integration points (for phases >1)
- **Performance Baselines**: Targets to maintain/improve from previous phases
- **Dependency Analysis**: Integration requirements from PHASE_DEPENDENCY_MAP.md

### Implementation Blueprint
- Start with pseudocode showing approach
- Reference real files for patterns
- Include error handling strategy
- Include integration patterns for consuming previous phases (if applicable)
- Include forward compatibility preparation for next phases (if applicable)
- list tasks to be completed to fullfill the PRP in the order they should be completed
- Include phase-appropriate validation strategy (unit/integration/performance/system)

### Phase-Appropriate Validation Gates (Must be Executable)

#### For Simple Features:
```bash
# Component Level Validation
ruff check --fix && mypy .
uv run pytest tests/unit/ -v --cov=src

# Basic Integration Testing  
uv run pytest tests/integration/ -v
```

#### For Complex Multi-Phase Projects:
```bash
# Level 1: Component Validation (Always Required)
ruff check src/ --fix && mypy src/
pytest tests/unit/ -v --cov=src --cov-report=term-missing

# Level 2: Integration Validation (Previous phase integration)
pytest tests/integration/phase_N/ -v
python scripts/validate_api_contracts.py --phase=[N-1]

# Level 3: Performance Validation (Baseline maintenance)
python scripts/performance_benchmark.py --baseline=phase_[N-1] --target-phase=[N]
python scripts/load_test.py --target-rps=[expected_throughput]

# Level 4: System Integration (End-to-end workflows)
pytest tests/e2e/workflows/ -v
pytest tests/integration/cross_phase/ -v

# Level 5: Forward Compatibility (Next phase preparation)
python scripts/validate_next_phase_interfaces.py --phase=[N+1]
python scripts/document_performance_baselines.py --phase=[N]
```

*** CRITICAL WORKFLOW STEPS ***

1. **FIRST**: Read PHASE[N]_REQUIREMENTS.md to understand what phase this is
2. **SECOND**: Read PROJECT_PHASE_PLAN.md to get template assignment and project context  
3. **THIRD**: Read previous PHASE*_COMPLETION_SUMMARY.md files for integration context
4. **FOURTH**: Research codebase patterns and external documentation
5. **FIFTH**: ULTRATHINK about the PRP - consider phase type, complexity, integration requirements
6. **SIXTH**: Populate the assigned template with comprehensive context
7. **FINAL**: Include phase-appropriate validation loops

## Output
Save as: `../PRP-PLANNING/PRPs/{generated-prp-name}.md`

## Quality Checklist
- [ ] All necessary context included
- [ ] Validation gates are executable by AI
- [ ] References existing patterns
- [ ] Clear implementation path
- [ ] Error handling documented

Score the PRP on a scale of 1-10 (confidence level to succeed in one-pass implementation using claude codes)

Remember: The goal is one-pass implementation success through comprehensive context.