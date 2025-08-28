# [Project Name] — Business Requirements Document (BRD) Template

### TL;DR

[Write a concise, 2-3 sentence summary of what you're building, who it's for, and the key value proposition. Focus on the core user workflow and business outcome.]

Example: "A [type of application] that [main functionality] for [target users] to [primary goal]. [Release scope] delivers [key features] optimized for [critical requirements]. Target user is [specific persona] with an eye to [future expansion path]."

---

## Goals

### Business Goals

[Define the strategic business objectives this project will achieve. Make them specific and measurable.]

* [Primary business outcome - what success looks like from a business perspective]

* [Technical/foundation goal - what capabilities this establishes for future development]

* [Performance/operational goal - what operational standards must be met]

* [Validation goal - what assumptions or workflows this will prove or validate]

### User Goals

[Define what end users want to accomplish. Focus on user outcomes, not features.]

* [Primary user workflow - what users want to see/monitor/track]

* [Secondary user action - what users want to configure/manage/control]

* [Tertiary user need - what users want to review/analyze/understand]

* [User experience goal - what kind of experience users expect]

### Non-Goals

[Clearly state what this project will NOT include to prevent scope creep.]

* [Feature category not included in this release - saved for later]

* [Advanced functionality not included - reserved for specific future release]

* [User types not supported - until later releases]

---

## User Stories

**Primary Persona:** [Main User Type/Role]

[List 5-8 core user stories that capture the essential workflows. Use "As a [persona], I want [capability] so that [outcome]" format.]

* As a [persona], I want to [core action] so I can [primary outcome].

* As a [persona], I want to [setup/configuration action] so I can [enable core workflow].

* As a [persona], I want to [monitoring action] so I can [stay informed of status].

* As a [persona], I want to [response action] so I can [take action when needed].

* As a [persona], I want to [review action] so I can [analyze and improve over time].

* As an [admin persona], I want to [administrative action] so I can [maintain system health].

**Secondary Persona (if applicable):** [Secondary User Type/Role]

* As a [secondary persona], I want to [secondary workflow] so I can [secondary outcome].

---

## Functional Requirements

### [Core Feature Category 1] (Priority: P0)

[Describe the most critical functionality that absolutely must work.]

* [Specific requirement with clear acceptance criteria]

* [Integration requirement - what external systems must connect]

* [Data requirement - what information must be captured/stored]

### [Core Feature Category 2] (Priority: P0)

[Describe the second most critical functionality.]

* [User interaction requirement - what interfaces users need]

* [Processing requirement - what the system must compute/analyze]

* [Output requirement - what results/alerts/reports must be generated]

### [Supporting Feature Category] (Priority: P1)

[Describe important but not critical functionality.]

* [Configuration requirement - what users must be able to customize]

* [Management requirement - what administration features are needed]

* [Optional enhancement that adds significant value]

**Out of Scope (This Release):** [List specific features that are explicitly not included]

---

## Non-Functional Requirements

### Performance Requirements

* [Response time requirement] - [specific metric, e.g., "sub-second processing"]

* [Throughput requirement] - [specific capacity, e.g., "handle X operations/second"]

* [Availability requirement] - [uptime target, e.g., "99% uptime during business hours"]

* [Scalability requirement] - [growth capacity, e.g., "support up to X concurrent users"]

### Security Requirements

* [Authentication requirement] - [how users will be authenticated]

* [Authorization requirement] - [what access controls are needed]

* [Data protection requirement] - [how sensitive data will be protected]

* [Credential management] - [how API keys/secrets will be handled]

### Integration Requirements

