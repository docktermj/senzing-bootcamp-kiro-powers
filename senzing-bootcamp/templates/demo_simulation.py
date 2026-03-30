#!/usr/bin/env python3
"""
Senzing Boot Camp - Module 0 Simulation Demo

This demo simulates entity resolution without requiring Senzing SDK installation.
Use this when the SDK hasn't been installed yet.

IMPORTANT: This is a SIMULATION showing what Senzing would do.
For the real Senzing SDK demo, install the SDK via Module 0 first.

Author: Senzing Boot Camp
Version: 0.1.0
Date: 2026-03-26
"""

import json
import sys
from typing import List, Dict, Any


class EntityResolutionSimulator:
    """Simulates Senzing entity resolution with pre-computed results."""
    
    def __init__(self):
        self.records = []
        self.entities = []
    
    def load_sample_data(self, dataset: str = "las_vegas") -> List[Dict[str, Any]]:
        """
        Load sample records for demonstration.
        
        Args:
            dataset: Dataset name (las_vegas, london, moscow)
        
        Returns:
            List of sample records
        """
        # Sample records showing obvious duplicates
        records = [
            {
                "RECORD_ID": "1",
                "DATA_SOURCE": "CRM_SYSTEM",
                "NAME_FULL": "John Smith",
                "ADDR_FULL": "123 Main St, Las Vegas, NV 89101",
                "PHONE_NUMBER": "(555) 123-4567",
                "EMAIL_ADDRESS": "john.smith@email.com"
            },
            {
                "RECORD_ID": "2",
                "DATA_SOURCE": "SUPPORT_SYSTEM",
                "NAME_FULL": "J. Smith",
                "ADDR_FULL": "123 Main Street, Las Vegas, NV 89101",
                "PHONE_NUMBER": "555-123-4567",
                "EMAIL_ADDRESS": "jsmith@email.com"
            },
            {
                "RECORD_ID": "3",
                "DATA_SOURCE": "SALES_SYSTEM",
                "NAME_FULL": "John R Smith",
                "ADDR_FULL": "123 Main St Apt 1, Las Vegas, NV 89101",
                "PHONE_NUMBER": "(555) 123-4567",
                "EMAIL_ADDRESS": "john.smith@email.com"
            },
            {
                "RECORD_ID": "4",
                "DATA_SOURCE": "CRM_SYSTEM",
                "NAME_FULL": "Jane Doe",
                "ADDR_FULL": "456 Oak Ave, Las Vegas, NV 89102",
                "PHONE_NUMBER": "(555) 987-6543",
                "EMAIL_ADDRESS": "jane.doe@email.com"
            },
            {
                "RECORD_ID": "5",
                "DATA_SOURCE": "SUPPORT_SYSTEM",
                "NAME_FULL": "Jane M. Doe",
                "ADDR_FULL": "456 Oak Avenue, Las Vegas, NV 89102",
                "PHONE_NUMBER": "555-987-6543",
                "EMAIL_ADDRESS": "jane.doe@email.com"
            }
        ]
        
        self.records = records
        return records
    
    def simulate_resolution(self) -> List[Dict[str, Any]]:
        """
        Simulate entity resolution with pre-computed results.
        This shows what Senzing would produce.
        
        Returns:
            List of resolved entities with match explanations
        """
        # Pre-computed resolution results (what Senzing would produce)
        entities = [
            {
                "ENTITY_ID": 1,
                "ENTITY_NAME": "John Smith",
                "RECORD_IDS": ["1", "2", "3"],
                "RECORDS": [self.records[0], self.records[1], self.records[2]],
                "MATCH_EXPLANATIONS": [
                    {
                        "RECORD_1": "1",
                        "RECORD_2": "2",
                        "FEATURES": {
                            "NAME_SIMILARITY": 92,
                            "ADDRESS_MATCH": 100,
                            "PHONE_MATCH": 100
                        },
                        "CONFIDENCE": 98,
                        "MATCH_LEVEL": "STRONG MATCH",
                        "EXPLANATION": "Same person with name abbreviation (John Smith ≈ J. Smith)"
                    },
                    {
                        "RECORD_1": "1",
                        "RECORD_2": "3",
                        "FEATURES": {
                            "NAME_SIMILARITY": 95,
                            "ADDRESS_MATCH": 95,
                            "PHONE_MATCH": 100,
                            "EMAIL_MATCH": 100
                        },
                        "CONFIDENCE": 99,
                        "MATCH_LEVEL": "STRONG MATCH",
                        "EXPLANATION": "Same person with middle initial (John Smith ≈ John R Smith)"
                    },
                    {
                        "RECORD_1": "2",
                        "RECORD_2": "3",
                        "FEATURES": {
                            "NAME_SIMILARITY": 90,
                            "ADDRESS_MATCH": 95,
                            "PHONE_MATCH": 100
                        },
                        "CONFIDENCE": 96,
                        "MATCH_LEVEL": "STRONG MATCH",
                        "EXPLANATION": "Same person (J. Smith ≈ John R Smith)"
                    }
                ]
            },
            {
                "ENTITY_ID": 2,
                "ENTITY_NAME": "Jane Doe",
                "RECORD_IDS": ["4", "5"],
                "RECORDS": [self.records[3], self.records[4]],
                "MATCH_EXPLANATIONS": [
                    {
                        "RECORD_1": "4",
                        "RECORD_2": "5",
                        "FEATURES": {
                            "NAME_SIMILARITY": 96,
                            "ADDRESS_MATCH": 100,
                            "PHONE_MATCH": 100,
                            "EMAIL_MATCH": 100
                        },
                        "CONFIDENCE": 99,
                        "MATCH_LEVEL": "STRONG MATCH",
                        "EXPLANATION": "Same person with middle initial (Jane Doe ≈ Jane M. Doe)"
                    }
                ]
            }
        ]
        
        self.entities = entities
        return entities


