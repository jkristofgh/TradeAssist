# Extension: Generate Comprehensive Extension PRP

## Usage: ext-1-generate-prp [EXTENSION_NAME] [EXTENSION_BRD_PATH]

Generates a single comprehensive Product Requirements Prompt (PRP) for complete extension development using the extension BRD and shared codebase analysis.

## Purpose

This command creates a comprehensive, implementation-ready PRP that covers the entire extension scope. It transforms business requirements into detailed technical implementation guidance, leveraging existing system architecture and patterns to ensure seamless integration.

## Usage Examples
```bash
/ext-1-generate-prp HistoricalDataFoundation PRP-EXTENSIONS/EXT_HistoricalDataFoundation/planning/EXTENSION_BRD.md
/ext-1-generate-prp AdvancedCharts ./EXTENSION_BRD_AdvancedCharts.md
/ext-1-generate-prp MachineLearning EXTENSION_BRD_ML.md
```

## Prerequisites Validation
Before executing this command, validate that:
- [ ] Extension BRD file exists and is readable
- [ ] PRP-EXTENSIONS/shared/CODEBASE_ANALYSIS.md exists (run /ext-0-analyze-codebase first)
- [ ] PRP-EXTENSIONS/shared/INTEGRATION_POINTS.md exists
- [ ] PRP-EXTENSIONS/templates/extension_prp_base.md exists
- [ ] Extension directory structure will be created if it doesn't exist

## Comprehensive PRP Generation Process

### 1. Extension Requirements Analysis
```bash
# Extract complete extension scope from BRD
- Extension objectives and success criteria
- All functional requirements and features
- Integration requirements with existing system
- Technical constraints and compatibility needs
- User workflow modifications or additions
- Performance and scalability requirements
```

### 2. Implementation Complexity Assessment
```bash
# Analyze technical implementation requirements
- Database schema changes and data modeling
- API endpoint design and integration patterns
- Frontend component architecture and UI integration
- Service layer design and business logic
- Testing strategy and validation requirements
- Performance optimization and caching needs
```

### 3. Codebase Integration Strategy
```bash
# Create comprehensive integration plan
- Map requirements to existing system architecture
- Identify all integration points and dependencies
- Plan backward compatibility preservation
- Design error handling and monitoring integration
- Plan configuration and deployment integration
```

### 4. Complete Implementation Roadmap
```bash
# Generate full technical implementation plan
- Detailed technical architecture for entire extension
- Database design with migrations and relationships
- API design with all endpoints and data models
- Frontend architecture with all components and workflows
- Service integration with existing system components
- Testing strategy covering unit, integration, and end-to-end tests
```

## Template Context Population

### Extension-Specific Variables
```markdown
{extension_name} - Name of the extension being developed
{target_project} - Name of the target project being extended  
{extension_version} - Version of this extension (1.0.0)
{extension_type} - Type of extension (feature_enhancement|integration|optimization)
{base_project_version} - Version of the base project being extended
```

### Comprehensive Context Variables
```markdown
{codebase_analysis_summary} - Complete architectural understanding
{integration_points_summary} - All available integration opportunities
{existing_patterns} - All code patterns and conventions to follow
{complete_requirements} - Full extension requirements from BRD
{technical_architecture} - Complete technical design
{implementation_strategy} - Detailed implementation approach
{natural_phases} - Implementation phases based on technical complexity
```

## Generated Comprehensive PRP Structure

### Complete Extension PRP Content
The generated PRP includes:
- **Extension Overview**: Complete scope, objectives, and business context
- **Technical Architecture**: Complete system design and integration strategy
- **Database Design**: Full schema with all tables, relationships, and migrations
- **API Design**: All endpoints with request/response models and authentication
- **Frontend Architecture**: Complete UI components, workflows, and integration
- **Service Layer**: All business logic, external integrations, and data processing
- **Testing Strategy**: Comprehensive testing approach for all components
- **Implementation Phases**: Natural phase boundaries based on technical dependencies
- **Deployment Strategy**: Production readiness and deployment approach

### Implementation Guidance
```markdown
Generated PRP provides specific implementation guidance for:
- Complete database schema design and migration strategy
- Full API implementation with all endpoints and models
- Complete frontend component architecture and integration
- Service layer implementation with all business logic
- Integration with existing authentication, logging, and monitoring
- Comprehensive testing strategy and validation approach
- Performance optimization and caching strategy
- Documentation and maintenance approach
```

## Output File Naming and Location

