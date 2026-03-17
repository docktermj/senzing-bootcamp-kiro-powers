#!/usr/bin/env python3
"""
Senzing Cost Calculator

Estimates costs for Senzing deployment based on data volume and requirements.

Usage:
    python cost_calculator.py --interactive
    python cost_calculator.py --records 1000000 --sources 3 --frequency daily
"""

import argparse
import sys


class CostCalculator:
    """Calculate Senzing deployment costs"""

    # Pricing estimates (adjust based on actual Senzing pricing)
    DSR_COST_PER_MILLION = 100  # Example: $100 per million DSRs
    INFRASTRUCTURE_BASE = 500  # Base monthly infrastructure cost
    INFRASTRUCTURE_PER_MILLION = 50  # Additional cost per million records

    def __init__(self):
        self.records = 0
        self.sources = 0
        self.update_frequency = 'static'
        self.deployment_type = 'cloud'
        self.performance_tier = 'standard'

    def calculate_dsrs(self) -> int:
        """Calculate Data Source Records (DSRs)"""
        # DSR = total records across all sources
        return self.records * self.sources

    def calculate_dsr_cost(self) -> float:
        """Calculate DSR licensing cost"""
        dsrs = self.calculate_dsrs()
        dsr_millions = dsrs / 1_000_000
        return dsr_millions * self.DSR_COST_PER_MILLION

    def calculate_infrastructure_cost(self) -> float:
        """Calculate monthly infrastructure cost"""
        base = self.INFRASTRUCTURE_BASE

        # Add cost based on data volume
        record_millions = (self.records * self.sources) / 1_000_000
        volume_cost = record_millions * self.INFRASTRUCTURE_PER_MILLION

        # Adjust for deployment type
        if self.deployment_type == 'on-premise':
            multiplier = 1.5  # Higher upfront, lower ongoing
        else:
            multiplier = 1.0

        # Adjust for performance tier
        if self.performance_tier == 'high':
            multiplier *= 2.0
        elif self.performance_tier == 'premium':
            multiplier *= 3.0

        return (base + volume_cost) * multiplier

    def calculate_time_estimate(self) -> dict:
        """Estimate implementation time"""
        # Base time per module (hours)
        base_time = {
            'setup': 2,
            'mapping_per_source': 2,
            'loading_per_source': 1,
            'testing': 4,
            'deployment': 8
        }

        total_mapping = base_time['mapping_per_source'] * self.sources
        total_loading = base_time['loading_per_source'] * self.sources

        total_hours = (
            base_time['setup'] +
            total_mapping +
            total_loading +
            base_time['testing'] +
            base_time['deployment']
        )

        return {
            'total_hours': total_hours,
            'total_days': total_hours / 8,
            'total_weeks': total_hours / 40
        }

    def generate_report(self):
        """Generate cost estimate report"""
        dsrs = self.calculate_dsrs()
        dsr_cost = self.calculate_dsr_cost()
        infra_cost = self.calculate_infrastructure_cost()
        time_est = self.calculate_time_estimate()

        print("\n" + "="*60)
        print("SENZING COST ESTIMATE")
        print("="*60)

        print("\nProject Parameters:")
        print(f"  Records per source: {self.records:,}")
        print(f"  Number of sources: {self.sources}")
        print(f"  Total DSRs: {dsrs:,}")
        print(f"  Update frequency: {self.update_frequency}")
        print(f"  Deployment type: {self.deployment_type}")
        print(f"  Performance tier: {self.performance_tier}")

        print("\nCost Breakdown:")
        print(f"  DSR Licensing: ${dsr_cost:,.2f}")
        print(f"  Infrastructure (monthly): ${infra_cost:,.2f}")
        print(f"  Infrastructure (annual): ${infra_cost * 12:,.2f}")

        print(f"\nTotal First Year Cost: ${dsr_cost + (infra_cost * 12):,.2f}")

        print("\nTime Estimate:")
        print(f"  Total hours: {time_est['total_hours']:.0f}")
        print(f"  Total days: {time_est['total_days']:.1f}")
        print(f"  Total weeks: {time_est['total_weeks']:.1f}")

        print("\nBreakdown by Phase:")
        print(f"  Setup & Planning: 2 hours")
        print(f"  Data Mapping: {2 * self.sources} hours ({self.sources} sources)")
        print(f"  Data Loading: {1 * self.sources} hours ({self.sources} sources)")
        print(f"  Testing & Validation: 4 hours")
        print(f"  Deployment: 8 hours")

        print("\n" + "="*60)
        print("NOTES")
        print("="*60)
        print("- Costs are estimates and may vary")
        print("- Contact Senzing for accurate pricing")
        print("- Time estimates assume experienced developer")
        print("- Add 50% time for first-time users")
        print("="*60)


def interactive_mode():
    """Interactive cost calculator"""
    calc = CostCalculator()

    print("\n" + "="*60)
    print("SENZING COST CALCULATOR - INTERACTIVE MODE")
    print("="*60)

    # Get inputs
    calc.records = int(input("\nRecords per data source: "))
    calc.sources = int(input("Number of data sources: "))

    print("\nUpdate frequency:")
    print("  1. Static (one-time load)")
    print("  2. Daily updates")
    print("  3. Real-time streaming")
    freq_choice = input("Choice (1-3): ")
    freq_map = {'1': 'static', '2': 'daily', '3': 'realtime'}
    calc.update_frequency = freq_map.get(freq_choice, 'static')

    print("\nDeployment type:")
    print("  1. Cloud (AWS, Azure, GCP)")
    print("  2. On-premise")
    deploy_choice = input("Choice (1-2): ")
    calc.deployment_type = 'cloud' if deploy_choice == '1' else 'on-premise'

    print("\nPerformance tier:")
    print("  1. Standard (< 100 records/sec)")
    print("  2. High (100-500 records/sec)")
    print("  3. Premium (500+ records/sec)")
    perf_choice = input("Choice (1-3): ")
    perf_map = {'1': 'standard', '2': 'high', '3': 'premium'}
    calc.performance_tier = perf_map.get(perf_choice, 'standard')

    # Generate report
    calc.generate_report()


def main():
    parser = argparse.ArgumentParser(description='Senzing cost calculator')

    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    parser.add_argument('--records', type=int, help='Records per source')
    parser.add_argument('--sources', type=int, help='Number of sources')
    parser.add_argument(
        '--frequency',
        choices=['static', 'daily', 'realtime'],
        help='Update frequency'
    )
    parser.add_argument(
        '--deployment',
        choices=['cloud', 'on-premise'],
        default='cloud'
    )
    parser.add_argument(
        '--performance',
        choices=['standard', 'high', 'premium'],
        default='standard'
    )

    args = parser.parse_args()

    if args.interactive:
        interactive_mode()
    elif args.records and args.sources:
        calc = CostCalculator()
        calc.records = args.records
        calc.sources = args.sources
        calc.update_frequency = args.frequency or 'static'
        calc.deployment_type = args.deployment
        calc.performance_tier = args.performance
        calc.generate_report()
    else:
        print("Use --interactive or provide --records and --sources")
        sys.exit(1)


if __name__ == '__main__':
    main()