* [Primary external API] - [what it provides and how it's used]

* [Secondary external service] - [integration requirements]

* [Internal system integration] - [if connecting to existing systems]

### Usability Requirements

* [User experience standard] - [response time, interface clarity]

* [Accessibility requirement] - [keyboard navigation, screen readers]

* [Device compatibility] - [desktop, mobile, specific browsers]

### Compliance Requirements

* [Regulatory requirement] - [specific standards that must be met]

* [Data privacy requirement] - [GDPR, CCPA, or other privacy standards]

* [Industry standard] - [specific compliance needs for your domain]

---

## User Experience Flow

### Entry Point & First-Time User Experience

[Describe how new users will get started and what their onboarding experience should be.]

* [Initial setup process and guided configuration]

* [Connection testing and validation feedback]

* [Sample data or starter configuration provided]

### Core User Workflow

[Describe the primary user workflow step by step.]

1. **[Primary activity]:** [What users do most often and what they see]

2. **[Configuration activity]:** [How users customize the system for their needs]

3. **[Response activity]:** [How users respond to alerts/notifications/events]

4. **[Review activity]:** [How users analyze results and refine their setup]

5. **[Management activity]:** [How users maintain and update their configuration]

### Advanced Features & Edge Cases

[Describe how the system handles unusual situations.]

* [Rate limiting scenario] - [how system degrades gracefully]

* [Connectivity issues] - [how system handles network problems]

* [Error conditions] - [how users are informed and can recover]

### UI/UX Requirements

[Describe the user interface and experience standards.]

* [Visual design requirements] - [performance-focused, accessibility needs]

* [Interaction patterns] - [keyboard shortcuts, notification styles]

* [Information hierarchy] - [what's most important to display prominently]

---

## Success Metrics

### User-Centric Metrics

[How you'll measure user success and satisfaction.]

* [User engagement metric] - [how often users interact with core features]

* [User efficiency metric] - [how well the system serves user goals]

* [User satisfaction metric] - [qualitative measure of user experience]

### Business Metrics

[How you'll measure business value and ROI.]

* [Business outcome metric] - [direct business value created]

* [Operational efficiency metric] - [cost savings or time savings]

* [Strategic metric] - [progress toward larger business goals]

### Technical Metrics

[How you'll measure system performance and reliability.]

* [Performance metric] - [response times, throughput achieved]

* [Reliability metric] - [uptime, error rates, system stability]

* [Quality metric] - [test coverage, bug rates, maintenance needs]

### Tracking Plan

[What events you'll log to measure these metrics.]

* Key user actions: [list 5-7 critical events to track]
* System health events: [list 3-5 technical events to monitor]
* Business outcome events: [list 3-5 success events to measure]

---

## Technical Integration Points

### External APIs and Services

* [Primary API] - [what data/functionality it provides]

* [Secondary service] - [integration requirements and dependencies]

* [Authentication service] - [how external auth will work]

### Data Storage Requirements

* [Primary data types] - [what information must be stored]

* [Data retention] - [how long data is kept and why]

* [Data privacy] - [how sensitive information is protected]

* [Data access patterns] - [how data will be queried and retrieved]

### System Architecture Needs

[High-level technical requirements that will inform architecture decisions.]

* [Deployment model] - [self-hosted, cloud, hybrid requirements]

* [Scalability needs] - [current and future capacity requirements]

* [Integration patterns] - [how this system connects to others]

* [Technology constraints] - [specific technical requirements or limitations]

---


### Suggested Phase Breakdown

**Phase 1: [Core Foundation]**
* [Foundational components that other phases depend on]
* [Basic functionality that proves core workflow]
* [Integration with primary external dependencies]

**Phase 2: [User Experience & Polish]**
* [User interface and experience features]
* [Advanced configuration and customization]
* [User feedback and iteration]

**Phase 3: [Advanced Features & Production]**
* [Nice-to-have features that add significant value]
* [Production readiness and monitoring]
* [Performance optimization and security hardening]

---

## Future Roadmap Context

[Describe how this project fits into the larger product roadmap.]

* **[Next Release]:** [What capabilities this enables for the next release]

* **[Future Major Release]:** [How this foundation supports major future features]

* **[Long-term Vision]:** [How this fits into the overall product strategy]

---

## Assumptions & Dependencies

### External Dependencies

* [Critical external service or API availability]
* [Third-party integrations required]
* [Infrastructure or platform requirements]

### Internal Dependencies

* [Other projects or teams this depends on]
* [Existing systems that must remain operational]

### Key Assumptions

* [User behavior assumptions that affect design]
* [Technical assumptions about performance or capacity]
* [Business assumptions about market or adoption]

---

## Acceptance Criteria

### Definition of Done

[Specific criteria that must be met for the project to be considered complete.]

* [ ] [All P0 functional requirements implemented and tested]
* [ ] [Performance requirements met under realistic conditions]
* [ ] [Security requirements validated through testing]
* [ ] [Integration requirements working end-to-end]
* [ ] [User experience requirements validated with real users]
* [ ] [Documentation complete for users and maintainers]

### Success Validation

[How you'll know this project succeeded in achieving its goals.]

* [User workflow validation] - [specific user scenarios that must work]
* [Performance validation] - [specific benchmarks that must be achieved]
* [Business outcome validation] - [specific business metrics that must be met]

---

## Complex PRP Framework Integration

### For Complex Multi-Phase Projects

If this project qualifies for the Complex Multi-Phase PRP framework (multiple components, complex architecture, performance requirements, integration points, regulatory requirements, or scalability needs), this BRD will be used as input to the systematic phase planning process.

#### Framework Usage
```bash
# After completing this BRD and the Architecture document:
/plan-project-phases PLANNING/BRD_[ProjectName].md PLANNING/Architecture_[ProjectName].md
```

This command will analyze the business requirements and technical architecture to:
- Generate optimal phase breakdown based on dependency analysis
- Create all PHASE[N]_REQUIREMENTS.md files with proper sequencing
- Establish integration points and performance baselines across phases
- Generate PROJECT_PHASE_PLAN.md master planning document

#### CLAUDE File Management
During the `/execute-prp` command, CLAUDE development guidelines will be automatically copied from the PLANNING/ repository to the appropriate project locations:
- `PLANNING/CLAUDE_PROJECT.md` → `CLAUDE.md` (project root)
- `PLANNING/CLAUDE_BACKEND.md` → `backend/CLAUDE.md` (if backend/ exists)
- `PLANNING/CLAUDE_FRONTEND.md` → `frontend/CLAUDE.md` (if frontend/ exists)
- `PLANNING/CLAUDE_SHARED.md` → `shared/CLAUDE.md` (if shared/ exists)

This ensures Claude Code auto-discovery works correctly while maintaining authoritative versions in PLANNING/.

---

## Appendices

### Glossary

[Define any domain-specific terms used in this document.]

* [Term 1]: [Definition]
* [Term 2]: [Definition]

### Reference Materials

[Link to supporting documents, research, or specifications.]

* [Relevant industry standards or specifications]
* [User research or market analysis that informed these requirements]
* [Technical specifications or API documentation]

### Revision History

[Track changes to this document over time.]

* v1.0 - [Date] - [Author] - Initial version
* v1.1 - [Date] - [Author] - [Description of changes]

---

**Document Owner:** [Name and contact]
**Last Updated:** [Date]
**Review Cycle:** [How often this document should be reviewed and updated]