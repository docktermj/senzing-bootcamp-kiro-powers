---
inclusion: manual
---

# Cost Estimation and ROI Calculator

## Overview

This guide helps estimate Senzing licensing costs, infrastructure costs, and ROI for entity resolution projects.

## Senzing Licensing Model

Senzing uses a **Data Source Record (DSR)** pricing model:

- **DSR**: A unique record from a data source
- **License tiers**: Based on total DSRs across all sources
- **Pricing**: Volume-based with discounts at higher tiers

### What Counts as a DSR?

✅ **Counts as DSR**:
- Each unique record in a data source
- Customer record in CRM
- Vendor record in procurement system
- Employee record in HR system
- Transaction record (if used for entity resolution)

❌ **Does NOT count as DSR**:
- Duplicate records within same source (counted once)
- Resolved entities (output of Senzing)
- Relationships between entities
- Audit logs or metadata

### Example DSR Calculation

```
Data Sources:
- CRM Customers: 500,000 records
- E-commerce Customers: 300,000 records
- Support Tickets: 200,000 records (if resolving ticket submitters)
- Vendor Database: 50,000 records

Total DSRs = 500,000 + 300,000 + 200,000 + 50,000 = 1,050,000 DSRs
```

## Licensing Tiers (Approximate)

**Note**: Contact Senzing for current pricing. These are estimates for planning.

| Tier | DSR Range | Approx. Annual Cost | Cost per DSR |
|------|-----------|---------------------|--------------|
| Evaluation | 0 - 500 | Free | $0 |
| Starter | 501 - 100K | $25K - $50K | $0.25 - $0.50 |
| Professional | 100K - 1M | $50K - $200K | $0.20 - $0.50 |
| Enterprise | 1M - 10M | $200K - $800K | $0.08 - $0.20 |
| Enterprise+ | 10M+ | Custom | $0.05 - $0.10 |

**Volume discounts**: Larger deployments get lower per-DSR costs

## Infrastructure Costs

### Database Costs

**SQLite** (Evaluation only):
- Cost: Free
- Performance: 20-50 records/sec
- Limit: < 100K records
- Use case: Development, testing

**PostgreSQL** (Recommended for production):

| Deployment | Specs | Monthly Cost | Records Supported |
|------------|-------|--------------|-------------------|
| Small | 4 vCPU, 16GB RAM, 500GB SSD | $200-400 | < 1M |
| Medium | 8 vCPU, 32GB RAM, 1TB SSD | $500-800 | 1M - 10M |
| Large | 16 vCPU, 64GB RAM, 2TB SSD | $1,000-2,000 | 10M - 50M |
| X-Large | 32 vCPU, 128GB RAM, 4TB SSD | $2,500-5,000 | 50M+ |

**Cloud Database Services**:
- AWS RDS PostgreSQL: $0.10 - $3.00/hour depending on instance
- Azure Database for PostgreSQL: Similar pricing
- GCP Cloud SQL: Similar pricing

### Compute Costs

**Application Servers**:

| Workload | Specs | Monthly Cost | Throughput |
|----------|-------|--------------|------------|
| Light | 2 vCPU, 8GB RAM | $100-200 | < 100 queries/min |
| Medium | 4 vCPU, 16GB RAM | $200-400 | 100-500 queries/min |
| Heavy | 8 vCPU, 32GB RAM | $400-800 | 500-2000 queries/min |

**Batch Processing**:
- Loading: Same as application servers
- Transformation: Can use spot instances (50-70% cheaper)

### Storage Costs

**Data Storage**:
- Raw data: $0.02 - $0.10/GB/month
- Transformed data: $0.02 - $0.10/GB/month
- Database storage: Included in database costs above
- Backups: $0.01 - $0.05/GB/month

**Example**:
- 1M records × 2KB average = 2GB raw data = $0.20/month
- Transformed: Similar
- Database: 10GB = Included
- Backups: 10GB = $0.50/month

### Monitoring and Logging

- Prometheus/Grafana (self-hosted): $50-100/month
- CloudWatch/Azure Monitor: $50-200/month
- DataDog/New Relic: $15-30/host/month
- Log aggregation: $50-500/month depending on volume

## Total Cost of Ownership (TCO)

### Example: Small Deployment (500K DSRs)

**Annual Costs**:
- Senzing license: $40,000
- Database (PostgreSQL): $4,800 ($400/month)
- Application servers: $2,400 ($200/month)
- Storage: $600 ($50/month)
- Monitoring: $1,200 ($100/month)
- **Total**: ~$49,000/year