def print_header(text: str, char: str = "="):
    """Print a formatted header."""
    width = 80
    print()
    print(char * width)
    print(text.center(width))
    print(char * width)
    print()


def print_section(text: str):
    """Print a section divider."""
    print()
    print("─" * 80)
    print(text)
    print("─" * 80)


def print_record(record: Dict[str, Any], prefix: str = ""):
    """Print a formatted record."""
    print(f"{prefix}Record {record['RECORD_ID']} ({record['DATA_SOURCE']}):")
    print(f"{prefix}  Name:    {record['NAME_FULL']}")
    print(f"{prefix}  Address: {record['ADDR_FULL']}")
    print(f"{prefix}  Phone:   {record['PHONE_NUMBER']}")
    if 'EMAIL_ADDRESS' in record:
        print(f"{prefix}  Email:   {record['EMAIL_ADDRESS']}")
    print()


def print_match_explanation(explanation: Dict[str, Any], prefix: str = ""):
    """Print a formatted match explanation."""
    rec1 = explanation['RECORD_1']
    rec2 = explanation['RECORD_2']
    features = explanation['FEATURES']
    confidence = explanation['CONFIDENCE']
    level = explanation['MATCH_LEVEL']
    
    print(f"{prefix}Record {rec1} ↔ Record {rec2}:")
    
    for feature, score in features.items():
        feature_name = feature.replace('_', ' ').title()
        print(f"{prefix}  ✓ {feature_name}: {score}%")
    
    print(f"{prefix}  ✓ Overall confidence: {confidence}% - {level}")
    print(f"{prefix}  → {explanation['EXPLANATION']}")
    print()