### PRP File Naming Convention
```bash
# Generated comprehensive PRP follows this pattern:
extension-prp-[extension-name-lowercase]-[YYYYMMDD-HHMMSS].md

# Examples:
extension-prp-historicaldata-20241215-143022.md
extension-prp-advancedcharts-20241215-151534.md
extension-prp-machinelearning-20241215-094712.md
```

### Output Location
```bash
# Comprehensive PRP is generated in extension planning directory:
PRP-EXTENSIONS/EXT_[ExtensionName]/planning/
└── extension-prp-[extension-name]-[timestamp].md
```

## Directory Structure Creation

### Extension Directory Setup
```bash
# Create extension directory structure if needed:
PRP-EXTENSIONS/EXT_[ExtensionName]/
├── planning/
│   ├── EXTENSION_BRD.md (provided)
│   ├── extension-prp-[timestamp].md (generated)
│   └── EXTENSION_CONFIG.yaml (generated)
└── phases/
    └── (phase requirements will be extracted by /ext-2-plan-phases)
```

## Integration Context Generation

### Complete System Integration
```markdown
Generated PRP includes comprehensive context about:
- All existing APIs and extension strategies
- Complete database schema and extension approach
- All frontend components and integration patterns
- All service patterns and extension opportunities
- Complete configuration and environment integration
- All monitoring, logging, and error handling patterns
```

### Comprehensive Pattern Following
```markdown
PRP includes detailed instructions for:
- Complete code organization following existing structure
- All naming conventions matching existing patterns
- Error handling using all established approaches
- Logging and monitoring using existing infrastructure
- Testing patterns matching complete existing test structure
- Documentation patterns following existing standards
```

## Quality Assurance Integration

### Complete Compatibility Requirements
```markdown
Generated PRP includes requirements for:
- Full backward compatibility with all existing APIs
- Complete database schema compatibility and migrations
- Full UI consistency with existing design patterns
- Performance compatibility with all existing benchmarks
- Complete security compatibility with existing approaches
```

### Comprehensive Validation Strategy
```markdown
PRP includes complete validation approach:
- Unit testing for all new functionality
- Integration testing with all existing components
- Complete regression testing to ensure no breaking changes
- API contract testing for all endpoints
- End-to-end testing for all workflows
- Performance testing for all scenarios
- Security testing for all integration points
```

## Command Execution Flow

### Step 1: Complete Requirements Analysis
- Read and parse complete extension BRD
- Extract all extension requirements and objectives
- Load shared codebase analysis for complete system understanding
- Load integration points for all extension opportunities
- Analyze complete technical scope and complexity

### Step 2: Comprehensive Architecture Design
- Design complete technical architecture
- Plan all database changes and relationships
- Design all API endpoints and data models
- Plan all frontend components and workflows
- Design all service integrations and business logic

### Step 3: Implementation Planning
- Create complete implementation strategy
- Identify natural phase boundaries based on technical dependencies
- Plan integration with existing system components
- Design testing strategy for all components
- Plan deployment and production readiness

### Step 4: Comprehensive PRP Generation
- Load extension_prp_base.md template
- Populate with complete extension context and architecture
- Generate all implementation guidance and examples
- Create comprehensive testing and validation requirements
- Generate complete deployment and maintenance guidance

### Step 5: File Generation and Validation
- Create extension directory structure if needed
- Generate timestamped comprehensive PRP filename
- Write complete PRP to extension planning directory
- Generate EXTENSION_CONFIG.yaml with metadata
- Validate generated PRP for completeness and accuracy

## Integration with Extension Workflow

This command creates the comprehensive foundation for extension development:

**Prerequisites**: `/ext-0-analyze-codebase [TARGET_PATH]` - One-time codebase understanding
**Current Step**: `/ext-1-generate-prp [EXTENSION_NAME] [BRD]` - Generate comprehensive PRP
**Next Step**: `/ext-2-plan-phases [PRP_PATH]` - Extract natural phase boundaries

## Success Metrics

Successful comprehensive extension PRP generation should produce:
- **Complete Implementation Plan**: Covers entire extension scope with technical detail
- **Architecture-Driven Design**: Based on existing system architecture and patterns
- **Integration-Ready Guidance**: Specific integration strategies for all system components
- **Phase-Discovery Ready**: Contains enough technical detail to identify natural phases
- **Implementation-Complete**: Provides all guidance needed for complete extension development

The resulting comprehensive PRP serves as the single source of truth for extension development, containing all technical architecture, implementation guidance, and integration strategies needed to build the complete extension.