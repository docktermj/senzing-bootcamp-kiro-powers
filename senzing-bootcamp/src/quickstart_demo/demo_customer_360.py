#!/usr/bin/env python3
"""
Customer 360 Quick Demo

Demonstrates customer deduplication and unified view using Senzing.
Shows how multiple customer records from different systems can be resolved
into a single, comprehensive customer profile.

Use Case: Customer 360 / Customer Master Data Management
Pattern: Deduplication across CRM, e-commerce, support systems

Time: 10-15 minutes
"""

import json
import sys
from pathlib import Path

try:
    from senzing import G2Engine, G2Exception
except ImportError:
    print("ERROR: Senzing SDK not installed")
    print("Install with: pip install senzing")
    sys.exit(1)


# Sample customer data showing duplicates across systems
CUSTOMER_DATA = [
    # CRM System - Original record
    {
        "DATA_SOURCE": "CRM",
        "RECORD_ID": "CRM-1001",
        "NAME_FULL": "John Smith",
        "EMAIL_ADDRESS": "john.smith@email.com",
        "PHONE_NUMBER": "555-1234",
        "ADDR_FULL": "123 Main St, Springfield, IL 62701"
    },
    # E-commerce System - Same person, slight name variation
    {
        "DATA_SOURCE": "ECOMMERCE",
        "RECORD_ID": "ECOM-5432",
        "NAME_FULL": "J. Smith",
        "EMAIL_ADDRESS": "john.smith@email.com",
        "PHONE_NUMBER": "555-1234",
        "ADDR_FULL": "123 Main Street, Springfield, IL 62701"
    },
    # Support System - Same person, nickname
    {
        "DATA_SOURCE": "SUPPORT",
        "RECORD_ID": "SUP-9876",
        "NAME_FULL": "Johnny Smith",
        "EMAIL_ADDRESS": "jsmith@email.com",
        "PHONE_NUMBER": "555-1234",
        "ADDR_FULL": "123 Main St, Springfield, Illinois 62701"
    },
    # Different customer - should NOT match
    {
        "DATA_SOURCE": "CRM",
        "RECORD_ID": "CRM-1002",
        "NAME_FULL": "Jane Smith",
        "EMAIL_ADDRESS": "jane.smith@email.com",
        "PHONE_NUMBER": "555-5678",
        "ADDR_FULL": "456 Oak Ave, Chicago, IL 60601"
    }
]


def print_header(text):
    """Print formatted section header"""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}\n")


def print_record(record, label="Record"):
    """Print formatted record"""
    print(f"{label}:")
    print(f"  Source: {record.get('DATA_SOURCE')}")
    print(f"  ID: {record.get('RECORD_ID')}")
    print(f"  Name: {record.get('NAME_FULL')}")
    print(f"  Email: {record.get('EMAIL_ADDRESS')}")
    print(f"  Phone: {record.get('PHONE_NUMBER')}")
    print(f"  Address: {record.get('ADDR_FULL')}")
    print()