**Per DSR**: $0.098/year

### Example: Medium Deployment (5M DSRs)

**Annual Costs**:
- Senzing license: $150,000
- Database (PostgreSQL): $9,600 ($800/month)
- Application servers: $4,800 ($400/month)
- Storage: $1,200 ($100/month)
- Monitoring: $2,400 ($200/month)
- **Total**: ~$168,000/year

**Per DSR**: $0.034/year

### Example: Large Deployment (50M DSRs)

**Annual Costs**:
- Senzing license: $500,000
- Database (PostgreSQL): $24,000 ($2,000/month)
- Application servers: $9,600 ($800/month)
- Storage: $3,600 ($300/month)
- Monitoring: $6,000 ($500/month)
- **Total**: ~$543,000/year

**Per DSR**: $0.011/year

## Development Phase Costs (Modules 1-6)

- **Time**: 3-6 hours for single data source
- **Personnel**: 1 developer
- **Infrastructure**: Minimal (local development)
  - SQLite: Free
  - Docker: Free
  - Development tools: Free

## ROI Calculator

### Cost Savings

**1. Reduced Duplicate Mailings**
```
Scenario: Marketing campaigns
- Mailings per year: 1,000,000
- Duplicate rate before: 15%
- Duplicate rate after: 2%
- Cost per mailing: $1.50

Savings = (150,000 - 20,000) × $1.50 = $195,000/year
```

**2. Fraud Prevention**
```
Scenario: Insurance claims
- Claims per year: 100,000
- Fraud rate: 5%
- Average fraudulent claim: $10,000
- Detection improvement: 30%

Savings = 100,000 × 0.05 × $10,000 × 0.30 = $1,500,000/year
```

**3. Improved Customer Service**
```
Scenario: Call center
- Calls per year: 500,000
- Time saved per call: 30 seconds
- Cost per minute: $1.00

Savings = 500,000 × 0.5 min × $1.00 = $250,000/year
```

**4. Data Quality Improvement**
```
Scenario: Data cleansing
- Manual hours saved: 2,000 hours/year
- Cost per hour: $50

Savings = 2,000 × $50 = $100,000/year
```

**5. Compliance and Risk Reduction**
```
Scenario: KYC/AML
- Reduced false positives: 80%
- Investigation time per false positive: 2 hours
- False positives per year: 10,000
- Cost per hour: $75

Savings = 10,000 × 0.80 × 2 × $75 = $1,200,000/year
```

### Revenue Opportunities

**1. Better Customer Insights**
```
Scenario: Cross-sell/upsell
- Customers: 500,000
- Improved targeting: 5% increase
- Average additional revenue: $100

Revenue = 500,000 × 0.05 × $100 = $2,500,000/year
```

**2. Faster Onboarding**
```
Scenario: New customer acquisition
- New customers per year: 50,000
- Time saved per customer: 10 minutes
- Conversion rate improvement: 2%
- Average customer value: $500

Revenue = 50,000 × 0.02 × $500 = $500,000/year
```

## ROI Calculation Template

