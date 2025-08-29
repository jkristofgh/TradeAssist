# Task Completion Checklist: TradeAssist

## When a Development Task is Completed

Since this is a minimal setup project using the Complex PRP Framework, the task completion process follows the framework's systematic approach:

### Framework Task Completion Process
1. **Use Framework Commands**: Execute the appropriate PRP framework command for the completed phase
2. **Update Phase Completion**: Run `/update-phase-completion [N]` to automatically document what was built
3. **Adapt Future Phases**: Run `/update-phase-plans [N]` to adjust upcoming phases based on learnings
4. **Commit Changes**: Standard git workflow to commit implemented code

### Code Quality Standards (To Be Established)
When development commands are established during implementation, ensure:
- [ ] All tests pass
- [ ] Code is formatted and linted
- [ ] Type checking passes
- [ ] No security vulnerabilities introduced
- [ ] Performance requirements met (sub-second latency)

### Performance Validation (Critical for Trading App)
- [ ] Alert latency measured and under 500ms target
- [ ] Memory usage acceptable for single-user deployment
- [ ] WebSocket connections stable under load
- [ ] Database operations optimized for time-series data

### Integration Testing
- [ ] Schwab API integration tested (sandbox mode first)
- [ ] Slack notifications delivered successfully
- [ ] Sound notifications working cross-platform
- [ ] Google Cloud Secret Manager integration secure
- [ ] End-to-end alert workflow functional

### Documentation Updates
- [ ] Update CLAUDE.md files if architectural decisions change
- [ ] Update phase completion summaries with actual implementation details
- [ ] Document any deviations from planned architecture
- [ ] Record performance benchmarks achieved

## Framework Integration
The completion process is automated through the Complex PRP Framework commands, which handle:
- Automated analysis of what was actually implemented
- Integration context for next phases
- Performance baseline establishment
- Adaptation recommendations for future phases