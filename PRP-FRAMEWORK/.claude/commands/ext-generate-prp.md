# Extension: Generate Extension PRP

## Usage: ext-generate-prp [EXTENSION_PHASE_REQUIREMENTS_PATH]

Generates a comprehensive Product Requirements Prompt (PRP) for extension development using the extension-specific PRP template and codebase context.

## Purpose

This command creates extension-aware PRPs that understand both the extension requirements and the existing codebase context. It uses the shared codebase analysis to ensure extensions follow existing patterns and integrate seamlessly.

## Usage Examples
```bash
/ext-generate-prp PRP-EXTENSIONS/Extension_TradeAssist_AdvancedCharts/phases/EXT_PHASE1_AdvancedCharts_REQUIREMENTS.md
/ext-generate-prp EXT_PHASE2_MachineLearning_REQUIREMENTS.md
/ext-generate-prp ./EXT_PHASE1_MultiUser_REQUIREMENTS.md
```

## Prerequisites Validation
Before executing this command, validate that:
- [ ] Extension phase requirements file exists and is readable
- [ ] PRP-EXTENSIONS/shared/CODEBASE_ANALYSIS.md exists
- [ ] PRP-EXTENSIONS/shared/INTEGRATION_POINTS.md exists
- [ ] PRP-EXTENSIONS/templates/extension_prp_base.md exists
- [ ] Extension directory structure exists (created by /ext-plan-phases)

## PRP Generation Process

### 1. Extension Context Loading
```bash
# Load extension-specific context
- Read extension phase requirements file
- Extract extension name, phase number, and objectives
- Load shared codebase analysis for system understanding
- Load integration points for extension opportunities
- Determine existing patterns to follow
```

### 2. Codebase Context Integration
```bash
# Integrate existing system context into PRP
- Include relevant architecture patterns from codebase analysis
- Reference specific integration points for this extension
- Include existing code conventions and standards
- Add compatibility requirements and constraints
- Reference existing APIs, services, and components
```

### 3. Extension PRP Customization
```bash
# Customize PRP template for specific extension
- Populate extension_prp_base.md with extension details
- Include specific integration requirements
- Add existing system references and examples
- Include compatibility testing requirements
- Add extension-specific validation criteria
```

### 4. Integration Example Generation
```bash
# Create concrete examples for extension development
- Generate API integration examples using existing patterns
- Create database integration examples following existing schema
- Include frontend integration examples using existing components
- Add configuration examples following existing patterns
```

## Template Context Population

### Extension-Specific Variables
```markdown
{extension_name} - Name of the extension being developed
{target_project} - Name of the target project being extended
{phase_number} - Current phase number (1, 2, 3, etc.)
{phase_name} - Descriptive name of the current phase
{base_project_version} - Version of the base project being extended
```

### Codebase Context Variables
```markdown
{codebase_analysis_summary} - Key findings from codebase analysis
{integration_points_summary} - Available integration opportunities
{existing_patterns} - Code patterns and conventions to follow
{extension_requirements} - Specific requirements for this extension phase
{implementation_plan} - Detailed implementation strategy
{success_criteria} - Specific success criteria for this phase
```

## Generated PRP Structure

### Extension PRP Content
The generated PRP includes:
- **Extension Context**: Name, phase, target project information
- **Existing System Understanding**: Architecture, patterns, integration points
- **Extension Requirements**: Specific functionality to be implemented
- **Implementation Strategy**: How to integrate with existing system
- **Code Guidelines**: Existing patterns and conventions to follow
- **Validation Strategy**: How to ensure compatibility and quality

### Extension-Specific Guidelines
```markdown
Generated PRP includes specific guidance on:
- Following existing code organization and patterns
- Using established libraries and frameworks
- Maintaining API compatibility and contracts
- Implementing proper error handling using existing patterns
- Adding comprehensive testing including regression tests
- Documenting changes following existing documentation standards
```

## Output File Naming

### PRP File Naming Convention
```bash
# Generated PRP files follow this pattern:
ext-[extension-name-lowercase]-phase[N]-[timestamp].md

# Examples:
ext-advancedcharts-phase1-20241215-143022.md
ext-machinelearning-phase2-20241215-151534.md
ext-multiuser-phase1-20241215-094712.md
```

### Output Location
```bash
# PRPs are generated in extension-specific directory:
PRP-EXTENSIONS/Extension_[ProjectName]_[ExtensionName]/prps/
└── ext-[extension-name]-phase[N]-[timestamp].md
```

## Integration Context Generation

### Existing System Integration
```markdown
Generated PRP includes specific context about:
- Existing APIs and how to extend them
- Database schema and how to add extension tables/columns
- Frontend components and how to integrate extension UI
- Service patterns and how to add extension services
- Configuration patterns and how to add extension settings
```

### Pattern Following Guidance
```markdown
PRP includes specific instructions for:
- Code organization following existing structure
- Naming conventions matching existing patterns
- Error handling using established approaches
- Logging and monitoring using existing infrastructure
- Testing patterns matching existing test structure
```

## Quality Assurance Integration

### Compatibility Requirements
```markdown
Generated PRP includes requirements for:
- Backward compatibility with existing APIs
- Database schema compatibility and migration
- UI consistency with existing design patterns
- Performance compatibility with existing benchmarks
- Security compatibility with existing approaches
```

### Validation Requirements
```markdown
PRP includes specific validation steps:
- Unit testing for all new functionality
- Integration testing with existing components
- Regression testing to ensure no breaking changes
- API contract testing for any modified endpoints
- End-to-end testing for complete workflows
```

## Command Execution Flow

### Step 1: Context Assembly
- Load extension phase requirements
- Load shared codebase analysis and integration points
- Extract extension-specific information
- Prepare template variable substitutions

### Step 2: PRP Generation
- Load extension_prp_base.md template
- Substitute extension and codebase context variables
- Generate integration examples and patterns
- Create implementation strategy based on existing patterns

### Step 3: File Generation
- Generate timestamped PRP filename
- Write PRP to extension-specific prps/ directory
- Validate generated PRP for completeness
- Output PRP file path and next steps

### Step 4: Validation and Output
- Verify all required sections are populated
- Check that all integration references are valid
- Ensure compatibility requirements are addressed
- Provide summary of generated PRP and usage instructions

## Integration with Extension Workflow

This command creates implementation-ready PRPs:

**Prerequisites**: 
- `/ext-analyze-codebase [TARGET_PATH]` - Codebase understanding
- `/ext-plan-phases [EXTENSION_NAME] [BRD]` - Extension phases created

**Current Step**: `/ext-generate-prp [PHASE_REQUIREMENTS]` - Generate implementation PRP
**Next Step**: `/ext-execute-prp [GENERATED_PRP]` - Execute the extension implementation

## Success Metrics

Successful extension PRP generation should produce:
- **Context-Rich PRP**: Includes both extension requirements and existing system context
- **Pattern-Aware Guidelines**: Specific guidance for following existing code patterns
- **Integration-Ready**: Concrete examples and strategies for system integration
- **Quality-Focused**: Comprehensive testing and validation requirements
- **Actionable Implementation**: Clear, specific implementation guidance for developers

The resulting PRP should enable seamless extension development that enhances the existing system while maintaining compatibility, performance, and code quality standards.