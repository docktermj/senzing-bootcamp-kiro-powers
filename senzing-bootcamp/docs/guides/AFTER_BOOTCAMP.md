# What to Do After the Bootcamp

Congratulations — you did it! You've worked through the Senzing Bootcamp and built a working entity resolution pipeline from the ground up. You understand your data, you've mapped and loaded it, validated results, and (if you went the full route) hardened, monitored, and packaged your deployment. That's a serious accomplishment.

This guide covers what comes next: keeping your system healthy, scaling when you need to, adding new data, staying current, and exploring advanced topics.

---

## Production Maintenance Cadence

A running Senzing deployment needs regular attention. Here's a practical schedule to keep things humming.

### Daily

- [ ] Review monitoring dashboards (Module 11 setup)
- [ ] Check error logs for new SENZ errors — use `explain_error_code` to diagnose
- [ ] Verify database backups completed successfully
- [ ] Confirm loading jobs (if scheduled) ran without failures

### Weekly

- [ ] Review entity resolution statistics — look for unexpected changes in entity counts
- [ ] Check database growth trends (disk usage, table sizes)
- [ ] Process redo records — use `search_docs(query='redo processing', version='current')` for guidance
- [ ] Review and rotate any expiring credentials

### Monthly

- [ ] Rotate secrets and API keys (Module 10 practices)
- [ ] Update SDK and dependencies to latest patch versions
- [ ] Review alert thresholds — adjust for current data volumes
- [ ] Run database maintenance:
  - PostgreSQL: `VACUUM ANALYZE` on Senzing tables
  - SQLite: `PRAGMA optimize;`
- [ ] Review and archive old logs

### Quarterly

- [ ] Run a disaster recovery test — restore from backup and verify
- [ ] Conduct a security audit (Module 10 checklist)
- [ ] Capacity planning review — project growth for next quarter
- [ ] Review Senzing release notes for new features
- [ ] Update documentation to reflect any changes

---

## Scaling Your Deployment

### Signs You've Outgrown Your Current Setup

Watch for these indicators:

- **Loading throughput dropping** — records per second declining over time
- **Query latency increasing** — searches taking noticeably longer
- **Disk filling up** — database storage approaching capacity
- **Memory pressure** — out-of-memory errors or excessive swapping
- **Redo queue growing** — redo records accumulating faster than they're processed

### How to Scale

Start with the easiest wins and work up:

1. **Database tuning** — PostgreSQL shared_buffers, work_mem, effective_cache_size
2. **Multi-threaded loading** — increase loader thread count for higher throughput
3. **Connection pooling** — reduce database connection overhead
4. **Read replicas** — offload query traffic from the primary database
5. **Horizontal scaling** — distribute loading across multiple processes or machines

Use `search_docs(query='performance tuning', version='current')` for current best practices and specific configuration recommendations.

### When to Move from SQLite to PostgreSQL

If you started with SQLite for evaluation, consider migrating to PostgreSQL when:

- Your dataset exceeds 100K records
- You need concurrent access (multiple loaders or query processes)
- You're moving toward production deployment

Module 2 covers database setup. Re-run it with PostgreSQL as your target. If you're deploying to a cloud provider, Module 11 can provision a managed database (e.g., RDS/Aurora for AWS via CDK).

### Deployment and Redeployment

Module 11 separates **packaging** (containerization, config, CI/CD — always done) from **deployment** (actually deploying to a target — optional). If you packaged during the bootcamp but didn't deploy, you can return to Module 11 Phase 2 at any time. Your deployment target (AWS, Azure, GCP, on-premises, local) shapes what artifacts are produced — if you change targets, re-run Module 11 from Step 1.

---

## Adding New Data Sources

When new data becomes available, follow the same proven workflow from the bootcamp:

### Step-by-Step

1. **Collect the data** — Follow Module 4 to gather and document the new source
2. **Evaluate quality** — Run Module 5's quality scoring. Use the iterate-vs-proceed gate: ≥80% proceed, 70-79% consider improving, <70% fix first.
3. **Map the data** — Use Module 5's `mapping_workflow` to get correct Senzing attribute names (don't guess). Mapping state is checkpointed to `config/mapping_state_[datasource].json` — if your session ends mid-mapping, you can resume where you left off.
4. **Test with a sample** — Load 100-1000 records first and verify resolution behavior
5. **Load the full dataset** — Follow Module 6 for single-source loading
6. **Monitor cross-source resolution** — After loading, check how the new source resolves against existing data. If entity resolution found zero matches, investigate: are key fields populated? Were they mapped correctly?

### Tips

