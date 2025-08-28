#!/usr/bin/env python3
"""
Complex PRP Framework - Project Generator

This tool creates new projects with the Complex PRP framework structure,
customized templates, and proper configuration.
"""

import os
import argparse
import shutil
import json
from pathlib import Path
from typing import Dict, List, Optional

# Project type configurations
PROJECT_TYPES = {
    "web-application": {
        "description": "Full-stack web application with frontend/backend separation",
        "backend_framework": "FastAPI",
        "frontend_framework": "React",
        "frontend_language": "TypeScript", 
        "database_type": "PostgreSQL",
        "directories": ["backend", "frontend", "shared", "tests", "docs"],
        "template_vars": {
            "TECHNOLOGY_STACK": "Python/TypeScript",
            "PRIMARY_LANGUAGE": "Python",
            "BACKEND_FRAMEWORK": "FastAPI",
            "FRONTEND_FRAMEWORK": "React",
            "FRONTEND_LANGUAGE": "TypeScript",
            "DATABASE_TYPE": "PostgreSQL",
            "API_STYLE": "RESTful"
        }
    },
    "trading-platform": {
        "description": "Real-time trading platform with performance requirements",
        "backend_framework": "FastAPI",
        "frontend_framework": "React",
        "frontend_language": "TypeScript",
        "database_type": "SQLite",
        "directories": ["backend", "frontend", "shared", "tests", "docs"],
        "template_vars": {
            "TECHNOLOGY_STACK": "Python/TypeScript",
            "PRIMARY_LANGUAGE": "Python", 
            "BACKEND_FRAMEWORK": "FastAPI",
            "FRONTEND_FRAMEWORK": "React",
            "FRONTEND_LANGUAGE": "TypeScript",
            "DATABASE_TYPE": "SQLite",
            "API_STYLE": "RESTful + WebSocket"
        }
    },
    "saas-application": {
        "description": "Multi-tenant SaaS application with scalability requirements",
        "backend_framework": "Django",
        "frontend_framework": "Vue.js",
        "frontend_language": "TypeScript",
        "database_type": "PostgreSQL",
        "directories": ["backend", "frontend", "shared", "tests", "docs"],
        "template_vars": {
            "TECHNOLOGY_STACK": "Python/TypeScript",
            "PRIMARY_LANGUAGE": "Python",
            "BACKEND_FRAMEWORK": "Django", 
            "FRONTEND_FRAMEWORK": "Vue.js",
            "FRONTEND_LANGUAGE": "TypeScript",
            "DATABASE_TYPE": "PostgreSQL",
            "API_STYLE": "RESTful"
        }
    },
    "ecommerce-system": {
        "description": "E-commerce platform with payment and inventory management",
        "backend_framework": "Express.js",
        "frontend_framework": "React",
        "frontend_language": "TypeScript",
        "database_type": "MongoDB",
        "directories": ["backend", "frontend", "shared", "tests", "docs"],
        "template_vars": {
            "TECHNOLOGY_STACK": "Node.js/TypeScript",
            "PRIMARY_LANGUAGE": "TypeScript",
            "BACKEND_FRAMEWORK": "Express.js",
            "FRONTEND_FRAMEWORK": "React", 
            "FRONTEND_LANGUAGE": "TypeScript",
            "DATABASE_TYPE": "MongoDB",
            "API_STYLE": "RESTful"
        }
    },
    "microservices": {
        "description": "Distributed microservices architecture",
        "backend_framework": "Spring Boot",
        "frontend_framework": "Angular",
        "frontend_language": "TypeScript",
        "database_type": "PostgreSQL",
        "directories": ["services", "gateway", "frontend", "shared", "tests", "docs"],
        "template_vars": {
            "TECHNOLOGY_STACK": "Java/TypeScript",
            "PRIMARY_LANGUAGE": "Java",
            "BACKEND_FRAMEWORK": "Spring Boot",
            "FRONTEND_FRAMEWORK": "Angular",
            "FRONTEND_LANGUAGE": "TypeScript", 
            "DATABASE_TYPE": "PostgreSQL",
            "API_STYLE": "RESTful + gRPC"
        }
    }
}

