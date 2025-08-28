# Getting Started with Complex PRP Framework

## Overview

The Complex PRP Framework provides a systematic approach to developing large, complex software projects using AI-assisted development with Claude Code. This guide will walk you through setting up your first project and using the framework's core features.

## Prerequisites

Before you begin, ensure you have:

- **Claude Code** installed and configured ([Installation Guide](https://docs.anthropic.com/en/docs/claude-code))
- **Git** for version control
- **Development Environment** set up for your chosen technology stack
- **Project Documentation** ready (BRD and Architecture documents)

## Step 1: Set Up the Framework

### Option A: Clone the Framework Repository

```bash
git clone <your-complex-prp-framework-repo>
cd Complex-PRP-Framework
```

### Option B: Download and Extract

Download the framework as a ZIP file and extract it to your desired location.

## Step 2: Create Your Project

### Using the Project Generator (Recommended)

```bash
# Navigate to the framework directory
cd Complex-PRP-Framework

# Generate a new project
python tools/project-generator.py --name "MyTradingPlatform" --type "trading-platform"

# Or for a web application
python tools/project-generator.py --name "MySaasApp" --type "web-application"

# Or for an e-commerce system  
python tools/project-generator.py --name "MyShop" --type "ecommerce-system"
```

This will create a new project directory alongside the framework with:
- Proper directory structure
- Template files customized for your project type
- Claude Code commands configured
- Example BRD and Architecture documents

### Manual Project Setup

If you prefer to set up manually:

1. **Create Project Directory**
   ```bash
   mkdir ../MyProject
   cd ../MyProject
   ```

2. **Copy Framework Files**
   ```bash
   # Copy Claude Code commands
   cp -r ../Complex-PRP-Framework/.claude ./
   
   # Copy template files
   mkdir PRPs
   cp -r ../Complex-PRP-Framework/templates/prp/* PRPs/
   cp -r ../Complex-PRP-Framework/templates/planning/* PRPs/
   ```

3. **Create Project Structure**
   ```bash
   mkdir -p PLANNING backend frontend shared tests docs
   ```

## Step 3: Prepare Your Project Documents

### Create Business Requirements Document (BRD)

Copy and customize the BRD template:

```bash
cp ../Complex-PRP-Framework/templates/project/TEMPLATE_BRD.md PLANNING/BRD_MyProject.md
```

Edit `PLANNING/BRD_MyProject.md` to include:
- Business objectives and success criteria
- User stories and functional requirements
- Performance and quality requirements  
- Integration and external system requirements
- Timeline and delivery constraints

### Create Architecture Document

Copy and customize the Architecture template:

```bash
cp ../Complex-PRP-Framework/templates/project/TEMPLATE_ARCHITECTURE.md PLANNING/Architecture_MyProject.md
```

Edit `PLANNING/Architecture_MyProject.md` to include:
- System components and their relationships
- Technology stack decisions
- Data flow and integration patterns
- Performance architecture and optimization
- Security and deployment requirements

### Create Claude Guidelines

Copy and customize the Claude guideline templates:

```bash
# Main project guidelines
cp ../Complex-PRP-Framework/templates/project/TEMPLATE_CLAUDE_PROJECT.md PLANNING/CLAUDE_PROJECT.md

# Backend guidelines
cp ../Complex-PRP-Framework/templates/project/TEMPLATE_CLAUDE_BACKEND.md PLANNING/CLAUDE_BACKEND.md

# Frontend guidelines  
cp ../Complex-PRP-Framework/templates/project/TEMPLATE_CLAUDE_FRONTEND.md PLANNING/CLAUDE_FRONTEND.md

# Shared code guidelines
cp ../Complex-PRP-Framework/templates/project/TEMPLATE_CLAUDE_SHARED.md PLANNING/CLAUDE_SHARED.md
```

Customize each file by replacing template variables like `{PROJECT_NAME}`, `{TECHNOLOGY_STACK}`, etc. with your project-specific values.

## Step 4: Run Systematic Phase Planning

Once your BRD and Architecture documents are ready:

```bash
# Generate optimal phase breakdown
/plan-project-phases PLANNING/BRD_MyProject.md PLANNING/Architecture_MyProject.md
```

This command will analyze your documents and create:
- **PROJECT_PHASE_PLAN.md** - Master project phase plan with dependencies
- **PHASE_DEPENDENCY_MAP.md** - Visual dependency analysis
- **PHASE1_REQUIREMENTS.md, PHASE2_REQUIREMENTS.md, etc.** - Individual phase files
- Optimal phase sequencing based on complexity analysis

### Review Generated Phase Plan

1. **Check PROJECT_PHASE_PLAN.md** for the overall strategy
2. **Review PHASE_DEPENDENCY_MAP.md** for dependency relationships
3. **Examine each PHASE[N]_REQUIREMENTS.md** file for phase-specific details
4. **Customize if needed** - you can edit the generated files before execution

## Step 5: Execute Your First Phase

### Generate Phase 1 PRP

```bash
# Generate comprehensive implementation PRP for Phase 1
/generate-prp PHASE1_REQUIREMENTS.md
```

This creates a detailed PRP file in the `PRPs/` directory with:
- Implementation requirements based on phase planning
- Integration context from previous phases (if any)
- Testing and validation requirements
- Performance targets and quality gates

### Execute Phase 1

```bash
# Execute the generated PRP
/execute-prp PRPs/[generated-phase1-prp].md
```

This command will:
- Set up the development environment
- Copy Claude guidelines to appropriate locations
- Begin implementation based on the PRP specifications
- Set up testing and validation frameworks

### Document Phase 1 Completion

After completing Phase 1 development:

```bash
# Generate automated completion summary
/update-phase-completion 1
```

This analyzes your codebase and creates:
- **PHASE1_COMPLETION_SUMMARY.md** with actual implementation details
- API endpoints and database schema documentation
- Performance metrics and benchmarks achieved
- Integration points ready for next phase

### Adapt Future Phases

```bash
# Update remaining phases based on Phase 1 learnings
/update-phase-plans 1
```

This command:
- Updates PHASE2_REQUIREMENTS.md, PHASE3_REQUIREMENTS.md, etc. with real context
- Adjusts dependenciess and scope based on actual implementation
- Creates **PHASE_ADAPTATION_LOG.md** tracking changes made
- Optimizes future phases based on development velocity

## Step 6: Continue with Remaining Phases

Repeat the cycle for each remaining phase:

```bash
# For Phase N:
/generate-prp PHASE[N]_REQUIREMENTS.md
/execute-prp PRPs/[generated-phase-prp].md
/update-phase-completion [N]
/update-phase-plans [N]
```

## Framework Commands Reference

### Core Commands

- **`/plan-project-phases BRD.md Architecture.md`** - Generate optimal phase breakdown
- **`/generate-prp PHASE[N]_REQUIREMENTS.md`** - Create implementation PRP for a phase  
- **`/execute-prp [prp-file].md`** - Execute phase implementation
- **`/update-phase-completion [N]`** - Document completed phase automatically
- **`/update-phase-plans [N]`** - Adapt future phases based on learnings

### Workflow Summary

```bash
# One-time setup
/plan-project-phases PLANNING/BRD.md PLANNING/Architecture.md

# Repeat for each phase
/generate-prp PHASE[N]_REQUIREMENTS.md
/execute-prp PRPs/[generated-prp].md  
/update-phase-completion [N]
/update-phase-plans [N]
```

## Best Practices for Success

### 1. Comprehensive Planning
- Invest time in detailed BRD and Architecture documents
- Include specific performance targets and quality requirements
- Document all external integrations and dependencies

### 2. Trust the Systematic Process
- Let the `/plan-project-phases` command guide initial planning
- Use the adaptation cycle (`/update-phase-plans`) after each phase
- Review adaptation logs to learn and improve

### 3. Maintain Context Continuity
- Always run `/update-phase-completion` after finishing a phase
- Use real implementation details, not theoretical plans
- Test all documented integration points before proceeding

### 4. Quality Assurance
- Follow the multi-level testing strategy in generated PRPs
- Maintain performance baselines established in earlier phases
- Validate all cross-phase integrations thoroughly

## Troubleshooting Common Issues

### "Command not found" errors
- Ensure Claude Code is properly installed and updated
- Check that you're in a directory with `.claude/commands/` folder

### "Template not found" errors  
- Verify template files exist in `PRPs/templates/` directory
- Check file permissions and accessibility

### Generated phases seem incorrect
- Review and enhance your BRD and Architecture documents
- Ensure documents have clear sections and requirements
- Consider manual adjustment of generated phase requirements files

### Integration issues between phases
- Verify completion summaries have detailed implementation specifics
- Test all documented APIs and integration points
- Use `/update-phase-plans` to adapt based on reality

## Next Steps

1. **Complete Your First Project** using the systematic workflow
2. **Study the Examples** in the `examples/` directory for inspiration
3. **Customize Templates** for your specific technology stack and patterns
4. **Contribute Back** - share successful patterns and improvements

## Getting Help

- **[Framework Guide](../FRAMEWORK_GUIDE.md)** - Comprehensive methodology documentation
- **[Troubleshooting Guide](troubleshooting.md)** - Solutions to common problems
- **[Best Practices](best-practices.md)** - Optimization techniques and patterns
- **[API Reference](api-reference.md)** - Complete command and template reference

Ready to transform your complex project into manageable, successful phases? Start with systematic planning and let the framework guide you to success!