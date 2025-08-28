# TEMPLATE: Project Phase Plan

## 📋 Project Overview
- **Project Name**: [Project Name]
- **Project Type**: [Trading/SaaS/E-commerce/IoT/etc.]
- **Target Architecture**: [Single-process/Microservices/Distributed/etc.]

## 📊 Business Context
### Business Requirements Summary
```markdown
[Key business objectives from BRD]
- Primary Goal: [Main business objective]
- Success Metrics: [How success will be measured]
- User Base: [Target user characteristics]
- Performance Targets: [Critical performance requirements]
- Compliance Requirements: [Regulatory or security requirements]
```

### Architecture Summary
```markdown
[Key architectural decisions from Architecture document]
- Architecture Pattern: [Monolith/Microservices/Serverless/etc.]
- Technology Stack: [Primary technologies and frameworks]
- Data Strategy: [Database and data storage approach]
- Integration Requirements: [External systems and APIs]
- Deployment Strategy: [How system will be deployed]
```

## 🎯 Phase Breakdown Strategy

### Phase Planning Approach
- **Planning Method**: [Systematic/Manual - how phases were determined]
- **Phase Sizing Strategy**: [Small/Medium/Large - based on project characteristics]
- **Sequencing Approach**: [Sequential/Parallel/Hybrid - based on dependencies]

### Phase Overview with Template Assignments
```
Phase 1: [Phase Name] - Template: prp_base.md
├── [Key Component 1]
├── [Key Component 2] 
├── [Key Component 3]
├── Phase Type: foundation
├── Complexity: [low | medium | high]
└── Dependencies: None (Foundation phase)

Phase 2: [Phase Name] - Template: prp_base.md
├── [Key Component 1]
├── [Key Component 2]
├── [Key Component 3]
├── Phase Type: [integration | frontend | optimization]
├── Complexity: [low | medium | high]
└── Dependencies: Phase 1 ([specific dependencies])

Phase 3: [Phase Name] - Template: prp_base.md
├── [Key Component 1]
├── [Key Component 2]
├── [Key Component 3]
├── Phase Type: [integration | optimization]
├── Complexity: [low | medium | high]
└── Dependencies: Phase 1, 2 ([specific dependencies])

Phase N: [Phase Name] - Template: prp_base.md
├── [Key Component 1]
├── [Key Component 2]
├── [Key Component 3]
├── Phase Type: [optimization | finalization]
├── Complexity: [low | medium | high]
└── Dependencies: Phase 1, 2, ..., N-1 ([specific dependencies])
```

## 📋 Template Configuration Strategy

### Template Assignment Logic
```yaml
template_assignments:
  default_template: prp_base.md  # Enhanced version handles all complexity levels
  
  # Phase-specific template configuration
  phase_1:
    template: prp_base.md
    project_type: complex_multi_phase
    phase_type: foundation
    complexity_level: [low | medium | high]
    
  phase_2:
    template: prp_base.md
    project_type: complex_multi_phase
    phase_type: [integration | frontend | optimization]
    complexity_level: [low | medium | high]
    
  phase_N:
    template: prp_base.md
    project_type: complex_multi_phase
    phase_type: [optimization | finalization]
    complexity_level: [low | medium | high]

# Template selection rationale
template_rationale:
  enhanced_prp_base: |
    The enhanced prp_base.md template adapts automatically to project complexity:
    - Simple features: Uses basic validation and simple patterns
    - Complex phases: Activates multi-level validation, performance testing, integration validation
    - Phase awareness: Includes previous phase context and forward compatibility preparation
    - Scales from single components to entire system phases
```

## 🔗 Dependency Analysis

### Critical Path Analysis
```markdown
[Identify the critical path through all phases]
Critical Path: Phase 1 → Phase 2 → Phase N
- Phase 1: [Critical components that everything else depends on]
- Phase 2: [Components that depend on Phase 1 and are needed by later phases]
- Phase N: [Final integration and optimization phases]
```

### Integration Points Map
```markdown
[Key integration points between phases]
Phase 1 → Phase 2 Integration:
- API Endpoints: [Specific APIs that Phase 2 will consume]
- Database Schema: [Tables and data structures available]
- Event System: [Events that Phase 2 can subscribe to]
- Performance Baseline: [Performance characteristics to maintain]

Phase 2 → Phase 3 Integration:
- UI Components: [Frontend patterns and components available]
- User Workflows: [Established user interaction patterns]
- State Management: [Frontend state patterns established]
- API Usage Patterns: [Established API consumption patterns]

[Continue for all phase transitions...]
```


## 📈 Success Metrics by Phase

### Phase 1 Success Criteria
```markdown
Functional Criteria:
- [ ] [Specific functional requirement 1]
- [ ] [Specific functional requirement 2]
- [ ] [Specific functional requirement 3]

Technical Criteria:
- [ ] Performance: [Specific measurable target]
- [ ] Reliability: [Specific uptime or error rate target]
- [ ] Integration: [Specific integration success criteria]

Business Criteria:
- [ ] [Business value delivered by this phase]
- [ ] [User experience milestone achieved]
```

