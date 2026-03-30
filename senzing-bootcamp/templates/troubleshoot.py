#!/usr/bin/env python3
"""
Interactive Troubleshooting Wizard

Helps diagnose and fix common Senzing Boot Camp issues through guided questions.

Usage:
    python troubleshoot.py
"""

import sys
import subprocess
from pathlib import Path


class TroubleshootingWizard:
    """Interactive troubleshooting wizard"""

    def __init__(self):
        self.issue_category = None
        self.module = None

    def print_header(self, title):
        """Print formatted header"""
        print("\n" + "="*60)
        print(title)
        print("="*60)

    def ask_question(self, question, options):
        """Ask multiple choice question"""
        print(f"\n{question}")
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")

        while True:
            try:
                choice = input("\nYour choice (number): ").strip()
                choice_num = int(choice)
                if 1 <= choice_num <= len(options):
                    return choice_num - 1
                print(f"Please enter a number between 1 and {len(options)}")
            except ValueError:
                print("Please enter a valid number")

    def ask_yes_no(self, question):
        """Ask yes/no question"""
        while True:
            response = input(f"\n{question} (yes/no): ").strip().lower()
            if response in ['yes', 'y']:
                return True
            elif response in ['no', 'n']:
                return False
            print("Please answer 'yes' or 'no'")

    def run_diagnostic(self, command, description):
        """Run diagnostic command"""
        print(f"\n🔍 Running diagnostic: {description}")
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def start(self):
        """Start troubleshooting wizard"""
        self.print_header("SENZING BOOT CAMP TROUBLESHOOTING WIZARD")
        print("This wizard will help diagnose and fix common issues.")
        print("Answer a few questions to get specific solutions.")

        # Ask about issue category
        category_idx = self.ask_question(
            "What type of issue are you experiencing?",
            [
                "Installation or setup problems",
                "Data transformation errors",
                "Data loading errors",
                "Query or results issues",
                "Performance problems",
                "Database connection issues",
                "Other or not sure"
            ]
        )

        # Route to specific troubleshooting
        if category_idx == 0:
            self.troubleshoot_installation()
        elif category_idx == 1:
            self.troubleshoot_transformation()
        elif category_idx == 2:
            self.troubleshoot_loading()
        elif category_idx == 3:
            self.troubleshoot_queries()
        elif category_idx == 4:
            self.troubleshoot_performance()
        elif category_idx == 5:
            self.troubleshoot_database()
        else:
            self.troubleshoot_general()

    def troubleshoot_installation(self):
        """Troubleshoot installation issues"""
        self.print_header("INSTALLATION TROUBLESHOOTING")

        # Check Python
        success, stdout, stderr = self.run_diagnostic(
            "python3 --version",
            "Checking Python version"
        )

        if not success:
            print("\n❌ Python not found or not working")
            print("\n💡 Solution:")
            print("Install Python 3.8+:")
            print("  Ubuntu/Debian: sudo apt install python3 python3-pip")
            print("  macOS: brew install python3")
            return

        print(f"✅ Python found: {stdout.strip()}")

        # Check Senzing
        success, stdout, stderr = self.run_diagnostic(
            "python3 -c 'import senzing; print(senzing.__version__)'",
            "Checking Senzing SDK"
        )

        if not success:
            print("\n❌ Senzing SDK not installed")
            print("\n💡 Solution:")
            print("Install Senzing SDK:")
            print("  pip install senzing")
            print("\nOr follow Module 5 installation guide:")
            print("  docs/modules/MODULE_5_SDK_SETUP.md")
            return

        print(f"✅ Senzing SDK found: {stdout.strip()}")

        # Check disk space
        success, stdout, stderr = self.run_diagnostic(
            "df -h . | tail -1 | awk '{print $4}'",
            "Checking disk space"
        )

        if success:
            print(f"✅ Available disk space: {stdout.strip()}")

        print("\n✅ Installation looks good!")
        print("If you're still having issues, check:")
        print("  - docs/guides/PREFLIGHT_CHECKLIST.md")
        print("  - docs/guides/TROUBLESHOOTING_INDEX.md")

    def troubleshoot_transformation(self):
        """Troubleshoot transformation issues"""
        self.print_header("TRANSFORMATION TROUBLESHOOTING")

        issue_idx = self.ask_question(
            "What transformation issue are you seeing?",
            [
                "JSON decode errors",
                "Missing required fields",
                "Wrong attribute names",
                "Data quality issues",
                "File encoding problems"
            ]
        )

        if issue_idx == 0:
            print("\n❌ JSON Decode Errors")
            print("\n💡 Solutions:")
            print("1. Check for empty lines in input:")
            print("   if line.strip():")
            print("       record = json.loads(line)")
            print("\n2. Validate JSON format:")
            print("   python -m json.tool < your_file.json")
            print("\n3. Check for special characters or encoding issues")

        elif issue_idx == 1:
            print("\n❌ Missing Required Fields")
            print("\n💡 Solutions:")
            print("1. Ensure DATA_SOURCE and RECORD_ID are present:")
            print("   record['DATA_SOURCE'] = 'YOUR_SOURCE'")
            print("   record['RECORD_ID'] = row['id']")
            print("\n2. Validate before writing:")
            print("   required = ['DATA_SOURCE', 'RECORD_ID']")
            print("   for field in required:")
            print("       if not record.get(field):")
            print("           print(f'Missing {field}')")

        elif issue_idx == 2:
            print("\n❌ Wrong Attribute Names")
            print("\n💡 Solutions:")
            print("1. Use mapping_workflow tool (don't guess names)")
            print("2. Common correct names:")
            print("   - NAME_FULL (not FULL_NAME)")
            print("   - NAME_ORG (not ORGANIZATION_NAME)")
            print("   - ADDR_FULL (not ADDRESS)")
            print("   - PHONE_NUMBER (not PHONE)")
            print("\n3. See docs/modules/MODULE_4_DATA_MAPPING.md")

        elif issue_idx == 3:
            print("\n❌ Data Quality Issues")
            print("\n💡 Solutions:")
            print("1. Run quality assessment:")
            print("   python templates/validate_schema.py")
            print("\n2. Check completeness:")
            print("   - Are required fields populated?")
            print("   - Are values in correct format?")
            print("\n3. Use lint_record to validate output")

        else:
            print("\n❌ File Encoding Problems")
            print("\n💡 Solutions:")
            print("1. Detect encoding:")
            print("   file -i your_file.csv")
            print("\n2. Convert to UTF-8:")
            print("   iconv -f ISO-8859-1 -t UTF-8 input.csv > output.csv")
            print("\n3. Specify encoding in Python:")
            print("   open('file.csv', encoding='utf-8')")

    def troubleshoot_loading(self):
        """Troubleshoot loading issues"""
        self.print_header("LOADING TROUBLESHOOTING")

        issue_idx = self.ask_question(
            "What loading issue are you seeing?",
            [
                "Database connection failed",
                "Slow loading performance",
                "Memory errors",
                "Data source not registered",
                "SENZ error codes"
            ]
        )

        if issue_idx == 0:
            print("\n❌ Database Connection Failed")
            print("\n💡 Solutions:")
            print("1. Check database is running:")
            print("   # PostgreSQL")
            print("   sudo systemctl status postgresql")
            print("   # SQLite")
            print("   ls -la database/G2C.db")
            print("\n2. Verify connection string")
            print("\n3. Check permissions")

        elif issue_idx == 1:
            print("\n❌ Slow Loading Performance")
            print("\n💡 Solutions:")
            print("1. Increase batch size (if using batches)")
            print("2. Use PostgreSQL instead of SQLite")
            print("3. Add more CPU/memory")
            print("4. Run performance baseline:")
            print("   python templates/performance_baseline.py")

        elif issue_idx == 2:
            print("\n❌ Memory Errors")
            print("\n💡 Solutions:")
            print("1. Process in smaller batches")
            print("2. Increase available memory")
            print("3. Use streaming instead of loading all at once")

        elif issue_idx == 3:
            print("\n❌ Data Source Not Registered")
            print("\n💡 Solutions:")
            print("1. Register data source before loading:")
            print("   # In Module 5 setup")
            print("2. Check registered sources:")
            print("   # Query sys_codes_used table")
            print("\n3. See MODULE_5_SDK_SETUP.md")

        else:
            error_code = input("\nEnter SENZ error code (e.g., 1001): ").strip()
            print(f"\n💡 Solution:")
            print(f"Use explain_error_code tool:")
            print(f"  explain_error_code('{error_code}')")
            print(f"\nOr check TROUBLESHOOTING_INDEX.md")

    def troubleshoot_queries(self):
        """Troubleshoot query issues"""
        self.print_header("QUERY TROUBLESHOOTING")

        issue_idx = self.ask_question(
            "What query issue are you seeing?",
            [
                "No results found",
                "Too many results",
                "Slow queries",
                "Unexpected matches"
            ]
        )

        if issue_idx == 0:
            print("\n❌ No Results Found")
            print("\n💡 Solutions:")
            print("1. Verify data was loaded:")
            print("   engine.stats()")
            print("\n2. Check search criteria")
            print("\n3. Try broader search")

        elif issue_idx == 1:
            print("\n❌ Too Many Results")
            print("\n💡 Solutions:")
            print("1. Add more specific search criteria")
            print("2. Use result limits")
            print("3. Filter by data source")

        elif issue_idx == 2:
            print("\n❌ Slow Queries")
            print("\n💡 Solutions:")
            print("1. Add database indexes")
            print("2. Use more specific searches")
            print("3. Limit result size")
            print("4. Check database performance")

        else:
            print("\n❌ Unexpected Matches")
            print("\n💡 Solutions:")
            print("1. Use whyEntities to understand matching:")
            print("   engine.whyEntities(entity1, entity2)")
            print("\n2. Review matching rules")
            print("\n3. Check data quality")

    def troubleshoot_performance(self):
        """Troubleshoot performance issues"""
        self.print_header("PERFORMANCE TROUBLESHOOTING")

        print("\n🔍 Running performance diagnostics...")

        # Check CPU
        success, stdout, stderr = self.run_diagnostic(
            "nproc",
            "Checking CPU cores"
        )
        if success:
            cores = int(stdout.strip())
            if cores < 2:
                print(f"⚠️  Only {cores} CPU core available (2+ recommended)")
            else:
                print(f"✅ {cores} CPU cores available")

        # Check memory
        success, stdout, stderr = self.run_diagnostic(
            "free -g | grep Mem | awk '{print $2}'",
            "Checking memory"
        )
        if success:
            mem_gb = int(stdout.strip())
            if mem_gb < 4:
                print(f"⚠️  Only {mem_gb}GB RAM (4GB+ recommended)")
            else:
                print(f"✅ {mem_gb}GB RAM available")

        print("\n💡 Performance Recommendations:")
        print("1. Run performance baseline:")
        print("   python templates/performance_baseline.py")
        print("\n2. Use PostgreSQL instead of SQLite")
        print("\n3. Increase batch sizes")
        print("\n4. Add more CPU/memory if possible")
        print("\n5. See docs/guides/TROUBLESHOOTING_INDEX.md")

    def troubleshoot_database(self):
        """Troubleshoot database issues"""
        self.print_header("DATABASE TROUBLESHOOTING")

        db_type_idx = self.ask_question(
            "Which database are you using?",
            ["SQLite", "PostgreSQL", "Other"]
        )

        if db_type_idx == 0:
            print("\n🔍 SQLite Troubleshooting")

            # Check if database exists
            db_path = input("\nDatabase path (default: database/G2C.db): ").strip()
            if not db_path:
                db_path = "database/G2C.db"

            if Path(db_path).exists():
                print(f"✅ Database file exists: {db_path}")

                # Check if locked
                success, stdout, stderr = self.run_diagnostic(
                    f"lsof {db_path}",
                    "Checking if database is locked"
                )

                if success and stdout:
                    print("⚠️  Database may be locked by another process")
                    print("\n💡 Solution:")
                    print("Close other connections to the database")
                else:
                    print("✅ Database not locked")
            else:
                print(f"❌ Database file not found: {db_path}")
                print("\n💡 Solution:")
                print("Create database directory:")
                print("  mkdir -p database")
                print("\nThen run Module 5 setup")

        elif db_type_idx == 1:
            print("\n🔍 PostgreSQL Troubleshooting")

            # Check PostgreSQL
            success, stdout, stderr = self.run_diagnostic(
                "psql --version",
                "Checking PostgreSQL client"
            )

            if not success:
                print("\n❌ PostgreSQL client not found")
                print("\n💡 Solution:")
                print("Install PostgreSQL:")
                print("  Ubuntu/Debian: sudo apt install postgresql")
                print("  macOS: brew install postgresql")
                return

            print(f"✅ PostgreSQL client: {stdout.strip()}")

            # Test connection
            if self.ask_yes_no("Test database connection?"):
                conn_string = input("Connection string: ").strip()
                success, stdout, stderr = self.run_diagnostic(
                    f"psql '{conn_string}' -c 'SELECT 1'",
                    "Testing connection"
                )

                if success:
                    print("✅ Connection successful")

                    # Validate schema
                    if self.ask_yes_no("Validate database schema?"):
                        print("\n💡 Run schema validator:")
                        print(f"python templates/validate_schema.py \\")
                        print(f"  --database postgresql \\")
                        print(f"  --connection '{conn_string}'")
                else:
                    print(f"❌ Connection failed: {stderr}")
                    print("\n💡 Check:")
                    print("  - PostgreSQL is running")
                    print("  - Connection string is correct")
                    print("  - User has permissions")

    def troubleshoot_general(self):
        """General troubleshooting"""
        self.print_header("GENERAL TROUBLESHOOTING")

        print("\n📚 Troubleshooting Resources:")
        print("\n1. Troubleshooting Index:")
        print("   docs/guides/TROUBLESHOOTING_INDEX.md")
        print("\n2. Module-specific guides:")
        print("   docs/modules/MODULE_*.md")
        print("\n3. Pre-flight check:")
        print("   bash scripts/preflight_check.sh")
        print("\n5. Schema validation:")
        print("   python templates/validate_schema.py")

        print("\n💡 Common Solutions:")
        print("  - Check Python version (3.8+)")
        print("  - Verify Senzing is installed")
        print("  - Check disk space and memory")
        print("  - Review error messages carefully")
        print("  - Use MCP tools for guidance")


def main():
    """Run troubleshooting wizard"""
    wizard = TroubleshootingWizard()

    try:
        wizard.start()

        print("\n" + "="*60)
        print("TROUBLESHOOTING COMPLETE")
        print("="*60)
        print("\nIf you're still having issues:")
        print("  - Review docs/guides/TROUBLESHOOTING_INDEX.md")
        print("  - Ask the agent for help")
        print("  - Check Senzing documentation")

    except KeyboardInterrupt:
        print("\n\nTroubleshooting cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
