# Complex PRP Framework

A comprehensive framework for AI-assisted development of complex, multi-phase software projects using Claude Code and systematic planning methodologies.

## 🎯 What is Complex PRP Framework?

The Complex Multi-Phase Product Requirements Prompt (PRP) framework transforms large, complex software projects into manageable, systematic development phases with full context continuity and quality assurance.

### Key Benefits

- **🧠 Systematic Planning**: AI-driven analysis of BRD and Architecture documents to generate optimal phase breakdown
- **🔗 Context Continuity**: Each phase understands exactly what was built previously through automated completion summaries
- **⚡ Dynamic Adaptation**: Future phases automatically adapt based on learnings from completed phases
- **📊 Quality Assurance**: Built-in testing and validation at every development stage
- **📈 Scalability**: Handles projects from medium to enterprise complexity

## 🚀 Quick Start

### Prerequisites
- [Claude Code](https://claude.ai/code) installed and configured
- Git for version control

### 1. Clone and Setup Internal Three-Directory Structure

```bash
# Clone the framework repository
git clone <your-complex-prp-framework-repo>
cd Complex-PRP-Framework

# Create your project planning documents (from PRP-FRAMEWORK)
cd PRP-FRAMEWORK
cp templates/project/TEMPLATE_BRD.md ../PRP-PLANNING/PLANNING/BRD_YourProject.md
cp templates/project/TEMPLATE_ARCHITECTURE.md ../PRP-PLANNING/PLANNING/Architecture_YourProject.md
cp templates/project/TEMPLATE_CLAUDE_*.md ../PRP-PLANNING/PLANNING/

# Edit these files with your actual project requirements
```

### 2. Generate Your Phase Plan

```bash
# Run systematic phase planning from your documents (run from PRP-FRAMEWORK directory)
/plan-project-phases ../PRP-PLANNING/PLANNING/BRD_YourProject.md ../PRP-PLANNING/PLANNING/Architecture_YourProject.md

# This creates:
# ✅ ../PRP-PLANNING/PRPs/PROJECT_PHASE_PLAN.md - Master phase plan with dependencies
# ✅ ../PRP-PLANNING/PRPs/PHASE_DEPENDENCY_MAP.md - Visual dependency analysis  
# ✅ ../PRP-PLANNING/PRPs/PHASE1_REQUIREMENTS.md, PHASE2_REQUIREMENTS.md, etc. - All phase files
# ✅ Optimal sequencing based on requirements analysis
```

### 3. Execute Development Phases

```bash
# For each phase (1, 2, 3, ...) - run from PRP-FRAMEWORK directory:

# Generate comprehensive implementation PRP
/generate-prp ../PRP-PLANNING/PRPs/PHASE[N]_REQUIREMENTS.md

# Execute the phase implementation (creates code in ../src/)
/execute-prp ../PRP-PLANNING/PRPs/[generated-prp-file].md

# Document what was actually built (automated analysis)
/update-phase-completion [N]

# Adapt future phases based on learnings (automated adaptation)
/update-phase-plans [N]

# Repeat for next phase...
```

**📖 See [QUICK_START.md](PRP-FRAMEWORK/QUICK_START.md) for a complete setup guide!**

## 📋 Framework Components

### Core Templates
- **Planning Templates**: PROJECT_PHASE_PLAN, PHASE_DEPENDENCY_MAP, PHASE_ADAPTATION_LOG
- **PRP Templates**: Enhanced prp_base.md with phase-aware capabilities
- **Project Templates**: CLAUDE_PROJECT, CLAUDE_BACKEND, CLAUDE_FRONTEND, CLAUDE_SHARED

### Claude Code Commands
- `/plan-project-phases` - Systematic phase planning from BRD/Architecture documents
- `/generate-prp` - Generate comprehensive implementation PRPs
- `/execute-prp` - Execute PRP implementations with quality validation
- `/update-phase-completion` - Automated completion documentation
- `/update-phase-plans` - Dynamic phase adaptation based on learnings

### Project Types Supported
- **Web Applications**: Full-stack web development with frontend/backend separation
- **Trading Platforms**: Real-time data processing with performance requirements
- **SaaS Applications**: Multi-tenant applications with scalability needs
- **E-commerce Systems**: Complex business logic with payment and inventory
- **IoT Platforms**: Device management and data processing systems
- **Microservices**: Distributed system architectures

## 🏗️ Internal Three-Directory Architecture

The framework uses a clean internal three-directory structure within the main repository:

```
Complex-PRP-Framework/                    # Main repository
├── PRP-FRAMEWORK/                        # Pure framework code  
│   ├── .claude/                         # Claude Code commands
│   ├── templates/                       # Core framework templates
│   │   ├── project/                     # Project structure templates
│   │   ├── prp/                         # PRP generation templates
│   │   └── planning/                    # Planning and tracking templates
│   ├── examples/                        # Complete project examples
│   ├── use-cases/                       # Specialized framework variations
│   ├── tools/                           # Framework utilities
│   └── docs/                            # Framework documentation
├── PRP-PLANNING/                         # Your project management
│   ├── PLANNING/                        # Your project documents
│   │   ├── BRD_YourProject.md          # Business requirements
│   │   ├── Architecture_YourProject.md  # Technical architecture
│   │   └── CLAUDE_*.md                  # Claude Code guidelines
│   ├── PRPs/                            # Generated planning files
│   │   ├── PROJECT_PHASE_PLAN.md        # Master phase plan
│   │   └── PHASE[N]_REQUIREMENTS.md    # Individual phase files
│   └── TASK.md                          # Project task tracking
├── src/                                  # Your actual source code
│   ├── CLAUDE.md                        # Main project guidance (auto-copied)
│   ├── backend/                         # Server-side implementation
│   │   └── CLAUDE.md                    # Backend guidance (auto-copied)
│   ├── frontend/                        # Client-side implementation
│   │   └── CLAUDE.md                    # Frontend guidance (auto-copied)
│   ├── shared/                          # Common utilities
│   │   └── CLAUDE.md                    # Shared code guidance (auto-copied)
│   └── tests/                           # Test suites
├── README.md                            # This file
├── PRP-FRAMEWORK/FRAMEWORK_GUIDE.md     # Complete methodology
└── LICENSE                              # License file
```

## 🎯 When to Use Complex PRP Framework

### Perfect For:
- **Multi-Component Projects**: Frontend, backend, database, integrations
- **Performance-Critical Systems**: Specific latency, throughput, or reliability targets  
- **Complex Integrations**: External APIs, third-party services, multiple data sources
- **Regulatory Requirements**: Security, compliance, audit trails
- **Scalable Applications**: Must support growth and future enhancements

### Example Project Types:
- Trading platforms with real-time data processing
- SaaS applications with complex business logic
- E-commerce systems with payment and inventory management
- IoT platforms with device management and analytics
- Healthcare systems with compliance requirements
- Financial applications with audit trails

### Not Ideal For:
- Simple CRUD applications
- Single-component features  
- Proof-of-concept projects
- Projects with fewer than 3 major components

## 📚 Documentation

- **[Getting Started Guide](PRP-FRAMEWORK/docs/getting-started.md)** - Complete setup and first project
- **[Framework Guide](PRP-FRAMEWORK/FRAMEWORK_GUIDE.md)** - Complete methodology documentation
- **[Quick Start Guide](PRP-FRAMEWORK/QUICK_START.md)** - 5-minute setup guide

## 🤝 Contributing

We welcome contributions! Here's how to get involved:

1. **Fork the repository** and create a feature branch
2. **Add your enhancements** - new project types, templates, or tools
3. **Test thoroughly** - ensure your changes work with existing examples
4. **Document your changes** - update relevant documentation
5. **Submit a pull request** - we'll review and integrate valuable contributions

### Areas for Contribution:
- **New Project Types**: Add templates for additional project architectures
- **Framework Tools**: Enhance project generation and validation utilities
- **Documentation**: Improve guides, examples, and troubleshooting
- **Templates**: Create specialized templates for specific technologies
- **Integration**: Add support for new development tools and frameworks

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Based on successful implementation patterns from real-world complex projects
- Inspired by systematic software development methodologies
- Built for the Claude Code ecosystem and AI-assisted development workflows

---

## 🚀 Ready to Start?

1. **Choose your approach**:
   - **New Project**: Use the project generator for a fresh start
   - **Existing Project**: Use the migration assistant to adopt the framework
   
2. **Follow the systematic workflow**:
   - Create comprehensive BRD and Architecture documents
   - Run systematic phase planning
   - Execute phases with adaptation and learning

3. **Join the community**:
   - Share your project experiences
   - Contribute improvements back to the framework
   - Help others succeed with complex project development

**Transform your complex project ideas into successful, systematic implementations with the Complex PRP Framework!**