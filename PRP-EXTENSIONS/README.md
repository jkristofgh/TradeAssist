# PRP Extensions Framework

## Quick Start

The Extension Framework enables systematic enhancement of existing codebases using the same methodology as the base PRP Framework.

### 5-Step Extension Workflow

1. **Analyze Codebase** (one-time): `/ext-0-analyze-codebase ./src`
2. **Generate Comprehensive PRP**: `/ext-1-generate-prp ExtensionName EXTENSION_BRD.md`
3. **Extract Phase Boundaries**: `/ext-2-plan-phases extension-prp-[timestamp].md`
4. **Execute Phase**: `/ext-3-execute-prp extension-prp-[timestamp].md --phase 1`
5. **Document Completion**: `/ext-4-update-completion ExtensionName 1`

### Directory Structure

```
PRP-EXTENSIONS/
├── shared/                     # Shared codebase analysis
├── templates/                  # Extension templates
├── EXT_ExtensionName/         # Per-extension workspace
└── EXTENSION_FRAMEWORK_GUIDE.md # Complete documentation
```

### Key Commands

- `/ext-0-analyze-codebase [PATH]` - Analyze existing codebase
- `/ext-1-generate-prp [NAME] [BRD]` - Generate comprehensive extension PRP
- `/ext-2-plan-phases [PRP_PATH]` - Extract natural phase boundaries from PRP
- `/ext-3-execute-prp [PRP_PATH] --phase [N]` - Execute specific phase
- `/ext-4-update-completion [NAME] [PHASE]` - Document completion

### Core Principles

- **Compatibility First**: No breaking changes to existing functionality
- **Pattern Following**: Use existing code patterns and conventions
- **Shared Analysis**: One codebase analysis benefits all extensions
- **Single Comprehensive PRP**: Complete technical architecture guides implementation
- **Implementation-Driven Phases**: Natural phase boundaries based on technical complexity
- **Systematic Development**: Phase-based development with documentation

See `EXTENSION_FRAMEWORK_GUIDE.md` for complete documentation and best practices.