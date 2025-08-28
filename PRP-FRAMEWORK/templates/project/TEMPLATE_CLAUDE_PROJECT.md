# Project Development Guidelines

## 🎯 Project Overview
Guidelines for full-stack {TECHNOLOGY_STACK} projects with focus on maintainability, performance, and scalability. Integrates with Complex Multi-Phase PRP framework for systematic development of large, complex applications.

### 🔄 Project Awareness & Context
- **Always read `TASK.md`** for long-term project status and cross-session continuity
- **Always read project documentation** (BRD, Architecture docs) at the start of conversations
- **Check Complex PRP phase status** in PROJECT_PHASE_PLAN.md and completion summaries for multi-phase projects
- **Use TodoWrite tool** for current session task tracking and progress management
- **Update `TASK.md`** with completed work and next session priorities at session end
- **Follow established architecture patterns** and avoid over-engineering
- **Use {ENVIRONMENT_MANAGEMENT}** for all {PRIMARY_LANGUAGE} operations
- **Maintain consistent coding standards** across all components

### 📋 Session Management & Continuity

#### Starting a New Session
1. **Read `TASK.md`** - Understand current project state and last session's progress
2. **Read BRD and Architecture documents** - Get full project context and requirements
3. **Check Complex PRP status** - For multi-phase projects, review current phase and completion status
4. **Read relevant CLAUDE_*.md files** - Get domain-specific guidance for the work ahead
5. **Use TodoWrite** - Plan current session tasks based on TASK.md priorities

#### During Session Work
1. **Use TodoWrite tool** - Track active tasks and progress in real-time
2. **Follow established patterns** - Maintain consistency with existing codebase
3. **Document as you work** - Keep context for next phases and team members
4. **Test continuously** - Validate work against performance and quality benchmarks

#### Ending a Session
1. **Update `TASK.md`** - Record completed work, current state, and next priorities
2. **Update phase status** - For Complex PRP projects, note phase progress
3. **Document integration points** - Capture any new APIs, schemas, or patterns created
4. **Note blockers or dependencies** - Help next session start smoothly

### 🏗️ Recommended Project Structure
```
{PROJECT_NAME}/
├── {BACKEND_DIR}/        # API application and services
│   └── CLAUDE.md         # Backend guidelines (copied from PLANNING/ during execute-prp)
├── {FRONTEND_DIR}/       # Client application  
│   └── CLAUDE.md         # Frontend guidelines (copied from PLANNING/ during execute-prp)
├── {SHARED_DIR}/         # Common types and utilities
│   └── CLAUDE.md         # Shared code guidelines (copied from PLANNING/ during execute-prp)
├── tests/                # Test suites mirroring main structure
├── docs/                 # Project documentation
├── PLANNING/             # Project planning documents (AUTHORITATIVE SOURCE)
│   ├── BRD_{PROJECT_NAME}.md           # Business Requirements
│   ├── Architecture_{PROJECT_NAME}.md  # Technical Architecture
│   ├── CLAUDE_PROJECT.md               # Main guidelines (REPOSITORY VERSION)
│   ├── CLAUDE_BACKEND.md               # Backend guidelines (REPOSITORY VERSION)
│   ├── CLAUDE_FRONTEND.md              # Frontend guidelines (REPOSITORY VERSION)
│   └── CLAUDE_SHARED.md                # Shared guidelines (REPOSITORY VERSION)
├── PRPs/                 # Complex PRP framework files (for multi-phase projects)
│   ├── templates/        # Complex PRP templates
│   ├── COMPLEX_PRP_USER_GUIDE.md # Framework documentation
│   └── [Phase files]     # Generated phase planning and completion files
├── CLAUDE.md             # Main guidelines (copied from PLANNING/ during execute-prp)
├── TASK.md               # Cross-session task tracking and project state
└── {DEPENDENCIES_FILE}   # Project dependencies
```

### 📂 CLAUDE File Management Strategy

#### Repository + Copy Approach
- **PLANNING/ Directory**: Serves as the authoritative repository for all CLAUDE development guidelines
- **Automatic Distribution**: `/execute-prp` command automatically copies files to appropriate locations
- **Claude Code Discovery**: Files are placed where Claude Code expects them for automatic reading
- **Version Control**: PLANNING/ maintains master versions; working copies get updated automatically

## 🚀 Complex Multi-Phase PRP Integration

### When to Use Complex PRP Framework
Use Complex PRP for projects with:
- **Multiple Components**: Frontend, backend, database, integrations
- **Complex Architecture**: Microservices, real-time systems, distributed components  
- **Performance Requirements**: Specific latency, throughput, or reliability targets
- **Integration Points**: External APIs, third-party services, multiple data sources
- **Regulatory Requirements**: Security, compliance, audit trails
- **Scalability Needs**: Must support growth and future enhancements

### Complex PRP Systematic Workflow

#### Step 0: Project Initiation (New Projects)
```bash
# For new complex projects, start with systematic planning
/plan-project-phases PLANNING/BRD_{PROJECT_NAME}.md PLANNING/Architecture_{PROJECT_NAME}.md

# This generates:
# - PROJECT_PHASE_PLAN.md (master phase plan)
# - PHASE_DEPENDENCY_MAP.md (visual dependencies)  
# - PHASE1_REQUIREMENTS.md, PHASE2_REQUIREMENTS.md, etc. (all phase files)
# - Optimal phase sequencing based on complexity analysis
```

#### Phase Development Cycle (Repeat for Each Phase)
```bash
# 1. Generate comprehensive implementation PRP
/generate-prp PHASE[N]_REQUIREMENTS.md

# 2. Execute the phase implementation
/execute-prp PRPs/[generated-phase-prp].md

# 3. Document what was actually built (automated analysis)
/update-phase-completion [N]

# 4. Adapt future phases based on learnings (automated adaptation)
/update-phase-plans [N]

# 5. Update TASK.md with phase completion and next phase priorities
```