### Phase 2 Success Criteria
```markdown
Functional Criteria:
- [ ] [Building on Phase 1, specific new functionality]
- [ ] [Integration with Phase 1 components working]
- [ ] [End-to-end workflows functional]

Technical Criteria:
- [ ] Performance: [Maintains Phase 1 baseline + new targets]
- [ ] Reliability: [No degradation from Phase 1]
- [ ] Integration: [Seamless integration with Phase 1]

Business Criteria:
- [ ] [Additional business value delivered]
- [ ] [Enhanced user experience milestones]
```

### [Continue for all phases...]


## 🎯 Performance Evolution Plan

### Performance Targets by Phase
```markdown
Phase 1 Performance Baseline:
- Response Time: [Target] ([Measurement method])
- Throughput: [Target] ([Measurement method])
- Database Performance: [Target] ([Measurement method])

Phase 2 Performance Targets:
- Response Time: [Maintain Phase 1 + new targets]
- Throughput: [Enhanced from Phase 1]
- UI Performance: [New frontend performance targets]

[Continue performance evolution through all phases...]
```

### Performance Optimization Strategy
```markdown
[How performance will be maintained and improved across phases]
Optimization Phases:
- Phase 1: [Focus on core algorithm performance]
- Phase 2: [Focus on UI responsiveness and user experience]
- Phase N-1: [Focus on system-wide optimization]
- Phase N: [Focus on production optimization and monitoring]
```

## 🔒 Security & Compliance Evolution

### Security Requirements by Phase
```markdown
Phase 1 Security Foundation:
- Authentication: [Approach and implementation]
- Data Protection: [How sensitive data is protected]
- API Security: [API protection mechanisms]

Phase 2 Security Enhancements:
- Frontend Security: [Client-side security measures]
- Session Management: [User session security]
- Input Validation: [User input protection]

[Continue security evolution through all phases...]
```

### Compliance Checkpoints
```markdown
[Regulatory or compliance requirements by phase]
- Phase 1: [Compliance foundations established]
- Phase 2: [User-facing compliance requirements]
- Phase N: [Full compliance validation and audit readiness]
```

## 🧪 Testing Strategy Evolution

### Testing Approach by Phase
```markdown
Phase 1 Testing:
- Unit Testing: [Coverage targets and approach]
- Integration Testing: [Core component integration]
- Performance Testing: [Baseline establishment]

Phase 2 Testing:
- Unit Testing: [Maintain coverage + new components]
- Integration Testing: [Cross-phase integration]
- UI Testing: [Frontend testing strategy]
- End-to-End Testing: [Complete workflow testing]

[Continue testing evolution through all phases...]
```

### Test Automation Strategy
```markdown
[How testing automation will evolve across phases]
- Phase 1: [Basic CI/CD and unit test automation]
- Phase 2: [Integration test automation]
- Phase N-1: [Full test suite automation]
- Phase N: [Production monitoring and automated validation]
```


## 🔄 Adaptation Strategy

### Phase Plan Evolution
```markdown
[How this plan will evolve based on learnings]
Adaptation Points:
- After Phase 1: [What might change based on Phase 1 learnings]
- After Phase 2: [What might change based on Phase 2 learnings]
- [Continue for all phases...]

Learning Integration:
- [How completion summaries will update future phases]
- [How performance learnings will adjust targets]
- [How integration learnings will improve subsequent phases]
```

```

## 📋 Deliverables Checklist

### Phase 1 Deliverables
- [ ] PHASE1_REQUIREMENTS.md (generated)
- [ ] [Generated Phase 1 PRP file]
- [ ] [Phase 1 implementation code]
- [ ] PHASE1_COMPLETION_SUMMARY.md
- [ ] [Updated phase plans based on Phase 1 learnings]

### Phase 2 Deliverables
- [ ] Updated PHASE2_REQUIREMENTS.md
- [ ] [Generated Phase 2 PRP file]
- [ ] [Phase 2 implementation code]
- [ ] PHASE2_COMPLETION_SUMMARY.md
- [ ] [Updated phase plans based on Phase 2 learnings]

### [Continue for all phases...]

### Final Project Deliverables
- [ ] [Complete working system meeting all BRD requirements]
- [ ] [Comprehensive documentation and user guides]
- [ ] [Production deployment and monitoring]
- [ ] [Handoff documentation and training materials]

## 📞 Project Contacts & Responsibilities

### Key Stakeholders
- **Project Owner**: [Name] - [Role and responsibilities]
- **Technical Lead**: [Name] - [Architecture and technical decisions]
- **Business Analyst**: [Name] - [Requirements and user experience]

### Phase Responsibilities
```markdown
[Who is responsible for each phase]
Phase 1: [Primary and secondary responsible parties]
Phase 2: [Primary and secondary responsible parties]
[Continue for all phases...]
```

## 🎉 Success Celebration Plan

### Phase Completion Recognition
```markdown
[How phase completions will be recognized and celebrated]
- Phase 1: [Completion milestone celebration]
- Phase 2: [Enhanced functionality celebration]  
- Final Phase: [Project completion and success celebration]
```

### Project Success Metrics
```markdown
[How overall project success will be measured and celebrated]
- Business Success: [Business objectives achieved]
- Technical Success: [Technical excellence demonstrated]
```