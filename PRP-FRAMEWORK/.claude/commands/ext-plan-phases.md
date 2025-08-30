# Extension: Plan Extension Phases

## Usage: ext-plan-phases [EXTENSION_NAME] [EXTENSION_BRD_PATH]

Creates extension-specific phase breakdown and requirements files based on extension BRD and shared codebase analysis.

## Purpose

This command transforms extension business requirements into systematic development phases, leveraging the shared codebase analysis to create extension-aware phase plans that integrate seamlessly with existing code.

## Usage Examples
```bash
/ext-plan-phases AdvancedCharts PRP-EXTENSIONS/Extension_TradeAssist_AdvancedCharts/EXTENSION_BRD_AdvancedCharts.md
/ext-plan-phases MachineLearning ./EXTENSION_BRD_ML.md
/ext-plan-phases MultiUser EXTENSION_BRD_MultiUser.md
```

## Prerequisites Validation
Before executing this command, validate that:
- [ ] Extension BRD file exists and is readable
- [ ] PRP-EXTENSIONS/shared/CODEBASE_ANALYSIS.md exists (run /ext-analyze-codebase first)
- [ ] PRP-EXTENSIONS/shared/INTEGRATION_POINTS.md exists
- [ ] Extension directory structure will be created if it doesn't exist
- [ ] TEMPLATE_EXTENSION_PHASE_REQUIREMENTS.md exists in PRP-EXTENSIONS/templates/

## Planning Process

### 1. Extension Requirements Analysis
```bash
# Extract key extension elements from BRD
- Extension objectives and success criteria
- Functional requirements and features
- Integration requirements with existing system
- Technical constraints and compatibility needs
- User workflow modifications or additions
```

### 2. Codebase Integration Assessment
```bash
# Analyze how extension fits with existing system
- Reference shared codebase analysis for architecture understanding
- Map extension requirements to available integration points
- Identify existing patterns the extension should follow
- Assess compatibility requirements and constraints
```

### 3. Extension Phase Decomposition
```bash
# Break extension into logical development phases
Foundation Phase: Core extension functionality that other phases depend on
Integration Phase: Integration with existing system components
Enhancement Phase: Additional features building on foundation
Polish Phase: Optimization, testing, and documentation
```

### 4. Phase Dependency Mapping
```bash
# Create optimal phase sequence for extension
- Identify extension-specific dependencies between phases
- Map dependencies on existing system components
- Consider integration complexity and risk factors
- Plan for compatibility testing and validation
```

## Extension Directory Structure Creation

### Extension Directory Setup
```bash
# Create extension directory structure
PRP-EXTENSIONS/Extension_[ProjectName]_[ExtensionName]/
├── metadata/
│   └── EXTENSION_CONFIG.yaml
├── planning/
│   ├── EXTENSION_BRD_[ExtensionName].md (provided)
│   └── EXTENSION_PHASE_PLAN_[ExtensionName].md (generated)
├── phases/
│   ├── EXT_PHASE1_[ExtensionName]_REQUIREMENTS.md (generated)
│   ├── EXT_PHASE2_[ExtensionName]_REQUIREMENTS.md (generated)
│   └── EXT_PHASE[N]_[ExtensionName]_REQUIREMENTS.md (generated)
└── prps/
    └── (PRPs will be generated here by /ext-generate-prp)
```

## Generated Files

### Extension Phase Plan
- **EXTENSION_PHASE_PLAN_[ExtensionName].md**: Master extension plan including:
  - Extension overview and objectives
  - Phase breakdown and sequencing
  - Integration strategy with existing system
  - Success criteria and validation approach

### Extension Phase Requirements
- **EXT_PHASE[N]_[ExtensionName]_REQUIREMENTS.md**: Detailed requirements for each phase including:
  - Phase-specific objectives and deliverables
  - Integration points with existing system
  - Compatibility requirements
  - Testing and validation requirements

### Extension Configuration
- **EXTENSION_CONFIG.yaml**: Extension metadata including:
  - Extension identification and version info
  - Target project and compatibility requirements
  - Phase summary and dependencies
  - Integration point mapping