### 🧱 Architecture Principles
- **Separation of Concerns:** Clear boundaries between layers and components
- **Single Responsibility:** Each module/component has one clear purpose
- **Dependency Injection:** Use frameworks' built-in DI systems
- **Database Abstraction:** Use {DATABASE_ABSTRACTION} for database operations
- **API Design:** {API_STYLE} APIs with consistent naming and response formats
- **Phase Compatibility:** New phases must not break existing functionality

### 🧪 Testing Strategy

#### Multi-Level Testing for Complex Projects
- **Unit Tests:** Test individual functions and components in isolation
- **Integration Tests:** Test API endpoints and database operations
- **Cross-Phase Tests:** Validate integration between phases
- **End-to-End Tests:** Test complete user workflows across all phases
- **Performance Tests:** Benchmark critical paths and validate baselines
- **Regression Tests:** Ensure new phases don't break existing functionality

### 📋 Enhanced Development Workflow

#### For Simple Projects
1. **Check `TASK.md`** for current priorities and context
2. **Read relevant CLAUDE_*.md** files for domain-specific guidance
3. **Write tests first** for new features (TDD approach)
4. **Implement with type safety** and proper error handling
5. **Test performance** against established benchmarks
6. **Update `TASK.md`** with progress and next priorities

#### For Complex Multi-Phase Projects
1. **Check Complex PRP status** - Review current phase and completion summaries
2. **Read BRD and Architecture** documents for full project context
3. **Follow systematic workflow** - Use 5-command Complex PRP cycle
4. **Maintain context continuity** - Use previous phase completion details
5. **Validate integration points** - Test cross-phase compatibility
6. **Update phase documentation** - Keep completion summaries current
7. **Plan adaptively** - Use learnings to improve future phases

### 🔐 Security Requirements
- **Credential Storage:** Use secure secret management systems
- **Access Control:** Implement proper authentication and authorization
- **Input Validation:** Validate and sanitize all user inputs
- **Audit Trail:** Log security-relevant events and changes
- **Encrypted Communications:** Use HTTPS/TLS for all network communications
- **Phase Security:** Maintain security standards across all phases

### 🤖 AI Behavior Rules
- **Follow Project Architecture:** Respect established patterns and conventions
- **Performance Awareness:** Consider performance implications of changes
- **Security First:** Always validate inputs and handle errors gracefully
- **Test Coverage:** Ensure adequate test coverage for new code
- **Documentation:** Keep code self-documenting with clear comments
- **Phase Context:** Understand current phase and integration requirements
- **Context Continuity:** Use actual implementation details from previous phases

### ✅ Definition of Done

#### For All Projects
- [ ] Feature works in development environment
- [ ] Unit tests pass with adequate coverage
- [ ] Performance meets established benchmarks
- [ ] Integration tests pass
- [ ] Documentation updated
- [ ] Code review completed
- [ ] No breaking changes without migration plan
- [ ] `TASK.md` updated with progress and next steps

#### Additional for Complex Multi-Phase Projects
- [ ] Phase completion summary generated and accurate
- [ ] Cross-phase integration validated
- [ ] Performance baselines maintained or improved
- [ ] API contracts maintained for backward compatibility
- [ ] Integration examples provided for future phases
- [ ] Phase adaptation completed if needed
- [ ] Next phase priorities updated in planning documents

### 📚 Essential Reading

#### For All Projects
- This file (`CLAUDE_PROJECT.md`) - General development guidelines
- Relevant domain-specific files (`CLAUDE_BACKEND.md`, `CLAUDE_FRONTEND.md`, `CLAUDE_SHARED.md`)
- Project BRD and Architecture documents

#### For Complex Multi-Phase Projects
- `PRPs/COMPLEX_PRP_USER_GUIDE.md` - Complete Complex PRP methodology
- `PROJECT_PHASE_PLAN.md` - Current project phase plan and status
- Previous phase completion summaries - For integration context
- `PHASE_DEPENDENCY_MAP.md` - Understanding phase relationships

### 🎯 Success Metrics
- **Development Velocity:** Consistent delivery of phase milestones
- **Quality Standards:** Low defect rates and high test coverage
- **Performance Targets:** Meeting or exceeding established benchmarks
- **Integration Success:** Smooth transitions between phases
- **Documentation Quality:** Complete and accurate project documentation
- **Team Productivity:** Effective use of tools and frameworks
- **Context Continuity:** Seamless knowledge transfer between phases

---

## Template Customization Variables
Replace these placeholders when creating a new project:

- `{PROJECT_NAME}` - Your project name
- `{TECHNOLOGY_STACK}` - e.g., "Python/TypeScript", "Node.js/React", "Django/Vue.js"
- `{PRIMARY_LANGUAGE}` - e.g., "Python", "JavaScript", "Go"
- `{ENVIRONMENT_MANAGEMENT}` - e.g., "virtual environments", "Docker containers", "conda"
- `{BACKEND_DIR}` - Backend directory name, e.g., "backend", "server", "api"
- `{FRONTEND_DIR}` - Frontend directory name, e.g., "frontend", "client", "web"
- `{SHARED_DIR}` - Shared code directory, e.g., "shared", "common", "lib"
- `{DEPENDENCIES_FILE}` - Dependencies file, e.g., "requirements.txt", "package.json", "go.mod"
- `{DATABASE_ABSTRACTION}` - e.g., "ORMs/query builders", "SQLAlchemy", "Prisma", "GORM"
- `{API_STYLE}` - e.g., "RESTful", "GraphQL", "gRPC"