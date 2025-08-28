# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Complex PRP Framework is a comprehensive system for AI-assisted development of complex, multi-phase software projects. It transforms large software projects into manageable phases with systematic planning, context continuity, and quality assurance.

## Core Architecture

### Framework Structure
```
Complex-PRP-Framework/
├── .claude/commands/           # Claude Code commands for framework operations
├── templates/                  # Core framework templates
│   ├── project/               # Project structure templates (CLAUDE guidelines, BRD, Architecture)
│   ├── prp/                   # PRP generation templates (prp_base.md, phase templates)
│   └── planning/              # Planning and tracking templates (phase plans, dependency maps)
├── examples/                  # Complete project examples (trading, SaaS, ecommerce)
├── use-cases/                 # Specialized framework variations (MCP server, Pydantic AI, web apps)
├── tools/                     # Framework utilities (project-generator.py)
└── docs/                      # Comprehensive documentation
```

### Key Components
- **Systematic Planning Engine**: Analyzes BRD and Architecture documents to generate optimal phase breakdown
- **Template System**: Adaptive templates that scale based on project complexity
- **Context Continuity**: Automated completion summaries and phase adaptation
- **Quality Assurance**: Multi-level validation and performance tracking

## Development Commands

### Framework Operations
```bash
# Create new project using framework
python tools/project-generator.py --name ProjectName --type web-application

# Core workflow commands (available in generated projects)
/plan-project-phases BRD.md Architecture.md    # Generate optimal phase plan
/generate-prp PHASE[N]_REQUIREMENTS.md               # Create implementation PRP
/execute-prp [generated-prp].md                 # Execute phase implementation
/update-phase-completion [N]                    # Document completed phase
/update-phase-plans [N]                         # Adapt future phases
```

### Project Types Supported
- **web-application**: Full-stack web development (FastAPI + React + TypeScript)
- **trading-platform**: Real-time trading systems (FastAPI + SQLite + React)
- **saas-application**: Multi-tenant SaaS (Django + Vue.js + TypeScript)
- **ecommerce-system**: E-commerce platforms (Express.js + React + MongoDB)
- **microservices**: Distributed architectures (Spring Boot + Angular + PostgreSQL)

## Template System

### Template Hierarchy
1. **prp_base.md**: Enhanced base template with phase awareness and multi-level validation
2. **Project Templates**: CLAUDE guidelines, BRD, and Architecture templates
3. **Planning Templates**: Phase plans, dependency maps, adaptation logs
4. **Completion Templates**: Automated documentation of implemented phases

### Template Customization
Templates automatically adapt based on:
- **Project Type**: Different tech stacks and architectural patterns
- **Phase Type**: Foundation, integration, or optimization phases
- **Complexity Level**: Scales validation and testing requirements
- **Previous Context**: Integration points and performance baselines from completed phases

## Systematic Planning Methodology

### BRD/Architecture Integration
The framework analyzes business requirements and technical architecture to create optimal development phases:
- **Business Requirements**: Performance targets, user workflows, integration needs
- **Technical Architecture**: Component relationships, technology stack, deployment strategy
- **Dependency Analysis**: Systematic mapping of phase dependencies and integration points

### Phase Adaptation
Each completed phase provides learnings that automatically adapt future phases:
- **Performance Baselines**: Real measurements replace theoretical targets
- **Integration Reality**: Actual API contracts and usage patterns
- **Development Progress**: Scope adjustments based on actual implementation
- **Scope Evolution**: Requirements changes based on implementation discoveries

## Quality Standards

### Multi-Level Validation
1. **Component Level**: Unit tests, linting, type checking (>90% coverage)
2. **Integration Level**: Cross-component testing, API contract validation
3. **Performance Level**: Load testing, memory profiling, response time validation
4. **System Level**: End-to-end workflows, production simulation testing

### Performance Tracking
Standardized performance reporting format across all phases:
- Response times with actual vs target measurements
- Memory usage and resource consumption patterns
- Database query performance and optimization
- System throughput under realistic conditions

## Best Practices

### Framework Usage
- Always start with systematic planning using `/plan-project-phases`
- Use the complete adaptation cycle after each phase completion
- Trust the automated completion documentation process
- Validate all generated integration examples before proceeding

### Template Development
- Preserve template structure when customizing for specific projects
- Maintain automation hooks and formatting markers for command compatibility
- Test customized templates with generation and execution commands
- Document template modifications for team consistency

### Context Continuity
- Use specific file paths, class names, and method signatures in documentation
- Include executable code examples and API usage patterns
- Document real performance metrics achieved, not theoretical targets
- Test all integration points before documenting them

## Architecture Patterns

### Single Process Applications (Trading Platforms)
- Ultra-light architecture with FastAPI + SQLite
- Real-time WebSocket systems for market data
- Sub-second processing requirements with performance monitoring
- Sequential phase development for reduced integration complexity

### Multi-Component Systems (SaaS Applications)
- Service-oriented architecture with clear boundaries
- Database-per-service patterns with eventual consistency
- API-first design with comprehensive contract testing
- Parallel development phases with integration validation

### Microservices Architectures
- Domain-driven design with service boundaries
- Event-driven communication patterns
- Service discovery and configuration management
- Container-based deployment with orchestration

## Error Handling

### Common Issues
- **Template not found**: Verify templates exist in correct directory structure
- **Phase planning fails**: Check BRD/Architecture document format and completeness
- **Integration problems**: Validate completion summaries have detailed implementation specifics
- **Performance regression**: Use baseline comparison and continuous monitoring

### Troubleshooting Strategy
1. Validate prerequisites (documents, templates, permissions)
2. Check template file locations and accessibility
3. Verify completion summaries contain accurate implementation details
4. Test integration points manually before documenting
5. Use adaptation logs to understand and resolve systematic issues

## Success Metrics

### Framework Effectiveness
- **Context Continuity**: Each phase understands previous implementation completely
- **Integration Success**: Zero integration failures between phases
- **Performance Achievement**: All performance targets met or exceeded
- **Documentation Quality**: Complete, accurate, and executable documentation

### Project Outcomes
- **Requirement Fulfillment**: All BRD requirements delivered
- **Architecture Compliance**: Technical design properly implemented
- **Quality Assurance**: Comprehensive testing at all levels
- **Maintainability**: Clear documentation and operational procedures