## Phase Planning Strategy

### Extension-Aware Phase Design
```markdown
Phase Planning Considerations for Extensions:
- Start with minimal integration to validate compatibility
- Build incrementally to minimize risk to existing system
- Plan compatibility testing at each phase
- Design rollback strategies for each phase

Example Extension Phase Pattern:
Phase 1: Core Extension Logic (minimal integration)
Phase 2: Basic Integration (with existing APIs/services)
Phase 3: Advanced Integration (with existing UI/workflows)
Phase 4: Enhancement and Optimization (full feature set)
```

### Integration-Driven Sequencing
```markdown
Extension Phase Sequencing Strategy:
- Foundation phases establish core functionality with minimal system impact
- Integration phases connect with existing system components systematically
- Enhancement phases add advanced features building on proven integration
- Validation phases ensure compatibility and performance standards
```

## Extension Metadata Generation

### Extension Configuration File
```yaml
extension:
  name: "[Extension Name]"
  id: "[extension_name_lowercase]"
  version: "1.0.0"
  type: "[feature_enhancement|integration|optimization]"
  target_project: "[Project Name]"
  
compatibility:
  requires_codebase_analysis_version: ">=1.0"
  
integration_points:
  backend: ["path/to/integration/point1", "path/to/integration/point2"]
  frontend: ["path/to/integration/point1", "path/to/integration/point2"]
  database: ["table_name1", "table_name2"]
  
phases:
  - name: "[Phase 1 Name]"
    complexity: "[low|medium|high]"
  - name: "[Phase 2 Name]"
    complexity: "[low|medium|high]"
```

## Quality Validation

### Planning Completeness
- [ ] All extension requirements mapped to phases
- [ ] Integration points clearly identified for each phase
- [ ] Dependencies properly sequenced
- [ ] Compatibility requirements addressed
- [ ] Success criteria defined for each phase

### Extension Integration Validation
- [ ] Extension phases align with existing system architecture
- [ ] Integration points are valid and available
- [ ] Extension follows existing system patterns
- [ ] Compatibility requirements are realistic and testable

## Command Execution Flow

### Step 1: Requirements Ingestion
- Read and parse extension BRD
- Load shared codebase analysis and integration points
- Extract extension objectives and constraints
- Map extension requirements to system capabilities

### Step 2: Phase Planning Engine
- Apply extension-aware phase breakdown algorithms
- Create integration-driven phase sequencing
- Map extension requirements to available integration points
- Generate phase dependencies and validation strategy

### Step 3: File Generation
- Create extension directory structure if needed
- Generate EXTENSION_PHASE_PLAN_[ExtensionName].md
- Create all EXT_PHASE[N]_[ExtensionName]_REQUIREMENTS.md files
- Generate EXTENSION_CONFIG.yaml metadata

### Step 4: Validation and Output
- Validate generated phase plan for completeness
- Check integration point references are valid
- Verify compatibility requirements are addressable
- Output summary of generated files and next steps

## Integration with Extension Workflow

This command creates the planning foundation for extension development:

**Prerequisite**: `/ext-analyze-codebase [TARGET_PATH]` - Shared codebase understanding
**Step 1**: `/ext-plan-phases [EXTENSION_NAME] [BRD]` - Create extension phases
**Step 2**: `/ext-generate-prp [PHASE_REQUIREMENTS]` - Generate phase PRP
**Step 3**: `/ext-execute-prp [PRP]` - Execute extension phase

## Success Metrics

Successful extension phase planning should achieve:
- **Clear Phase Breakdown**: Each phase has specific, achievable objectives
- **Integration Alignment**: Phases align with existing system architecture and patterns  
- **Risk Management**: Phases are sequenced to minimize integration risk
- **Compatibility Focus**: Each phase maintains system compatibility and follows patterns
- **Actionable Requirements**: Phase requirements are specific enough for PRP generation

The resulting extension phase plan should enable systematic, low-risk development that enhances the existing system without disrupting established functionality.