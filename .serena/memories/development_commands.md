# Development Commands: TradeAssist

## Framework Commands (From Complex PRP Framework)
Run these commands from the PRP-FRAMEWORK directory:

### Planning Commands
- `/plan-project-phases BRD.md Architecture.md` - Generate systematic phase breakdown
- `/generate-prp PHASE[N]_REQUIREMENTS.md` - Create implementation PRP for specific phase
- `/execute-prp [generated-prp].md` - Execute phase implementation
- `/update-phase-completion [N]` - Document completed phase with automated analysis
- `/update-phase-plans [N]` - Adapt future phases based on learnings

### Current Project Commands
```bash
# Generate phase plan for TradeAssist (already executed)
/plan-project-phases ../PRP-PLANNING/PLANNING/BRD_TradingPlatform.md ../PRP-PLANNING/PLANNING/Architecture_TradingPlatform.md

# Execute phases (run after phase plan generation)
/generate-prp ../PRP-PLANNING/PRPs/PHASE1_REQUIREMENTS.md
/execute-prp ../PRP-PLANNING/PRPs/[generated-prp-file].md
/update-phase-completion 1
```

## Expected Development Commands (To Be Determined)
Since the source code structure is minimal (only .gitkeep files), development commands will be established during implementation:

### Testing Commands (Estimated)
- `pytest` - Run test suite
- `pytest --cov` - Run tests with coverage

### Code Quality Commands (Estimated)  
- `black .` - Format code
- `isort .` - Sort imports
- `flake8` - Lint code
- `mypy` - Type checking

### Application Commands (Estimated)
- `python -m src.main` - Start the application
- `python -m src.setup` - Initial setup and configuration

## Git Commands
Standard git workflow for version control and commits.