def run_demo(config_json):
    """Run Customer 360 demo"""
    
    print_header("Customer 360 Quick Demo")
    print("This demo shows how Senzing resolves duplicate customer records")
    print("across multiple systems (CRM, E-commerce, Support) into a unified view.")
    print()
    
    # Initialize Senzing
    print("Initializing Senzing...")
    g2_engine = G2Engine()
    
    try:
        g2_engine.init("CustomerDemo", config_json, False)
        print("✓ Senzing initialized\n")
    except G2Exception as e:
        print(f"ERROR: Failed to initialize Senzing: {e}")
        return 1
    
    try:
        # Step 1: Load customer records
        print_header("Step 1: Loading Customer Records")
        print(f"Loading {len(CUSTOMER_DATA)} customer records from 3 systems...\n")
        
        for i, record in enumerate(CUSTOMER_DATA, 1):
            print_record(record, f"Loading Record {i}/{len(CUSTOMER_DATA)}")
            g2_engine.addRecord(
                record["DATA_SOURCE"],
                record["RECORD_ID"],
                json.dumps(record)
            )
        
        print("✓ All records loaded\n")
        
        # Step 2: Show resolution results
        print_header("Step 2: Resolution Results")
        print("Senzing automatically resolved the records. Let's see the results...\n")
        
        # Get entity for first record
        response = bytearray()
        g2_engine.getEntityByRecordID("CRM", "CRM-1001", response)
        entity = json.loads(response.decode())
        
        resolved_records = entity.get("RESOLVED_ENTITY", {}).get("RECORDS", [])
        
        print(f"Entity ID: {entity.get('RESOLVED_ENTITY', {}).get('ENTITY_ID')}")
        print(f"Records Resolved: {len(resolved_records)}")
        print()
        
        print("Resolved Records:")
        for record in resolved_records:
            print(f"  • {record['DATA_SOURCE']}:{record['RECORD_ID']}")
        print()
        
        # Step 3: Show unified customer view
        print_header("Step 3: Unified Customer View")
        print("Senzing created a comprehensive profile from all matching records:\n")
        
        # Show best values
        resolved = entity.get("RESOLVED_ENTITY", {})
        print("Best Name:", resolved.get("ENTITY_NAME"))
        
        # Show all names found
        name_data = resolved.get("NAME_DATA", [])
        if name_data:
            print("\nAll Name Variations:")
            for name in name_data:
                print(f"  • {name}")
        
        # Show all contact info
        address_data = resolved.get("ADDRESS_DATA", [])
        if address_data:
            print("\nAll Addresses:")
            for addr in address_data:
                print(f"  • {addr}")
        
        phone_data = resolved.get("PHONE_DATA", [])
        if phone_data:
            print("\nAll Phone Numbers:")
            for phone in phone_data:
                print(f"  • {phone}")
        
        # Step 4: Show why records matched
        print_header("Step 4: Why Did These Records Match?")
        print("Senzing explains the matching logic:\n")
        
        why_response = bytearray()
        g2_engine.whyEntityByRecordID("CRM", "CRM-1001", why_response)
        why_result = json.loads(why_response.decode())
        
        why_results = why_result.get("WHY_RESULTS", [])
        if why_results and len(why_results) > 0:
            match_info = why_results[0].get("MATCH_INFO", {})
            print("Matching Features:")
            for key, value in match_info.items():
                if isinstance(value, dict):
                    print(f"  • {key}:")
                    for k, v in value.items():
                        print(f"      {k}: {v}")
        
        # Step 5: Verify Jane Smith is separate
        print_header("Step 5: Verification - Different Customer")
        print("Let's verify that Jane Smith (CRM-1002) is correctly identified")
        print("as a DIFFERENT customer (not merged with John Smith)...\n")
        
        jane_response = bytearray()
        g2_engine.getEntityByRecordID("CRM", "CRM-1002", jane_response)
        jane_entity = json.loads(jane_response.decode())
        
        jane_entity_id = jane_entity.get("RESOLVED_ENTITY", {}).get("ENTITY_ID")
        john_entity_id = entity.get("RESOLVED_ENTITY", {}).get("ENTITY_ID")
        
        print(f"John Smith Entity ID: {john_entity_id}")
        print(f"Jane Smith Entity ID: {jane_entity_id}")
        print()
        
        if jane_entity_id != john_entity_id:
            print("✓ Correct! Jane Smith is a separate customer.")
            print("  Senzing correctly distinguished between similar names.")
        else:
            print("✗ ERROR: Records incorrectly merged")
        
        # Summary
        print_header("Demo Complete!")
        print("Key Takeaways:")
        print("  • Senzing automatically resolved 3 duplicate records into 1 entity")
        print("  • No manual rules or configuration required")
        print("  • Correctly distinguished between John Smith and Jane Smith")
        print("  • Created unified customer view with all contact information")
        print("  • Explained WHY records matched")
        print()
        print("Next Steps:")
        print("  • Try Module 1: Define your own Customer 360 use case")
        print("  • Try Module 2: Collect your actual customer data")
        print("  • Try Module 4: Map your data to Senzing format")
        print()
        
        return 0
        
    except G2Exception as e:
        print(f"\nERROR: {e}")
        return 1
    finally:
        g2_engine.destroy()


def main():
    """Main entry point"""
    
    # Check for config file or use default SQLite
    config_file = Path("database/G2C.db")
    
    if not config_file.parent.exists():
        print(f"ERROR: Database directory not found: {config_file.parent}")
        print("Please run Module 5 (SDK Setup) first to create the database.")
        return 1
    
    config_json = json.dumps({
        "SQL": {
            "CONNECTION": f"sqlite3://na:na@{config_file}"
        }
    })
    
    return run_demo(config_json)


if __name__ == "__main__":
    sys.exit(main())
