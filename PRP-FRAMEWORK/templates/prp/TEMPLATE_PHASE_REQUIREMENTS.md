# TEMPLATE: Multi-Phase Project Phase Requirements

## 📋 Phase Information
- **Phase Number**: [X]
- **Phase Name**: [Descriptive Name]
- **Dependencies**: [List prerequisite phases]

## 🔄 Previous Phase Context
### What Already Exists
```
[Detailed description of implemented components from previous phases]
- File structure created
- API endpoints implemented
- Database schema established
- Key functions and classes
- Integration patterns used
```

### Existing Codebase References
- **Backend Files**: `backend/[specific files]`
- **Frontend Files**: `frontend/[specific files]`
- **Shared Components**: `shared/[specific files]`
- **Configuration**: `[config files]`
- **Database Schema**: `[schema files or descriptions]`

### API Contracts Established
```
[Document existing API endpoints that this phase will use]
GET /api/[endpoint] - Description
POST /api/[endpoint] - Description
WebSocket /ws/[endpoint] - Description
```

### Integration Points Available
```
[Describe how previous phases expose functionality for integration]
- Database connections: [Connection patterns]
- Service interfaces: [Interface definitions]
- Event systems: [Event handling patterns]
- Authentication: [Auth patterns established]
```

## 🎯 Current Phase Requirements
### Primary Objectives
```
[Clear statement of what this phase will accomplish]
1. [Objective 1]
2. [Objective 2]
3. [Objective 3]
```

### Detailed Requirements
```
[Specific features and functionality to implement]
- Feature A: [Description and acceptance criteria]
- Feature B: [Description and acceptance criteria]
- Feature C: [Description and acceptance criteria]
```

### Technical Specifications
```
[Technical details for implementation]
- Technology stack additions: [New dependencies]
- Architecture patterns: [Patterns to follow]
- Performance requirements: [Specific metrics]
- Security considerations: [Security requirements]
```

## 🔗 Integration Requirements
### Backward Compatibility
```
[How to ensure this phase doesn't break previous phases]
- API compatibility: [Maintain existing endpoints]
- Database compatibility: [Schema evolution strategy]
- Configuration compatibility: [Config migration needs]
```

### Forward Integration
```
[How this phase prepares for future phases]
- Expose interfaces: [What interfaces to create]
- Event hooks: [Events to emit for future phases]
- Extension points: [Where future phases can plug in]
```

### Cross-Phase Communication
```
[How this phase will interact with existing components]
- Data flow: [How data moves between phases]
- Event handling: [How events are processed]
- Error handling: [How errors propagate]
```

## ✅ Success Criteria
### Functional Validation
```
[How to verify the phase works correctly]
- [ ] [Specific test case 1]
- [ ] [Specific test case 2]
- [ ] [Specific test case 3]
```

### Integration Validation
```
[How to verify integration with previous phases]
- [ ] Previous phase features still work
- [ ] New features integrate seamlessly
- [ ] End-to-end workflows function properly
- [ ] Performance requirements met
```

### Performance Benchmarks
```
[Specific performance criteria to meet]
- Response time: [Specific timing requirements]
- Throughput: [Specific throughput requirements]
- Resource usage: [Memory/CPU limits]
```

## 📁 Expected Deliverables
### Code Components
```
[Specific files and components to be created]
- Backend: [List of files/modules]
- Frontend: [List of components/pages]
- Shared: [List of utilities/types]
- Tests: [List of test files]
```

### Documentation Updates
```
[Documentation that needs to be updated]
- [ ] API documentation
- [ ] Architecture diagrams
- [ ] User guides
- [ ] Developer setup instructions
```

### Configuration Changes
```
[Configuration updates needed]
- Environment variables: [New vars needed]
- Database migrations: [Schema changes]
- Deployment scripts: [Script updates]
```

## 🔧 Implementation Guidelines
### Code Patterns to Follow
```
[Specific patterns established in previous phases]
- Error handling: [Pattern to use]
- Logging: [Logging format/strategy]
- Testing: [Testing patterns]
- Documentation: [Doc string formats]
```

### Dependencies and Constraints
```
[Technical constraints and dependency requirements]
- Technology versions: [Specific versions to use]
- External services: [APIs or services to integrate]
- Performance constraints: [Specific limitations]
```

## 🧪 Testing Strategy
### Unit Testing
```
[Unit testing approach for this phase]
- Coverage requirements: [Minimum coverage %]
- Mock strategies: [How to mock previous phases]
- Test organization: [How to structure tests]
```

### Integration Testing
```
[How to test integration with previous phases]
- End-to-end scenarios: [Key workflows to test]
- Cross-phase data flow: [Data consistency tests]
- Performance testing: [Load/stress testing approach]
```


## 🔄 Phase Completion Criteria
### Definition of Done
```
[Clear criteria for when this phase is complete]
- [ ] All functional requirements implemented
- [ ] Integration tests passing
- [ ] Performance benchmarks met
- [ ] Documentation updated
- [ ] Code review completed
- [ ] Deployment successful
```

### Handoff Requirements
```
[What needs to be documented for the next phase]
- Updated architecture diagrams
- API documentation
- Integration guide for next phase
- Known limitations or technical debt
```