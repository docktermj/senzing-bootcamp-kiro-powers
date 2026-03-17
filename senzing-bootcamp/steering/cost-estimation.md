# Cost Estimation

Understand the costs involved in your entity resolution project.

## Development Phase (Modules 1-6)

- **Time**: 3-6 hours for single data source
- **Personnel**: 1 developer
- **Infrastructure**: Minimal (local development)
  - SQLite: Free
  - Docker: Free
  - Development tools: Free

## Production Deployment

### Option 1: On-Premise

**One-time costs**:
- Senzing license: [Contact Senzing for pricing]
- Server hardware: $5,000 - $20,000
- Setup and configuration: 40-80 hours

**Ongoing costs**:
- Maintenance: 10-20 hours/month
- Hardware refresh: $2,000/year
- Power and cooling: $500/month

### Option 2: Cloud (AWS example)

**Monthly costs** (estimated for 1M records):
- EC2 instance (m5.2xlarge): $280/month
- RDS PostgreSQL (db.m5.large): $200/month
- EBS storage (500 GB): $50/month
- Data transfer: $50/month
- **Total**: ~$580/month

**Scaling costs** (10M records):
- EC2 instance (m5.4xlarge): $560/month
- RDS PostgreSQL (db.m5.2xlarge): $400/month
- EBS storage (2 TB): $200/month
- Data transfer: $100/month
- **Total**: ~$1,260/month

### Senzing Licensing

Contact Senzing for pricing based on:
- Number of records
- Number of data sources
- Deployment type (on-premise vs cloud)
- Support level

## Cost Optimization Tips

1. Start with SQLite for evaluation (free)
2. Use spot instances for batch processing (70% savings)
3. Implement data retention policies (reduce storage)
4. Optimize queries to reduce compute time
5. Use reserved instances for production (40% savings)

## ROI Considerations

**Benefits**:
- Reduced duplicate records → Cost savings
- Improved data quality → Better decisions
- Faster customer lookup → Improved service
- Fraud detection → Loss prevention

**Example ROI**:
- Duplicate mailings eliminated: $50,000/year saved
- Fraud prevented: $200,000/year saved
- Customer service efficiency: 20% improvement
- **Total benefit**: $250,000+/year
- **Cost**: $20,000/year
- **ROI**: 1,150%

## Cost Estimation Document

Create `docs/cost_estimation.md` with your specific estimates based on:
- Your data volume
- Your deployment choice
- Your team size
- Your expected benefits

## When to Load This Guide

Load this steering file when:
- Starting Module 1 (during problem definition)
- Starting Module 5 (choosing deployment option)
- Starting Module 12 (deployment planning)
- User asks about costs or pricing
- Planning production deployment

**Note**: See also `steering/cost-calculator.md` for detailed ROI calculator and DSR pricing.
- Preparing business case or ROI analysis
