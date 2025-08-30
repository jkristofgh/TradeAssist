# Extension PRP Template Base

## Extension Context
- **Extension Name**: {extension_name}
- **Target Project**: {target_project}
- **Phase**: {phase_number} - {phase_name}
- **Base Project Version**: {base_project_version}

## Existing System Understanding
### Current Architecture (from CODEBASE_ANALYSIS.md)
{codebase_analysis_summary}

### Available Integration Points (from INTEGRATION_POINTS.md)
{integration_points_summary}

### Existing Patterns to Follow
{existing_patterns}

## Extension Requirements
{extension_requirements}

## Implementation Strategy
### Backward Compatibility Approach
- Ensure no breaking changes to existing APIs
- Follow established code patterns and conventions
- Maintain existing database schema integrity
- Preserve existing user workflows

### Integration Approach
- Leverage existing service patterns
- Use established authentication and authorization
- Follow existing error handling patterns
- Maintain existing logging and monitoring patterns

### Testing Strategy
- Unit tests for all new functionality
- Integration tests with existing components
- Regression tests to ensure existing functionality intact
- API contract tests for any modified endpoints

## Code Guidelines
### Follow Existing Project Patterns
- Use the same code structure and organization as the base project
- Follow established naming conventions
- Use existing libraries and frameworks where possible
- Maintain consistency with existing API design

### Extension-Specific Guidelines
- Clearly separate extension code from base project code where possible
- Use dependency injection for loose coupling
- Implement proper error handling with existing patterns
- Add comprehensive logging using existing logging infrastructure

## Validation and Quality Assurance
### Pre-Implementation Validation
- [ ] Understanding of existing system architecture confirmed
- [ ] Integration points identified and validated
- [ ] Compatibility requirements understood
- [ ] Existing patterns and conventions reviewed

### Development Validation
- [ ] Code follows existing project patterns
- [ ] Integration with existing components working
- [ ] No breaking changes introduced
- [ ] All tests passing (new and existing)

### Post-Implementation Validation
- [ ] All extension functionality working as specified
- [ ] Existing system functionality remains intact
- [ ] Performance impact assessed and acceptable
- [ ] Documentation updated appropriately

## Extension Implementation Plan
{implementation_plan}

## Success Criteria
{success_criteria}

## Completion Checklist
- [ ] All extension functionality implemented according to requirements
- [ ] Integration with existing system validated
- [ ] All tests passing (unit, integration, regression)
- [ ] Code follows established patterns and conventions
- [ ] API documentation updated (if applicable)
- [ ] No breaking changes to existing functionality
- [ ] Extension completion summary documented
- [ ] Next phase integration points prepared (if applicable)