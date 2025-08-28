# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Clone and Navigate to Framework
```bash
# Clone the repository
git clone <your-repo-url>
cd Complex-PRP-Framework

# Navigate to the framework directory (contains Claude commands)
cd PRP-FRAMEWORK

# The internal structure contains three directories:
# PRP-FRAMEWORK/ (framework code - you're here)
# PRP-PLANNING/ (your project docs and generated files)
# src/ (your actual source code)
```

### Step 2: Create Your Project Documents
```bash
# Copy and customize templates for your project (run from PRP-FRAMEWORK)
cp templates/project/TEMPLATE_BRD.md ../PRP-PLANNING/PLANNING/BRD_YourProject.md
cp templates/project/TEMPLATE_ARCHITECTURE.md ../PRP-PLANNING/PLANNING/Architecture_YourProject.md
cp templates/project/TEMPLATE_CLAUDE_*.md ../PRP-PLANNING/PLANNING/

# Edit the BRD and Architecture files with your project requirements
```

### Step 3: Generate Your Phase Plan
```bash
# Run systematic phase planning (from repository root directory)
/plan-project-phases PRP-PLANNING/PLANNING/BRD_YourProject.md PRP-PLANNING/PLANNING/Architecture_YourProject.md
```

### Step 4: Execute Your First Phase
```bash
# Generate implementation PRP (from repository root directory)
/generate-prp PRP-PLANNING/PRPs/PHASE1_REQUIREMENTS.md

# Execute the phase (creates code in src/)
/execute-prp PRP-PLANNING/PRPs/[generated-prp-file].md

# Document completion and adapt future phases
/update-phase-completion 1
/update-phase-plans 1
```

## 📁 Internal Three-Directory Structure

After cloning, your repository contains three internal directories:

### **PRP-FRAMEWORK/** (Framework Code - Don't Modify)
```
PRP-FRAMEWORK/
├── templates/                 # Framework templates
├── examples/                  # Framework examples
├── tools/                     # Framework utilities
└── docs/                      # Framework documentation
```

### **PRP-PLANNING/** (Your Project Management)
```
PRP-PLANNING/
├── PLANNING/                  # YOUR PROJECT DOCS
│   ├── BRD_YourProject.md    # Your business requirements
│   ├── Architecture_YourProject.md # Your technical design
│   └── CLAUDE_*.md           # Your Claude Code guidelines
├── PRPs/                      # GENERATED FILES
│   ├── PROJECT_PHASE_PLAN.md # Generated master plan
│   ├── PHASE1_REQUIREMENTS.md     # Generated phase files
│   └── [other generated files]
└── TASK.md                    # Project task tracking
```

### **src/** (Your Actual Source Code)
```
src/
├── CLAUDE.md                  # Main project guidance (auto-copied)
├── backend/                   # YOUR BACKEND CODE
│   └── CLAUDE.md             # Backend guidance (auto-copied)
├── frontend/                  # YOUR FRONTEND CODE
│   └── CLAUDE.md             # Frontend guidance (auto-copied)
├── shared/                    # YOUR SHARED CODE
│   └── CLAUDE.md             # Shared code guidance (auto-copied)
└── tests/                     # YOUR TESTS
```

## ✅ What You Need to Do

1. **Edit PRP-PLANNING/PLANNING/ files** with your project requirements
2. **Run commands from repository root** directory as shown above
3. **Your code gets created in src/** as guided by generated PRPs
4. **Don't modify** the PRP-FRAMEWORK/ directory contents

## 🎯 Key Commands

- `/plan-project-phases BRD.md ARCH.md` - Generate optimal phase breakdown
- `/generate-prp PHASE_FILE.md` - Create implementation PRP
- `/execute-prp PRP_FILE.md` - Implement a phase
- `/update-phase-completion N` - Document completed phase
- `/update-phase-plans N` - Adapt future phases

## 🔄 Typical Workflow

```bash
# One-time setup after clone (run from repository root)
/plan-project-phases PRP-PLANNING/PLANNING/BRD_YourProject.md PRP-PLANNING/PLANNING/Architecture_YourProject.md

# Repeat for each phase (run from repository root)
/generate-prp PRP-PLANNING/PRPs/PHASE[N]_REQUIREMENTS.md
/execute-prp PRP-PLANNING/PRPs/[generated-prp].md
/update-phase-completion [N]
/update-phase-plans [N]
```

## 📚 Next Steps

- Read [FRAMEWORK_GUIDE.md](FRAMEWORK_GUIDE.md) for complete methodology
- Check [examples/](examples/) for reference implementations  
- Customize templates in PLANNING/ for your specific project

**You're ready to build complex projects systematically!** 🚀