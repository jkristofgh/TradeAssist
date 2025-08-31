# Extension Framework Guide

## Overview
The Extension Framework enables systematic enhancement of existing codebases using the same rigorous planning and execution methodology as the base PRP Framework. It provides a structured approach to extending projects while maintaining compatibility and following established patterns.

## Framework Philosophy
- **Compatibility First**: Extensions must not break existing functionality
- **Pattern Following**: Extensions follow existing code patterns and conventions
- **Systematic Development**: Use the same phase-based approach as original project development
- **Shared Understanding**: All extensions benefit from shared codebase analysis
- **Minimal Overhead**: Lightweight process focused on essential activities

## Extension Framework Structure

```
PRP-EXTENSIONS/
├── shared/                                    # Shared across all extensions
│   ├── CODEBASE_ANALYSIS.md                   # System architecture and patterns
│   └── INTEGRATION_POINTS.md                  # Available extension opportunities
├── templates/                                 # Extension templates
│   ├── TEMPLATE_EXTENSION_BRD.md
│   ├── TEMPLATE_EXTENSION_PHASE_REQUIREMENTS.md
│   ├── TEMPLATE_EXTENSION_PHASE_COMPLETION.md
│   └── extension_prp_base.md
└── EXT_[ExtensionName]/                        # Per-extension workspace
    ├── planning/
    │   ├── EXTENSION_BRD.md
    │   ├── EXTENSION_PHASE_PLAN.md
    │   └── extension-prp-[extension-name]-[timestamp].md
    ├── phases/
    │   ├── PHASE[N]_REQUIREMENTS.md
    │   └── EXT_PHASE[N]_[ExtensionName]_COMPLETION.md
    └── metadata/
        └── EXTENSION_CONFIG.yaml
```

## Extension Commands

### Core Extension Commands
- **`/ext-0-analyze-codebase [TARGET_CODEBASE_PATH]`** - One-time codebase analysis (shared)
- **`/ext-1-generate-prp [EXTENSION_NAME] [EXTENSION_BRD_PATH]`** - Generate comprehensive extension PRP
- **`/ext-2-plan-phases [COMPREHENSIVE_PRP_PATH]`** - Extract natural phase boundaries from PRP
- **`/ext-3-execute-prp [COMPREHENSIVE_PRP_PATH] --phase [PHASE_NUMBER]`** - Execute specific phase
- **`/ext-4-update-completion [EXTENSION_NAME] [PHASE_NUMBER]`** - Document completion

## Extension Development Workflow

### Step 1: One-Time Codebase Analysis
```bash
# Analyze existing codebase (run once, benefits all extensions)
/ext-0-analyze-codebase ./src

# Creates:
# - PRP-EXTENSIONS/shared/CODEBASE_ANALYSIS.md
# - PRP-EXTENSIONS/shared/INTEGRATION_POINTS.md
```

### Step 2: Generate Comprehensive PRP
```bash
# Generate single comprehensive PRP from BRD
/ext-1-generate-prp AdvancedCharts PRP-EXTENSIONS/EXT_AdvancedCharts/planning/EXTENSION_BRD.md

# Creates:
# - PRP-EXTENSIONS/EXT_AdvancedCharts/planning/extension-prp-advancedcharts-[timestamp].md
```

### Step 3: Extract Phase Boundaries
```bash
# Extract natural phase boundaries from comprehensive PRP
/ext-2-plan-phases PRP-EXTENSIONS/EXT_AdvancedCharts/planning/extension-prp-advancedcharts-[timestamp].md

# Creates:
# - PRP-EXTENSIONS/EXT_AdvancedCharts/planning/EXTENSION_PHASE_PLAN.md
# - PRP-EXTENSIONS/EXT_AdvancedCharts/phases/PHASE1_REQUIREMENTS.md
# - PRP-EXTENSIONS/EXT_AdvancedCharts/phases/PHASE2_REQUIREMENTS.md
# - etc.
```

### Step 4: Execute Phases (Per Phase)
```bash
# Execute specific phase using comprehensive PRP and phase requirements
/ext-3-execute-prp PRP-EXTENSIONS/EXT_AdvancedCharts/planning/extension-prp-advancedcharts-[timestamp].md --phase 1

# Document what was built for the phase
/ext-4-update-completion AdvancedCharts 1
```

## Key Design Principles

### 1. Compatibility First
- Extensions must not break existing functionality
- All existing APIs and workflows must continue to work unchanged
- Changes should be additive, not destructive
- Comprehensive regression testing is required

### 2. Pattern Following
- Extensions follow existing code organization and structure
- Use established libraries, frameworks, and conventions
- Maintain consistency with existing error handling and logging
- Follow existing testing and documentation patterns

### 3. Shared Understanding
- Single codebase analysis shared by all extensions
- Consistent understanding of system architecture across extensions
- Reuse of integration patterns and opportunities
- Cross-extension awareness and coordination

### 4. Systematic Development
- Same rigorous phase-based approach as original project
- Clear requirements, implementation, and completion documentation
- Context continuity between phases
- Quality assurance and validation at each phase

## Extension Types

