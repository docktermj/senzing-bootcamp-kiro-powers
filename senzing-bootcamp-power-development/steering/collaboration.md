---
inclusion: manual
---

# Collaboration Features

For team projects, establish collaboration workflows.

## Multi-User Workflow

### Code Review Checkpoints

- **Module 4**: Review transformation logic before committing
- **Module 6**: Review single-source loading programs before testing
- **Module 7**: Review multi-source orchestration before production
- **Module 8**: Review query logic and UAT results before deployment
- **Module 12**: Review deployment configuration before production

### Git Branching Strategy

```bash
# Feature branches for each data source
git checkout -b feature/customer-crm-mapping
# Work on transformation
git add src/transform/transform_customer_crm.py
git commit -m "Add customer CRM transformation"
git push origin feature/customer-crm-mapping
# Create pull request for review
```

### Documentation Standards

- All programs must have docstrings
- README updated with setup instructions
- Mapping decisions documented in docs/
- Code comments for complex logic

## Handoff Procedures

Create `docs/handoff_checklist.md`:

```markdown
# Project Handoff Checklist

## Knowledge Transfer
- [ ] Business problem explained
- [ ] Data sources documented
- [ ] Transformation logic reviewed
- [ ] Loading procedures demonstrated
- [ ] Query programs explained

## Access and Credentials
- [ ] Repository access granted
- [ ] Database credentials shared (securely)
- [ ] API keys transferred
- [ ] Environment setup documented

## Documentation Review
- [ ] README.md complete
- [ ] All docs/ files up to date
- [ ] Code comments adequate
- [ ] Known issues documented

## Testing and Validation
- [ ] All tests passing
- [ ] Sample queries demonstrated
- [ ] Performance benchmarks shared
- [ ] Data quality validated

## Ongoing Support
- [ ] Contact information provided
- [ ] Support schedule defined
- [ ] Escalation procedures documented
```

## Team Communication

### Daily Standup Topics
- Which data sources are being worked on
- Any blockers or data quality issues
- Transformation or loading progress
- Query results and insights

### Weekly Review Topics
- Overall project progress
- Data quality trends
- Performance metrics
- Lessons learned

## Pair Programming

For complex transformations or queries:
- One person writes code, other reviews
- Switch roles regularly
- Document decisions made during pairing
- Commit frequently with clear messages

## Knowledge Sharing

### Documentation
- Maintain up-to-date README
- Document all design decisions
- Create runbooks for common operations
- Share lessons learned

### Code Reviews
- Review all transformation logic
- Verify data quality checks
- Ensure error handling is robust
- Check for security issues

## When to Load This Guide

Load this steering file when:
- Working on team projects
- User asks about collaboration or handoffs
- Setting up code review processes
- Preparing for knowledge transfer
- Onboarding new team members