def run_demo():
    """Run the simulation demo."""
    
    # Print disclaimer
    print_header("⚠️  SIMULATION DEMO  ⚠️", "=")
    print("This is a SIMULATION showing what Senzing entity resolution would do.")
    print("This demo uses pre-computed results to demonstrate the concepts.")
    print()
    print("For the REAL Senzing SDK demo:")
    print("  • Install the SDK via Module 0 (SDK Setup)")
    print("  • You'll see the real SDK in Module 6")
    print()
    input("Press Enter to continue with the simulation...")
    
    # Initialize simulator
    simulator = EntityResolutionSimulator()
    
    # Step 1: Load sample data
    print_header("Step 1: Loading Sample Records")
    print("Loading 5 sample customer records...")
    records = simulator.load_sample_data("las_vegas")
    print(f"✓ Loaded {len(records)} records")
    
    # Show records BEFORE resolution
    print_section("BEFORE Entity Resolution - 5 Separate Records")
    print("Notice the duplicates? Let's see if Senzing agrees!")
    print()
    
    for record in records:
        print_record(record)
    
    print("Can you spot the duplicates?")
    print("  • Records 1, 2, 3 look like the same person (John Smith)")
    print("  • Records 4, 5 look like the same person (Jane Doe)")
    print()
    input("Press Enter to run entity resolution...")
    
    # Step 2: Simulate resolution
    print_header("Step 2: Running Entity Resolution")
    print("Simulating Senzing entity resolution...")
    print("  [1/3] Parsing and standardizing features...")
    print("  [2/3] Comparing records and calculating match scores...")
    print("  [3/3] Resolving entities...")
    print("✓ Entity resolution complete")
    
    entities = simulator.simulate_resolution()
    
    # Step 3: Show results
    print_header("Step 3: Results Summary")
    
    total_records = len(records)
    total_entities = len(entities)
    duplicates_found = total_records - total_entities
    match_rate = (duplicates_found / total_records) * 100
    avg_records_per_entity = total_records / total_entities
    
    print(f"Records loaded:              {total_records}")
    print(f"Entities created:            {total_entities}")
    print(f"Duplicates found:            {duplicates_found} ({match_rate:.0f}% match rate)")
    print(f"Average records per entity:  {avg_records_per_entity:.2f}")
    
    # Step 4: Show resolved entities
    print_section("AFTER Entity Resolution - Resolved Entities")
    
    for entity in entities:
        print()
        print(f"Entity {entity['ENTITY_ID']}: {entity['ENTITY_NAME']}")
        print(f"Records matched: {len(entity['RECORDS'])}")
        print()
        
        for record in entity['RECORDS']:
            print_record(record, prefix="  ")
    
    # Step 5: Show match explanations
    print_header("Step 4: Match Explanations")
    print("WHY did these records match? Let's see the details...")
    print()
    
    for entity in entities:
        print(f"Entity {entity['ENTITY_ID']}: {entity['ENTITY_NAME']}")
        print()
        
        for explanation in entity['MATCH_EXPLANATIONS']:
            print_match_explanation(explanation, prefix="  ")
    
    # Step 6: Key insights
    print_header("Key Insights")
    print("✓ Senzing automatically recognized duplicates - no manual rules required")
    print()
    print("✓ Different data formats handled automatically:")
    print("    • Phone: (555) 123-4567 ≈ 555-123-4567")
    print("    • Address: Main St ≈ Main Street")
    print("    • Name: J. Smith ≈ John Smith")
    print()
    print("✓ Confidence scores show match strength (98-99% = very confident)")
    print()
    print("✓ This happened in real-time as records were loaded")
    print()
    print("✓ No training data or manual rules were required")
    
    # Step 7: Connect to user's use case
    print_header("What This Means for Your Data")
    print("Now imagine this with YOUR data:")
    print()
    print("  • Instead of these 5 sample records, you'd have thousands or millions")
    print("  • Instead of customer records, you'd have your specific data")
    print("  • The same process would find duplicates across your systems")
    print("  • You'd get a unified view of your entities")
    print()
    print("What you just saw is exactly how Senzing will work with your data!")
    
    # Final message
    print_header("Demo Complete! 🎉")
    print("You've seen how entity resolution works!")
    print()
    print("Next steps:")
    print("  • Continue to Module 2 to work with your own data")
    print("  • Or install the SDK (Module 0) to see the real demo")
    print("  • You'll see the real SDK in action in Module 6")
    print()
    print("Remember: This was a SIMULATION. The real Senzing SDK:")
    print("  • Handles millions of records")
    print("  • Learns from your data")
    print("  • Provides even more detailed match explanations")
    print("  • Supports real-time updates and queries")
    print()


def main():
    """Main entry point."""
    try:
        run_demo()
        return 0
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n\nError running demo: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