### Feature Enhancement Extensions
- Add new functionality to existing components
- Enhance existing user workflows
- Extend existing APIs with new capabilities
- Examples: Advanced Charts, Machine Learning Predictions

### Integration Extensions
- Connect with external systems and services
- Add new notification channels
- Integrate with third-party APIs
- Examples: Discord Bot, Telegram Notifications

### Optimization Extensions
- Improve performance of existing functionality
- Add caching and optimization layers
- Enhance monitoring and observability
- Examples: Performance Dashboard, Advanced Monitoring

## Extension Best Practices

### Planning Phase
1. **Start with Shared Analysis**: Always run `/ext-0-analyze-codebase` first
2. **Clear Extension BRD**: Define specific objectives and success criteria
3. **Single Comprehensive PRP**: Generate one complete PRP covering entire extension scope
4. **Implementation-Driven Phases**: Extract natural phase boundaries based on technical complexity
5. **Compatibility Requirements**: Define backward compatibility requirements upfront

### Development Phase
1. **Follow Existing Patterns**: Use the same code structure and conventions
2. **Additive Changes Only**: Don't modify existing APIs or workflows
3. **Comprehensive Context**: Use single PRP for complete understanding while executing focused phases
4. **Comprehensive Testing**: Include regression testing for existing functionality
5. **Documentation**: Follow existing documentation standards

### Quality Assurance
1. **Regression Testing**: Verify existing functionality remains intact
2. **Integration Testing**: Test integration with existing components
3. **Performance Validation**: Ensure extension doesn't degrade performance
4. **Security Review**: Maintain existing security standards

## Template Usage

### Extension BRD Template
Use `TEMPLATE_EXTENSION_BRD.md` to define:
- Extension objectives and success criteria
- Functional requirements and user workflows
- Integration requirements with existing system
- Compatibility and constraint requirements

### Extension Phase Requirements Template
Use `TEMPLATE_EXTENSION_PHASE_REQUIREMENTS.md` to define:
- Phase-specific objectives and deliverables
- Integration points with existing system
- Implementation requirements for backend/frontend
- Testing and validation requirements

### Extension Completion Template
Use `TEMPLATE_EXTENSION_PHASE_COMPLETION.md` to document:
- What was actually implemented
- How extension integrates with existing system
- Testing results and validation outcomes
- Context for next phase development

## Common Extension Patterns

### API Extension Pattern
```markdown
1. Analyze existing API structure and patterns
2. Add new endpoints following existing conventions
3. Extend existing endpoints with optional parameters
4. Maintain backward compatibility with existing clients
5. Update API documentation following existing format
```

### Database Extension Pattern
```markdown
1. Analyze existing database schema and patterns
2. Create migration scripts for new tables/columns
3. Follow existing naming conventions and relationships
4. Ensure existing queries continue to work
5. Add indexes and constraints following existing patterns
```

### Frontend Extension Pattern
```markdown
1. Analyze existing component structure and patterns
2. Create new components following existing conventions
3. Integrate with existing state management
4. Follow existing styling and UX patterns
5. Maintain existing navigation and workflow patterns
```

## Troubleshooting Common Issues

### Extension Planning Issues
- **Problem**: Extension requirements don't align with existing architecture
- **Solution**: Review shared codebase analysis and adjust requirements to fit existing patterns

### Integration Issues
- **Problem**: Extension breaks existing functionality
- **Solution**: Review integration points and ensure changes are additive only

### Compatibility Issues
- **Problem**: Extension requires breaking changes
- **Solution**: Redesign extension to use existing interfaces or create parallel interfaces

### Pattern Mismatch Issues
- **Problem**: Extension code doesn't follow existing patterns
- **Solution**: Review codebase analysis and update implementation to match existing conventions

## Extension Success Criteria

### Functional Success
- [ ] All extension functionality works as specified
- [ ] Extension integrates seamlessly with existing workflows
- [ ] User experience is consistent with existing application

### Technical Success
- [ ] No breaking changes to existing functionality
- [ ] Code follows established patterns and conventions
- [ ] Performance impact is within acceptable limits
- [ ] Security standards are maintained

### Process Success
- [ ] Extension follows systematic development process
- [ ] Documentation is complete and accurate
- [ ] Testing includes both functionality and regression validation
- [ ] Extension can be maintained using existing processes

## Getting Started

1. **Understand the Base Project**: Familiarize yourself with the existing codebase and patterns
2. **Run Codebase Analysis**: Execute `/ext-0-analyze-codebase [TARGET_PATH]` to understand integration opportunities
3. **Define Extension Requirements**: Create clear Extension BRD defining what you want to build
4. **Generate Comprehensive PRP**: Use `/ext-1-generate-prp` to create complete technical architecture
5. **Extract Phase Boundaries**: Use `/ext-2-plan-phases` to discover natural implementation phases
6. **Execute Phase by Phase**: Use `/ext-3-execute-prp` for focused phase implementation
7. **Document Progress**: Use `/ext-4-update-completion` to track and prepare for next phases
8. **Validate Thoroughly**: Ensure compatibility and quality at each step

The Extension Framework enables you to enhance existing projects systematically while maintaining the quality, compatibility, and maintainability that made the original project successful.