# Extension: Analyze Existing Codebase

## Usage: ext-analyze-codebase [TARGET_CODEBASE_PATH]

Analyzes an existing codebase to understand its architecture, patterns, and extension opportunities. This creates shared analysis files that all extensions can reference.

## Purpose

This command performs a comprehensive analysis of the existing codebase to create documentation that informs extension development. The analysis is shared across all extensions to ensure consistency and avoid duplication.

## Usage Examples
```bash
/ext-analyze-codebase ./src
/ext-analyze-codebase /path/to/project/src
/ext-analyze-codebase .
```

## Prerequisites Validation
Before executing this command, validate that:
- [ ] Target codebase path exists and is readable
- [ ] PRP-EXTENSIONS/shared/ directory exists
- [ ] Write permissions to PRP-EXTENSIONS/shared/ directory

## Analysis Process

### 1. Codebase Structure Analysis
```bash
# Analyze overall project structure
- Directory organization and module hierarchy
- File naming conventions and patterns
- Import/dependency patterns
- Configuration and environment setup
```

### 2. Architecture Pattern Discovery
```bash
# Identify architectural patterns in use
- MVC, MVP, or other architectural patterns
- Service layer organization
- Data access patterns
- API design patterns
- Authentication and authorization patterns
```

### 3. Technology Stack Assessment
```bash
# Document technology choices and versions
- Programming languages and versions
- Frameworks and their configurations
- Database systems and ORM patterns
- External dependencies and libraries
- Development and build tools
```

### 4. Integration Point Identification
```bash
# Find opportunities for extension
- Existing plugin/extension mechanisms
- Service interfaces that can be extended
- Database schema extension points
- API endpoints that can be enhanced
- Event systems or hooks available
```

### 5. Code Quality and Convention Analysis
```bash
# Understand existing code standards
- Coding style and formatting standards
- Testing patterns and coverage
- Error handling approaches
- Logging and monitoring patterns
- Documentation standards
```

### 6. Performance and Security Baseline
```bash
# Establish current system characteristics
- Current performance characteristics
- Security implementation patterns
- Data protection approaches
- Rate limiting and throttling patterns
```

## Generated Output Files

### Primary Analysis Document
- **PRP-EXTENSIONS/shared/CODEBASE_ANALYSIS.md**: Comprehensive codebase analysis including:
  - System architecture overview
  - Technology stack and dependencies
  - Code organization and patterns
  - Development conventions and standards
  - Performance and security considerations

### Integration Opportunities Document  
- **PRP-EXTENSIONS/shared/INTEGRATION_POINTS.md**: Specific extension opportunities including:
  - Service extension points
  - API extension opportunities
  - Database extension patterns
  - Frontend component extension points
  - Configuration extension mechanisms

## Analysis Methodology

### Code Structure Analysis
```bash
# Systematic examination of codebase
1. Map directory structure and identify major modules
2. Analyze import dependencies and coupling patterns
3. Identify service boundaries and interfaces
4. Document configuration and environment patterns
5. Map data flow and processing patterns
```

### Pattern Recognition
```bash
# Identify reusable patterns for extensions
1. Service layer patterns (how services are structured)
2. API design patterns (RESTful conventions, error handling)
3. Database interaction patterns (ORM usage, query patterns)
4. Frontend component patterns (if applicable)
5. Testing patterns and conventions
```

### Extension Opportunity Mapping
```bash
# Find safe integration points
1. Identify plugin/extension mechanisms already in place
2. Find service interfaces suitable for extension
3. Locate configuration extension points
4. Map database schema extension opportunities
5. Identify UI extension points (if applicable)
```

## Quality Checklist

### Analysis Completeness
- [ ] All major system components analyzed
- [ ] Technology stack completely documented
- [ ] Integration points clearly identified
- [ ] Code conventions and patterns documented
- [ ] Performance and security baseline established

### Documentation Quality
- [ ] Analysis is comprehensive and accurate
- [ ] Integration points are specific and actionable
- [ ] Examples provided where helpful
- [ ] Documentation is clear and well-organized

### Accuracy Validation
- [ ] All file paths and component references are correct
- [ ] Technology versions and configurations are accurate
- [ ] Integration examples are tested and valid
- [ ] Code patterns reflect actual implementation

## Command Execution Flow

### Step 1: Codebase Discovery
- Scan target directory structure recursively
- Identify major programming languages and frameworks
- Map configuration files and build systems
- Document external dependencies

### Step 2: Pattern Analysis Engine
- Analyze code organization patterns
- Identify service and component boundaries
- Map API design and data flow patterns
- Document testing and quality patterns

### Step 3: Integration Assessment
- Identify extension mechanisms and hooks
- Map service interfaces suitable for extension  
- Find configuration extension opportunities
- Document safe modification points

### Step 4: Documentation Generation
- Generate comprehensive CODEBASE_ANALYSIS.md
- Create specific INTEGRATION_POINTS.md
- Validate all documentation for accuracy
- Create usage examples where helpful

## Integration with Extension Workflow

This command creates the foundation for the extension framework:

**Step 0**: `/ext-analyze-codebase [TARGET_PATH]` - Create shared codebase understanding
**Step 1**: `/ext-plan-phases [EXTENSION_NAME] [BRD]` - Plan extension using shared analysis
**Step 2**: `/ext-generate-prp [REQUIREMENTS]` - Generate PRP with codebase context
**Step 3**: `/ext-execute-prp [PRP]` - Execute extension with full context

## Success Metrics

A successful codebase analysis should achieve:
- **Comprehensive Understanding**: Complete picture of system architecture and patterns
- **Clear Integration Points**: Specific, actionable extension opportunities identified
- **Pattern Documentation**: Existing conventions and standards clearly documented
- **Accurate References**: All file paths, APIs, and components correctly identified
- **Actionable Insights**: Analysis directly supports extension planning and development

The resulting analysis should enable confident, pattern-following extension development that integrates seamlessly with the existing codebase.