class ProjectGenerator:
    """Generates new projects with Complex PRP framework structure."""
    
    def __init__(self, framework_path: str):
        self.framework_path = Path(framework_path)
        self.templates_path = self.framework_path / "templates"
    
    def generate_project(self, project_name: str, project_type: str, output_dir: str = None) -> str:
        """Generate a new project with the specified configuration."""
        
        if project_type not in PROJECT_TYPES:
            raise ValueError(f"Unknown project type: {project_type}. Available types: {list(PROJECT_TYPES.keys())}")
        
        config = PROJECT_TYPES[project_type]
        
        # Determine output directory
        if output_dir is None:
            output_dir = Path.cwd().parent / project_name
        else:
            output_dir = Path(output_dir) / project_name
        
        print(f"Creating project: {project_name}")
        print(f"Project type: {project_type}")
        print(f"Description: {config['description']}")
        print(f"Output directory: {output_dir}")
        
        # Create project directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create directory structure
        self._create_directory_structure(output_dir, config)
        
        # Copy and customize templates
        self._copy_templates(output_dir, project_name, config)
        
        # Copy Claude Code commands
        self._copy_claude_commands(output_dir)
        
        # Create configuration files
        self._create_config_files(output_dir, project_name, config)
        
        # Create example files
        self._create_example_files(output_dir, project_name, config)
        
        print(f"\\n✅ Project '{project_name}' created successfully!")
        print(f"📁 Location: {output_dir}")
        print(f"\\n🚀 Next steps:")
        print(f"1. cd {output_dir}")
        print(f"2. Edit PLANNING/BRD_{project_name}.md with your requirements")
        print(f"3. Edit PLANNING/Architecture_{project_name}.md with your design") 
        print(f"4. Run: /plan-project-phases PLANNING/BRD_{project_name}.md PLANNING/Architecture_{project_name}.md")
        
        return str(output_dir)
    
    def _create_directory_structure(self, project_dir: Path, config: Dict):
        """Create the project directory structure."""
        
        # Standard directories
        directories = [
            "PLANNING",
            "PRPs", 
            "PRPs/templates",
            "tests",
            "docs",
            ".claude",
            ".claude/commands"
        ]
        
        # Add project-specific directories
        directories.extend(config["directories"])
        
        for directory in directories:
            (project_dir / directory).mkdir(parents=True, exist_ok=True)
    
    def _copy_templates(self, project_dir: Path, project_name: str, config: Dict):
        """Copy and customize template files."""
        
        # Copy PRP templates
        prp_templates = self.templates_path / "prp"
        if prp_templates.exists():
            for template_file in prp_templates.glob("*.md"):
                shutil.copy2(template_file, project_dir / "PRPs" / "templates")
        
        # Copy planning templates  
        planning_templates = self.templates_path / "planning"
        if planning_templates.exists():
            for template_file in planning_templates.glob("*.md"):
                shutil.copy2(template_file, project_dir / "PRPs" / "templates")
        
        # Copy and customize project templates
        project_templates = self.templates_path / "project"
        if project_templates.exists():
            self._copy_and_customize_project_templates(project_dir, project_name, config, project_templates)
    
    def _copy_and_customize_project_templates(self, project_dir: Path, project_name: str, config: Dict, templates_dir: Path):
        """Copy and customize project-level templates."""
        
        template_vars = config.get("template_vars", {})
        template_vars.update({
            "PROJECT_NAME": project_name,
            "BACKEND_DIR": "backend",
            "FRONTEND_DIR": "frontend", 
            "SHARED_DIR": "shared",
            "DEPENDENCIES_FILE": self._get_dependencies_file(config),
            "ENVIRONMENT_MANAGEMENT": self._get_environment_management(config)
        })
        
        # Process each template file
        for template_file in templates_dir.glob("TEMPLATE_*.md"):
            output_filename = template_file.name.replace("TEMPLATE_", "").replace("CLAUDE_", f"{project_name}_")
            if "CLAUDE" in template_file.name:
                output_filename = template_file.name.replace("TEMPLATE_", "")
                output_path = project_dir / "PLANNING" / output_filename
            else:
                output_path = project_dir / "PLANNING" / output_filename
                
            self._process_template_file(template_file, output_path, template_vars)
    
    def _process_template_file(self, template_file: Path, output_path: Path, template_vars: Dict):
        """Process a template file, replacing variables with actual values."""
        
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace template variables
        for var, value in template_vars.items():
            content = content.replace(f"{{{var}}}", str(value))
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _copy_claude_commands(self, project_dir: Path):
        """Copy Claude Code commands to the project."""
        
        commands_source = self.framework_path / ".claude" / "commands"
        commands_dest = project_dir / ".claude" / "commands"
        
        if commands_source.exists():
            for command_file in commands_source.glob("*.md"):
                shutil.copy2(command_file, commands_dest)
    
    def _create_config_files(self, project_dir: Path, project_name: str, config: Dict):
        """Create project configuration files."""
        
        # Create .gitignore
        gitignore_content = self._get_gitignore_content(config)
        with open(project_dir / ".gitignore", 'w') as f:
            f.write(gitignore_content)
        
        # Create Claude settings
        claude_settings = {
            "projectName": project_name,
            "projectType": config.get("description", "Complex multi-phase project"),
            "framework": "Complex-PRP-Framework",
            "version": "1.0.0"
        }
        
        with open(project_dir / ".claude" / "settings.local.json", 'w') as f:
            json.dump(claude_settings, f, indent=2)
        
        # Create TASK.md
        task_content = f"""# {project_name} - Task Tracking

## Project Overview
{config.get('description', 'Complex multi-phase project using Complex PRP Framework')}

## Current Status
- **Phase**: Planning
- **Last Updated**: {self._get_current_date()}

## Planning Phase Tasks
- [ ] Complete BRD documentation (PLANNING/BRD_{project_name}.md)
- [ ] Complete Architecture documentation (PLANNING/Architecture_{project_name}.md)
- [ ] Run systematic phase planning: `/plan-project-phases PLANNING/BRD_{project_name}.md PLANNING/Architecture_{project_name}.md`
- [ ] Review generated phase plan and dependency map
- [ ] Customize phase files if needed

## Next Session Priorities
1. Document business requirements in detail
2. Define technical architecture and technology choices
3. Run systematic phase planning to generate optimal development strategy

## Notes
- Project created using Complex PRP Framework
- Framework supports systematic planning and phase adaptation
- Use `/plan-project-phases` for optimal phase breakdown based on requirements

---
*Updated by: Complex PRP Framework Project Generator*
"""
        
        with open(project_dir / "TASK.md", 'w') as f:
            f.write(task_content)
    
    def _create_example_files(self, project_dir: Path, project_name: str, config: Dict):
        """Create example files to help users get started."""
        
        # Create example README
        readme_content = f"""# {project_name}

{config.get('description', 'A complex multi-phase project built with the Complex PRP Framework')}

## Technology Stack
- **Backend**: {config.get('backend_framework', 'TBD')}
- **Frontend**: {config.get('frontend_framework', 'TBD')}
- **Database**: {config.get('database_type', 'TBD')}
- **Language**: {config.get('frontend_language', 'TBD')}

## Getting Started

### 1. Complete Project Documentation
- Edit `PLANNING/BRD_{project_name}.md` with your business requirements
- Edit `PLANNING/Architecture_{project_name}.md` with your technical design

### 2. Generate Phase Plan
```bash
/plan-project-phases PLANNING/BRD_{project_name}.md PLANNING/Architecture_{project_name}.md
```

### 3. Execute Development Phases
```bash
# For each phase:
/generate-prp INITIAL_PHASE[N].md
/execute-prp PRPs/[generated-prp].md
/update-phase-completion [N]
/update-phase-plans [N]
```

## Project Structure
```
{project_name}/
├── PLANNING/           # Project planning documents
├── PRPs/              # Complex PRP framework files
├── {'/'.join(config.get('directories', []))}
├── TASK.md            # Project task tracking
└── README.md          # This file
```

## Framework Features
- **Systematic Planning**: AI-driven phase breakdown from BRD/Architecture
- **Context Continuity**: Each phase understands previous implementation
- **Dynamic Adaptation**: Future phases adapt based on learnings
- **Quality Assurance**: Built-in testing and validation

Built with [Complex PRP Framework](https://github.com/your-org/complex-prp-framework)
"""
        
        with open(project_dir / "README.md", 'w') as f:
            f.write(readme_content)
    
    def _get_dependencies_file(self, config: Dict) -> str:
        """Get the appropriate dependencies file name for the project type."""
        backend_framework = config.get("backend_framework", "")
        
        if "python" in backend_framework.lower() or "django" in backend_framework.lower() or "fastapi" in backend_framework.lower():
            return "requirements.txt"
        elif "node" in backend_framework.lower() or "express" in backend_framework.lower():
            return "package.json"
        elif "java" in backend_framework.lower() or "spring" in backend_framework.lower():
            return "pom.xml"
        else:
            return "requirements.txt"
    
    def _get_environment_management(self, config: Dict) -> str:
        """Get the appropriate environment management approach."""
        backend_framework = config.get("backend_framework", "")
        
        if "python" in backend_framework.lower() or "django" in backend_framework.lower() or "fastapi" in backend_framework.lower():
            return "virtual environments"
        elif "node" in backend_framework.lower() or "express" in backend_framework.lower():
            return "npm/yarn"
        elif "java" in backend_framework.lower() or "spring" in backend_framework.lower():
            return "Maven/Gradle"
        else:
            return "virtual environments"
    
    def _get_gitignore_content(self, config: Dict) -> str:
        """Generate appropriate .gitignore content based on project type."""
        
        base_gitignore = """# Complex PRP Framework
.claude/settings.local.json
PRPs/*.md
!PRPs/templates/

# IDE and editors
.vscode/
.idea/
*.swp
*.swo
*~

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Database
*.db
*.sqlite
*.sqlite3
"""
        
        backend_framework = config.get("backend_framework", "").lower()
        
        if "python" in backend_framework or "django" in backend_framework or "fastapi" in backend_framework:
            base_gitignore += """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
env/
ENV/
env.bak/
venv.bak/

# pytest
.pytest_cache/
.coverage
htmlcov/

# mypy
.mypy_cache/
.dmypy.json
dmypy.json
"""
        
        if "node" in backend_framework or "express" in backend_framework or "react" in config.get("frontend_framework", "").lower():
            base_gitignore += """
# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*

# Build outputs
build/
dist/
out/

# Next.js
.next/

# Nuxt.js
.nuxt/

# React
build/
"""
        
        return base_gitignore
    
    def _get_current_date(self) -> str:
        """Get current date in YYYY-MM-DD format."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")

def main():
    """Main entry point for the project generator."""
    
    parser = argparse.ArgumentParser(
        description="Generate new projects with Complex PRP Framework structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available project types:
{chr(10).join([f"  {ptype}: {config['description']}" for ptype, config in PROJECT_TYPES.items()])}

Examples:
  python project-generator.py --name MyTradingApp --type trading-platform
  python project-generator.py --name MySaasApp --type saas-application --output ../projects
"""
    )
    
    parser.add_argument(
        "--name", 
        required=True,
        help="Project name (will be used for directory name and project references)"
    )
    
    parser.add_argument(
        "--type",
        required=True,
        choices=list(PROJECT_TYPES.keys()),
        help="Project type"
    )
    
    parser.add_argument(
        "--output",
        help="Output directory (default: ../PROJECT_NAME)"
    )
    
    parser.add_argument(
        "--list-types",
        action="store_true",
        help="List available project types and exit"
    )
    
    args = parser.parse_args()
    
    if args.list_types:
        print("Available project types:")
        for ptype, config in PROJECT_TYPES.items():
            print(f"  {ptype}: {config['description']}")
        return
    
    try:
        # Determine framework path (current script's directory parent)
        framework_path = Path(__file__).parent.parent
        
        generator = ProjectGenerator(framework_path)
        project_path = generator.generate_project(args.name, args.type, args.output)
        
        print(f"\\n🎉 Success! Your project is ready for complex PRP development.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())