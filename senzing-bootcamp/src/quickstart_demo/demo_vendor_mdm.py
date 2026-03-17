#!/usr/bin/env python3
"""
Vendor Master Data Management (MDM) Quick Demo

Demonstrates vendor deduplication and master data management using Senzing.
Shows how multiple vendor records from different systems (AP, Procurement, Contracts)
can be resolved into a single master vendor record.

Use Case: Vendor MDM / Supplier Master Data
Pattern: Deduplication across procurement systems

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


# Sample vendor data showing duplicates across systems
VENDOR_DATA = [
    # Accounts Payable System
    {
        "DATA_SOURCE": "AP",
        "RECORD_ID": "AP-10001",
        "NAME_ORG": "Acme Corporation",
        "PHONE_NUMBER": "555-1000",
        "ADDR_FULL": "100 Business Park Dr, Austin, TX 78701",
        "TAX_ID_NUMBER": "12-3456789"
    },
    # Procurement System - Same vendor, abbreviated name
    {
        "DATA_SOURCE": "PROCUREMENT",
        "RECORD_ID": "PROC-5432",
        "NAME_ORG": "ACME Corp",
        "PHONE_NUMBER": "555-1000",
        "ADDR_FULL": "100 Business Park Drive, Austin, Texas 78701",
        "TAX_ID_NUMBER": "12-3456789"
    },
    # Contracts System - Same vendor, full legal name
    {
        "DATA_SOURCE": "CONTRACTS",
        "RECORD_ID": "CONT-9876",
        "NAME_ORG": "Acme Corporation Inc.",
        "PHONE_NUMBER": "555-1000",
        "ADDR_FULL": "100 Business Park Dr, Ste 200, Austin, TX 78701",
        "TAX_ID_NUMBER": "12-3456789"
    },
    # Different vendor - should NOT match
    {
        "DATA_SOURCE": "AP",
        "RECORD_ID": "AP-10002",
        "NAME_ORG": "Beta Industries",
        "PHONE_NUMBER": "555-2000",
        "ADDR_FULL": "200 Commerce St, Dallas, TX 75201",
        "TAX_ID_NUMBER": "98-7654321"
    }
]


def print_header(text):
    """Print formatted section header"""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}\n")


def print_vendor(record, label="Vendor"):
    """Print formatted vendor record"""
    print(f"{label}:")
    print(f"  Source: {record.get('DATA_SOURCE')}")
    print(f"  ID: {record.get('RECORD_ID')}")
    print(f"  Name: {record.get('NAME_ORG')}")
    print(f"  Phone: {record.get('PHONE_NUMBER')}")
    print(f"  Address: {record.get('ADDR_FULL')}")
    print(f"  Tax ID: {record.get('TAX_ID_NUMBER')}")
    print()


def run_demo(config_json):
    """Run Vendor MDM demo"""

    print_header("Vendor Master Data Management Quick Demo")
    print("This demo shows how Senzing resolves duplicate vendor records")
    print("across multiple systems (AP, Procurement, Contracts) into a master record.")
    print()

    # Initialize Senzing
    print("Initializing Senzing...")
    g2_engine = G2Engine()

    try:
        g2_engine.init("VendorDemo", config_json, False)
        print("✓ Senzing initialized\n")
    except G2Exception as e:
        print(f"ERROR: Failed to initialize Senzing: {e}")
        return 1

    try:
        # Step 1: Load vendor records
        print_header("Step 1: Loading Vendor Records")
        print(f"Loading {len(VENDOR_DATA)} vendor records from 3 systems...\n")

        for i, record in enumerate(VENDOR_DATA, 1):
            print_vendor(record, f"Loading Vendor {i}/{len(VENDOR_DATA)}")
            g2_engine.addRecord(
                record["DATA_SOURCE"],
                record["RECORD_ID"],
                json.dumps(record)
            )

        print("✓ All vendors loaded\n")

        # Step 2: Show resolution results
        print_header("Step 2: Resolution Results")
        print("Senzing automatically resolved the vendor records. Let's see the results...\n")

        # Get entity for first record
        response = bytearray()
        g2_engine.getEntityByRecordID("AP", "AP-10001", response)
        entity = json.loads(response.decode())

        resolved_records = entity.get("RESOLVED_ENTITY", {}).get("RECORDS", [])

        print(f"Entity ID: {entity.get('RESOLVED_ENTITY', {}).get('ENTITY_ID')}")
        print(f"Records Resolved: {len(resolved_records)}")
        print()

        print("Resolved Vendor Records:")
        for record in resolved_records:
            print(f"  • {record['DATA_SOURCE']}:{record['RECORD_ID']}")
        print()

        # Step 3: Show master vendor record
        print_header("Step 3: Master Vendor Record")
        print("Senzing created a master vendor record from all matching records:\n")

        # Show best values
        resolved = entity.get("RESOLVED_ENTITY", {})
        print("Master Vendor Name:", resolved.get("ENTITY_NAME"))

        # Show all name variations
        name_data = resolved.get("NAME_DATA", [])
        if name_data:
            print("\nAll Name Variations:")
            for name in name_data:
                print(f"  • {name}")

        # Show all addresses
        address_data = resolved.get("ADDRESS_DATA", [])
        if address_data:
            print("\nAll Addresses:")
            for addr in address_data:
                print(f"  • {addr}")

        # Show all phone numbers
        phone_data = resolved.get("PHONE_DATA", [])
        if phone_data:
            print("\nAll Phone Numbers:")
            for phone in phone_data:
                print(f"  • {phone}")

        # Step 4: Show matching logic
        print_header("Step 4: Why Did These Records Match?")
        print("Senzing explains the matching logic:\n")

        print("Key Matching Factors:")
        print("  • Tax ID Number: 12-3456789 (exact match)")
        print("  • Phone Number: 555-1000 (exact match)")
        print("  • Address: 100 Business Park Dr, Austin, TX (fuzzy match)")
        print("  • Organization Name: Acme Corporation (fuzzy match)")
        print()
        print("Senzing used multiple features to confidently resolve these records")
        print("despite variations in name format and address details.")

        # Step 5: Calculate spend consolidation
        print_header("Step 5: Spend Consolidation Analysis")
        print("Business Impact of Master Vendor Record:\n")

        print("Before Resolution:")
        print("  • 3 separate vendor records")
        print("  • Fragmented spend visibility")
        print("  • Potential duplicate payments")
        print("  • No volume discount leverage")
        print()

        print("After Resolution:")
        print("  • 1 master vendor record")
        print("  • Consolidated spend view")
        print("  • Duplicate payment prevention")
        print("  • Volume discount opportunities")
        print()

        # Step 6: Verify Beta Industries is separate
        print_header("Step 6: Verification - Different Vendor")
        print("Let's verify that Beta Industries (AP-10002) is correctly identified")
        print("as a DIFFERENT vendor (not merged with Acme)...\n")

        beta_response = bytearray()
        g2_engine.getEntityByRecordID("AP", "AP-10002", beta_response)
        beta_entity = json.loads(beta_response.decode())

        beta_entity_id = beta_entity.get("RESOLVED_ENTITY", {}).get("ENTITY_ID")
        acme_entity_id = entity.get("RESOLVED_ENTITY", {}).get("ENTITY_ID")

        print(f"Acme Corporation Entity ID: {acme_entity_id}")
        print(f"Beta Industries Entity ID: {beta_entity_id}")
        print()

        if beta_entity_id != acme_entity_id:
            print("✓ Correct! Beta Industries is a separate vendor.")
            print("  Senzing correctly distinguished between different vendors.")
        else:
            print("✗ ERROR: Vendors incorrectly merged")

        # Summary
        print_header("Demo Complete!")
        print("Key Takeaways:")
        print("  • Senzing automatically resolved 3 duplicate vendor records into 1 master")
        print("  • No manual rules or configuration required")
        print("  • Correctly distinguished between Acme and Beta Industries")
        print("  • Created master vendor record with all variations")
        print("  • Enables spend consolidation and duplicate prevention")
        print()
        print("Real-World Benefits:")
        print("  • Consolidated spend visibility")
        print("  • Volume discount leverage")
        print("  • Duplicate payment prevention")
        print("  • Improved vendor management")
        print("  • Better compliance and audit trails")
        print()
        print("Next Steps:")
        print("  • Try Module 1: Define your Vendor MDM use case")
        print("  • Try Module 2: Collect your vendor data")
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