- Always test with small samples before full loads
- Use `analyze_record` to validate your mapped data before loading
- Document the new source in your project's data source inventory
- Watch entity counts before and after — a new source should increase resolved entities, not just raw record counts

---

## Keeping Senzing Updated

### Check for Updates

Use `get_capabilities` to see the current Senzing version and available tools. Compare against your installed version.

### Migration Between Major Versions

Use `get_sdk_reference(topic='migration')` for detailed V3→V4 migration guidance, including:

- Renamed functions and methods
- Changed flags and parameters
- Removed APIs and their replacements
- Breaking changes to watch for

### Upgrade Safely

1. **Read the release notes** — use `search_docs(query='release notes', version='current')`
2. **Test in staging first** — never upgrade production without testing
3. **Back up your database** before upgrading
4. **Run your validation queries** (Module 8) after upgrading to confirm results are consistent
5. **Update your code** for any API changes flagged by the migration guide

---

## Advanced Topics to Explore

Once you're comfortable with the basics, there's a lot more to dig into.

### Custom Matching Rules and Thresholds

Senzing's default matching works well for most cases, but you can tune it:

- Adjust match thresholds for your specific data quality
- Configure custom features for domain-specific identifiers
- Use `search_docs(query='matching configuration', version='current')` for details

### Real-Time Streaming Ingestion

Move beyond batch loading to continuous data integration:

- RabbitMQ consumers for message-driven loading
- SQS consumers for AWS-native pipelines
- Kafka integration for high-throughput streaming
- Use `find_examples(query='stream loading consumer')` for working code

### REST API Patterns

Expose entity resolution as a service:

- REST API wrappers for search and query operations
- Batch API endpoints for bulk operations
- Use `find_examples(query='REST API entity resolution')` for examples

### Data Mart and Reporting Dashboards

Build analytics on top of your resolved entities:

- Export resolved data to reporting databases
- Create dashboards for entity resolution metrics
- Track resolution quality over time
- Use `reporting_guide(topic='data_mart')` and `reporting_guide(topic='dashboard')` for patterns

### Semantic Search

Explore embeddings-based candidate generation for fuzzy matching scenarios where traditional blocking may miss candidates.

- Use `search_docs(query='semantic search', version='current')` to check current support

---

## Community and Support

You're not on your own after the bootcamp.

### Documentation

- **Senzing docs**: [https://docs.senzing.com](https://docs.senzing.com)
- **MCP tools**: Use `search_docs` for any Senzing topic — it searches across all official documentation

### Support

- **Technical support**: [support@senzing.com](mailto:support@senzing.com)
- **Production licensing and sales**: [sales@senzing.com](mailto:sales@senzing.com)

### Code Examples

Use `find_examples` to discover working code across 27+ indexed Senzing GitHub repositories:

```text
"Show me examples of multi-threaded loading"
"Find examples of redo processing"
"How do other projects handle error retry?"
```

### SDK Reference

Use `get_sdk_reference` for precise method signatures, flag definitions, and API details — more reliable than searching the web.

---

## Providing Feedback

Your experience matters. If you have feedback on the bootcamp:

1. **Say "bootcamp feedback"** to the agent — it will walk you through documenting your experience
2. **Share your feedback file** at `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` with the power author

Feedback helps improve the bootcamp for everyone who comes after you.

---

## Quick Reference: MCP Tools for Ongoing Work

| Task | MCP Tool | Example |
| ---- | -------- | ------- |
| Search documentation | `search_docs` | `search_docs(query='redo processing', version='current')` |
| Diagnose errors | `explain_error_code` | `explain_error_code(error_code='0023', version='current')` |
| Map new data | `mapping_workflow` | Start with `action='start'` and your file paths |
| Validate mapped data | `analyze_record` | Pass your mapped JSONL files |
| Find code examples | `find_examples` | `find_examples(query='multi-threaded loading')` |
| SDK method reference | `get_sdk_reference` | `get_sdk_reference(topic='functions', filter='add_record')` |
| Setup guidance | `sdk_guide` | `sdk_guide(topic='install', platform='linux_apt')` |
| Generate code | `generate_scaffold` | `generate_scaffold(language='<chosen_language>', workflow='load', version='current')` |
| Reporting patterns | `reporting_guide` | `reporting_guide(topic='reports')` |
| Check capabilities | `get_capabilities` | See current version and all available tools |

---

## You're Ready

You've got the knowledge, the tools, and a working system. Whether you're maintaining what you've built, scaling it up, or expanding with new data sources — you know the workflow and you've got the MCP tools to back you up.

Go build something great.

---

**Version**: 1.0.0
**Last updated**: 2026-04-01
