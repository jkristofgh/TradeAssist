# Execute BASE PRP

Implement a feature using using the PRP file.

## PRP File: $ARGUMENTS

## Execution Process

1. **Setup Project Context**
   - **Load PRP**: Read the specified PRP file and understand all context and requirements
   - **Setup CLAUDE Files**: Copy CLAUDE development guidelines from PRP-PLANNING/PLANNING/ to proper locations for Claude Code auto-discovery
     - Copy `../PRP-PLANNING/PLANNING/CLAUDE_PROJECT.md` → `../src/CLAUDE.md` (main source directory) 
     - Copy `../PRP-PLANNING/PLANNING/CLAUDE_BACKEND.md` → `../src/backend/CLAUDE.md` (if backend/ directory exists)
     - Copy `../PRP-PLANNING/PLANNING/CLAUDE_FRONTEND.md` → `../src/frontend/CLAUDE.md` (if frontend/ directory exists)
     - Copy `../PRP-PLANNING/PLANNING/CLAUDE_SHARED.md` → `../src/shared/CLAUDE.md` (if shared/ directory exists)
   - **Validate Context**: Follow all instructions in the PRP and extend research if needed
   - **Complete Context**: Ensure you have all needed context to implement the PRP fully
   - **Additional Research**: Do more web searches and codebase exploration as needed

2. **ULTRATHINK**
   - Think hard before you execute the plan. Create a comprehensive plan addressing all requirements.
   - Break down complex tasks into smaller, manageable steps using your todos tools.
   - Use the TodoWrite tool to create and track your implementation plan.
   - Identify implementation patterns from existing code to follow.

3. **Execute the plan**
   - Execute the PRP
   - Implement all the code

4. **Validate**
   - Run each validation command
   - Fix any failures
   - Re-run until all pass

5. **Complete**
   - Ensure all checklist items done
   - Run final validation suite
   - Report completion status
   - Read the PRP again to ensure you have implemented everything

6. **Reference the PRP**
   - You can always reference the PRP again if needed

Note: If validation fails, use error patterns in PRP to fix and retry.