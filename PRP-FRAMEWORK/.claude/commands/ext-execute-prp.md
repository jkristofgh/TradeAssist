# Extension: Execute Extension PRP

## Usage: ext-execute-prp [EXTENSION_PRP_PATH]

Executes an extension PRP with full codebase context, using existing project CLAUDE guidelines and extension-specific requirements.

## Purpose

This command implements extension functionality using the generated extension PRP. It leverages existing project development guidelines while incorporating extension-specific context and compatibility requirements.

## Usage Examples
```bash
/ext-execute-prp PRP-EXTENSIONS/Extension_TradeAssist_AdvancedCharts/prps/ext-advancedcharts-phase1-20241215-143022.md
/ext-execute-prp ext-machinelearning-phase2-20241215-151534.md
/ext-execute-prp ./ext-multiuser-phase1-20241215-094712.md
```

## Prerequisites Validation
Before executing this command, validate that:
- [ ] Extension PRP file exists and is readable
- [ ] PRP-PLANNING/PLANNING/CLAUDE_PROJECT.md exists
- [ ] PRP-PLANNING/PLANNING/CLAUDE_BACKEND.md exists (if backend changes)
- [ ] PRP-PLANNING/PLANNING/CLAUDE_FRONTEND.md exists (if frontend changes)
- [ ] Existing project codebase is accessible and in working state
- [ ] Development environment is set up for the target project

## Execution Process

### 1. Extension PRP Context Loading
```bash
# Load extension-specific context
- Read and understand extension PRP requirements
- Extract extension name, phase, and specific objectives
- Load codebase analysis and integration context
- Understand compatibility requirements and constraints
- Identify existing patterns to follow for this extension
```

### 2. Project CLAUDE Guidelines Integration
```bash
# Use existing project development guidelines
- Copy PRP-PLANNING/PLANNING/CLAUDE_PROJECT.md → ./CLAUDE.md
- Copy PRP-PLANNING/PLANNING/CLAUDE_BACKEND.md → ./src/backend/CLAUDE.md (if backend/ exists)
- Copy PRP-PLANNING/PLANNING/CLAUDE_FRONTEND.md → ./src/frontend/CLAUDE.md (if frontend/ exists)
- Apply project-specific development patterns and conventions
- Follow established code quality and testing standards
```

### 3. Extension-Aware Implementation
```bash
# Implement extension with full context
- Follow existing project patterns and conventions
- Integrate with existing system components as specified
- Maintain backward compatibility with existing APIs
- Implement comprehensive testing including regression tests
- Document changes following existing documentation patterns
```

### 4. Compatibility Validation
```bash
# Ensure extension maintains system integrity
- Run existing project test suite to ensure no breaking changes
- Validate integration with existing components
- Test backward compatibility of any modified APIs
- Verify performance impact is within acceptable limits
- Confirm security patterns and standards are maintained
```

## Extension Implementation Strategy

### Compatibility-First Development
```markdown
Extension implementation follows compatibility-first principles:
- All existing functionality must continue to work unchanged
- New functionality integrates seamlessly with existing workflows
- API changes are additive only (no breaking changes)
- Database changes use migrations that preserve existing data
- UI changes maintain existing design patterns and usability
```

### Pattern-Following Implementation
```markdown
Extension development follows established project patterns:
- Code organization matches existing project structure
- Naming conventions follow established patterns
- Error handling uses existing error handling infrastructure
- Logging and monitoring integrate with existing systems
- Configuration follows existing configuration patterns
```

### Integration-Aware Development
```markdown
Extension integrates thoughtfully with existing system:
- Uses existing authentication and authorization systems
- Leverages existing database connections and patterns
- Integrates with existing API structure and versioning
- Uses established frontend component and state patterns
- Follows existing deployment and operational patterns
```

## Testing and Validation Strategy

