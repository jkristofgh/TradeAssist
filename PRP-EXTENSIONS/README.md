# PRP Extensions Framework

## Quick Start

The Extension Framework enables systematic enhancement of existing codebases using the same methodology as the base PRP Framework.

### 5-Step Extension Workflow

1. **Analyze Codebase** (one-time): `/ext-analyze-codebase ./src`
2. **Plan Extension**: `/ext-plan-phases ExtensionName EXTENSION_BRD.md`
3. **Generate PRP**: `/ext-generate-prp EXT_PHASE1_REQUIREMENTS.md`
4. **Execute Implementation**: `/ext-execute-prp ext-extensionname-phase1.md`
5. **Document Completion**: `/ext-update-completion ExtensionName 1`

### Directory Structure

```
PRP-EXTENSIONS/
├── shared/                     # Shared codebase analysis
├── templates/                  # Extension templates
├── Extension_Project_Name/     # Per-extension workspace
└── EXTENSION_FRAMEWORK_GUIDE.md # Complete documentation
```

### Key Commands

- `/ext-analyze-codebase [PATH]` - Analyze existing codebase
- `/ext-plan-phases [NAME] [BRD]` - Plan extension phases  
- `/ext-generate-prp [REQUIREMENTS]` - Generate extension PRP
- `/ext-execute-prp [PRP]` - Execute extension
- `/ext-update-completion [NAME] [PHASE]` - Document completion

### Core Principles

- **Compatibility First**: No breaking changes to existing functionality
- **Pattern Following**: Use existing code patterns and conventions
- **Shared Analysis**: One codebase analysis benefits all extensions
- **Systematic Development**: Phase-based development with documentation

See `EXTENSION_FRAMEWORK_GUIDE.md` for complete documentation and best practices.