```python
#!/usr/bin/env python3
"""
Senzing ROI Calculator
"""

class ROICalculator:
    def __init__(self):
        self.costs = {}
        self.savings = {}
        self.revenue = {}
    
    def add_cost(self, name, annual_amount):
        """Add a cost item"""
        self.costs[name] = annual_amount
    
    def add_savings(self, name, annual_amount):
        """Add a cost savings item"""
        self.savings[name] = annual_amount
    
    def add_revenue(self, name, annual_amount):
        """Add a revenue opportunity"""
        self.revenue[name] = annual_amount
    
    def calculate_roi(self):
        """Calculate ROI"""
        total_costs = sum(self.costs.values())
        total_savings = sum(self.savings.values())
        total_revenue = sum(self.revenue.values())
        
        total_benefit = total_savings + total_revenue
        net_benefit = total_benefit - total_costs
        roi_percent = (net_benefit / total_costs) * 100 if total_costs > 0 else 0
        payback_months = (total_costs / (total_benefit / 12)) if total_benefit > 0 else float('inf')
        
        return {
            'total_costs': total_costs,
            'total_savings': total_savings,
            'total_revenue': total_revenue,
            'total_benefit': total_benefit,
            'net_benefit': net_benefit,
            'roi_percent': roi_percent,
            'payback_months': payback_months
        }
    
    def print_report(self):
        """Print ROI report"""
        results = self.calculate_roi()
        
        print("\n" + "="*60)
        print("SENZING ROI ANALYSIS")
        print("="*60)
        
        print("\nCOSTS:")
        for name, amount in self.costs.items():
            print(f"  {name:<30} ${amount:>12,.0f}")
        print(f"  {'TOTAL COSTS':<30} ${results['total_costs']:>12,.0f}")
        
        print("\nSAVINGS:")
        for name, amount in self.savings.items():
            print(f"  {name:<30} ${amount:>12,.0f}")
        print(f"  {'TOTAL SAVINGS':<30} ${results['total_savings']:>12,.0f}")
        
        print("\nREVENUE OPPORTUNITIES:")
        for name, amount in self.revenue.items():
            print(f"  {name:<30} ${amount:>12,.0f}")
        print(f"  {'TOTAL REVENUE':<30} ${results['total_revenue']:>12,.0f}")
        
        print("\nRESULTS:")
        print(f"  {'Total Benefit':<30} ${results['total_benefit']:>12,.0f}")
        print(f"  {'Net Benefit':<30} ${results['net_benefit']:>12,.0f}")
        print(f"  {'ROI':<30} {results['roi_percent']:>12.1f}%")
        print(f"  {'Payback Period':<30} {results['payback_months']:>12.1f} months")
        
        print("\n" + "="*60)

# Example usage
if __name__ == '__main__':
    calc = ROICalculator()
    
    # Costs
    calc.add_cost('Senzing License', 40000)
    calc.add_cost('Database', 4800)
    calc.add_cost('Application Servers', 2400)
    calc.add_cost('Storage', 600)
    calc.add_cost('Monitoring', 1200)
    
    # Savings
    calc.add_savings('Reduced Duplicate Mailings', 195000)
    calc.add_savings('Improved Customer Service', 250000)
    calc.add_savings('Data Quality Improvement', 100000)
    
    # Revenue
    calc.add_revenue('Better Customer Insights', 500000)
    
    # Print report
    calc.print_report()
```

**Example Output**:
```
============================================================
SENZING ROI ANALYSIS
============================================================

COSTS:
  Senzing License                $       40,000
  Database                       $        4,800
  Application Servers            $        2,400
  Storage                        $          600
  Monitoring                     $        1,200
  TOTAL COSTS                    $       49,000

SAVINGS:
  Reduced Duplicate Mailings     $      195,000
  Improved Customer Service      $      250,000
  Data Quality Improvement       $      100,000
  TOTAL SAVINGS                  $      545,000

REVENUE OPPORTUNITIES:
  Better Customer Insights       $      500,000
  TOTAL REVENUE                  $      500,000

RESULTS:
  Total Benefit                  $    1,045,000
  Net Benefit                    $      996,000
  ROI                                   2,033.7%
  Payback Period                            0.6 months

============================================================
```

## Quick Estimator

### Step 1: Count Your DSRs

```
Data Source 1: __________ records
Data Source 2: __________ records
Data Source 3: __________ records
...

Total DSRs: __________
```

### Step 2: Estimate Costs

Use the tables above to estimate:
- Senzing license: $__________
- Infrastructure: $__________
- Total annual cost: $__________

### Step 3: Estimate Benefits

Pick 2-3 benefits that apply to your use case:
- Benefit 1: $__________
- Benefit 2: $__________
- Benefit 3: $__________
- Total annual benefit: $__________

### Step 4: Calculate ROI

```
ROI = (Total Benefit - Total Cost) / Total Cost × 100%
Payback = Total Cost / (Total Benefit / 12) months
```

## Cost Optimization Tips

1. Start with SQLite for evaluation (free)
2. Use spot instances for batch processing (70% savings)
3. Implement data retention policies (reduce storage)
4. Optimize queries to reduce compute time
5. Use reserved instances for production (40% savings)

## Agent Behavior

When helping users with cost estimation in Module 1:

1. **Count DSRs** across all identified data sources
2. **Estimate license tier** based on total DSRs
3. **Estimate infrastructure** based on workload
4. **Identify applicable benefits** from their use case
5. **Calculate ROI** using the template
6. **Generate cost report** in `docs/cost_estimate.md`
7. **Discuss with user** to validate assumptions

## When to Load This Guide

Load this guide when:
- Starting Module 1 (business problem definition)
- User asks about costs or pricing
- Planning production deployment (Module 5 or Module 12)
- Justifying project to stakeholders
- Comparing build vs buy options
- Preparing business case or ROI analysis

## Version History

- **v3.0.0** (2026-03-17): Consolidated cost calculator and estimation guide