### Multi-Level Testing Approach
```markdown
Extension testing includes multiple validation levels:

Level 1: Extension Functionality Testing
- Unit tests for all new extension functionality
- Integration tests for extension-specific features
- Edge case testing for extension-specific scenarios

Level 2: System Integration Testing
- Integration tests between extension and existing components
- API compatibility tests for any modified endpoints
- Database integration tests for schema changes
- Frontend integration tests for UI components

Level 3: Regression Testing
- Full existing project test suite execution
- Backward compatibility validation
- Performance regression testing
- Security and error handling validation

Level 4: End-to-End Workflow Testing
- Complete user workflows including extension functionality
- Cross-component functionality validation
- Real-world usage scenario testing
```

### Validation Checkpoints
```markdown
Throughout implementation, validate:
- [ ] Extension functionality works as specified
- [ ] All existing functionality remains intact
- [ ] No breaking changes introduced to APIs or workflows
- [ ] Performance impact is within acceptable limits
- [ ] Code follows established patterns and conventions
- [ ] Documentation is updated appropriately
```

## Development Guidelines Application

### Existing Project Guidelines
The execution uses existing project CLAUDE guidelines for:
- Code structure and organization standards
- Testing patterns and coverage requirements
- Documentation standards and practices
- Performance and security requirements
- Deployment and operational considerations

### Extension-Specific Guidelines
Additional extension-specific guidelines include:
- Compatibility requirements and constraints
- Integration patterns and examples
- Extension-specific testing requirements
- Rollback and recovery considerations
- Extension versioning and update strategies

## Quality Assurance and Validation

### Pre-Implementation Validation
```bash
# Before starting implementation
- [ ] Understanding of extension requirements confirmed
- [ ] Integration points validated and accessible
- [ ] Existing system patterns and conventions understood
- [ ] Development environment prepared and tested
```

### Development Validation
```bash
# During implementation
- [ ] Code follows existing project patterns consistently
- [ ] Integration with existing components working correctly
- [ ] No breaking changes introduced to existing functionality
- [ ] All tests passing (new extension tests + existing project tests)
- [ ] Performance impact measured and acceptable
```

### Post-Implementation Validation
```bash
# After implementation completion
- [ ] All extension functionality working as specified
- [ ] Complete system integration validated
- [ ] Comprehensive test suite passing
- [ ] Documentation updated and accurate
- [ ] Extension ready for completion summary
```

## Command Execution Flow

### Step 1: Context Preparation
- Load extension PRP and understand requirements
- Set up project CLAUDE guidelines in appropriate locations
- Validate development environment and existing codebase state
- Prepare compatibility testing framework

### Step 2: Extension Implementation
- Implement extension functionality following PRP requirements
- Integrate with existing system using established patterns
- Maintain backward compatibility throughout development
- Add comprehensive testing at all levels

### Step 3: Validation and Testing
- Execute comprehensive test suite including regression tests
- Validate integration with existing system components
- Confirm performance and security standards maintained
- Test complete workflows including extension functionality

### Step 4: Completion Preparation
- Document implementation results and integration points
- Prepare completion summary with specific implementation details
- Validate that extension is ready for production use
- Prepare next phase integration points (if applicable)

## Integration with Extension Workflow

This command implements the planned extension:

**Prerequisites**:
- `/ext-analyze-codebase [TARGET_PATH]` - Codebase understanding
- `/ext-plan-phases [EXTENSION_NAME] [BRD]` - Extension phases planned
- `/ext-generate-prp [PHASE_REQUIREMENTS]` - Implementation PRP generated

**Current Step**: `/ext-execute-prp [GENERATED_PRP]` - Implement the extension
**Next Step**: `/ext-update-completion [EXTENSION_NAME] [PHASE]` - Document implementation

## Success Metrics

Successful extension execution should achieve:
- **Functional Success**: All extension requirements implemented and working
- **Integration Success**: Seamless integration with existing system components
- **Compatibility Success**: No breaking changes to existing functionality
- **Quality Success**: Code meets established quality and testing standards
- **Performance Success**: Extension performs within acceptable parameters

The completed extension should enhance the existing system capabilities while maintaining all existing functionality, performance characteristics, and operational standards.