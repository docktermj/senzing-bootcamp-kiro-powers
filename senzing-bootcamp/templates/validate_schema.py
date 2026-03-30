#!/usr/bin/env python3
"""
Senzing Schema Validator

Validates PostgreSQL or SQLite database schema against Senzing SDK requirements.
Catches common schema issues before they cause runtime errors.

Usage:
    python validate_schema.py --database postgresql \
        --connection "postgresql://user:pass@host:5432/db"
    python validate_schema.py --database sqlite \
        --connection "database/G2C.db"
"""

import argparse
import sys
from typing import Dict, List, Tuple

# Database connectors (optional imports)
try:
    import psycopg2
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

try:
    import sqlite3
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False


class SchemaValidator:
    """Validates Senzing database schema"""

    # Required tables and their critical columns
    REQUIRED_SCHEMA = {
        'sys_vars': {
            'columns': {
                'var_group': 'VARCHAR(50)',
                'var_code': 'VARCHAR(50)',
                'var_value': 'TEXT',
                'sys_lstupd_dt': 'TIMESTAMP'
            },
            'primary_key': ['var_group', 'var_code'],
            'critical': True,
            'description': 'System variables including version information'
        },
        'sys_cfg': {
            'columns': {
                'config_data_id': 'BIGSERIAL/INTEGER',
                'config_data': 'TEXT',
                'config_comments': 'TEXT',
                'sys_create_dt': 'TIMESTAMP'  # NOT sys_create_date!
            },
            'primary_key': ['config_data_id'],
            'critical': True,
            'description': 'Configuration storage',
            'common_errors': [
                'Using sys_create_date instead of sys_create_dt causes SENZ1001 error'
            ]
        },
        'sys_codes_used': {
            'columns': {
                'code_type': 'VARCHAR(50)',
                'code': 'VARCHAR(50)',
                'code_id': 'BIGSERIAL/INTEGER'  # Required!
            },
            'primary_key': ['code_type', 'code'],
            'critical': True,
            'description': 'Data source tracking',
            'common_errors': [
                'Missing code_id column causes SENZ1001 error when querying data sources'
            ]
        }
    }

    # Required version values in sys_vars
    REQUIRED_VERSIONS = {
        'VERSION': '4.2.1',
        'SCHEMA_VERSION': '4.0'
    }

    def __init__(self, db_type: str, connection_string: str):
        self.db_type = db_type.lower()
        self.connection_string = connection_string
        self.connection = None
        self.errors = []
        self.warnings = []
        self.info = []

    def connect(self) -> bool:
        """Connect to database"""
        try:
            if self.db_type == 'postgresql':
                if not POSTGRES_AVAILABLE:
                    self.errors.append(
                        "psycopg2 not installed. "
                        "Install with: pip install psycopg2-binary"
                    )
                    return False
                self.connection = psycopg2.connect(self.connection_string)

            elif self.db_type == 'sqlite':
                if not SQLITE_AVAILABLE:
                    self.errors.append("sqlite3 not available")
                    return False
                self.connection = sqlite3.connect(self.connection_string)

            else:
                self.errors.append(f"Unsupported database type: {self.db_type}")
                return False

            self.info.append(f"✅ Connected to {self.db_type} database")
            return True

        except Exception as e:
            self.errors.append(f"❌ Connection failed: {e}")
            return False

    def get_table_columns(self, table_name: str) -> Dict[str, str]:
        """Get columns and their types for a table"""
        cursor = self.connection.cursor()
        columns = {}

        try:
            if self.db_type == 'postgresql':
                cursor.execute("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))

            elif self.db_type == 'sqlite':
                cursor.execute(f"PRAGMA table_info({table_name})")
                # SQLite returns: cid, name, type, notnull, dflt_value, pk
                for row in cursor.fetchall():
                    columns[row[1]] = row[2]
                return columns

            for row in cursor.fetchall():
                columns[row[0]] = row[1]

        except Exception as e:
            self.warnings.append(f"Could not read columns for {table_name}: {e}")

        finally:
            cursor.close()

        return columns

    def table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        cursor = self.connection.cursor()

        try:
            if self.db_type == 'postgresql':
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = %s
                    )
                """, (table_name,))
                return cursor.fetchone()[0]

            elif self.db_type == 'sqlite':
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name=?
                """, (table_name,))
                return cursor.fetchone() is not None

        except Exception as e:
            self.warnings.append(f"Error checking table {table_name}: {e}")
            return False

        finally:
            cursor.close()

    def validate_table(self, table_name: str, schema: Dict) -> bool:
        """Validate a single table"""
        print(f"\n{'='*60}")
        print(f"Validating table: {table_name}")
        print(f"Description: {schema['description']}")
        print(f"{'='*60}")

        # Check if table exists
        if not self.table_exists(table_name):
            if schema.get('critical'):
                self.errors.append(f"❌ CRITICAL: Table '{table_name}' does not exist")
                print(f"❌ Table does not exist")
                return False
            else:
                self.warnings.append(f"⚠️  Table '{table_name}' does not exist (optional)")
                print(f"⚠️  Table does not exist (optional)")
                return True

        print(f"✅ Table exists")

        # Get actual columns
        actual_columns = self.get_table_columns(table_name)
        required_columns = schema['columns']

        # Check each required column
        all_columns_ok = True
        for col_name, col_type in required_columns.items():
            if col_name not in actual_columns:
                self.errors.append(f"❌ CRITICAL: Column '{table_name}.{col_name}' is missing")
                print(f"❌ Missing column: {col_name} ({col_type})")
                all_columns_ok = False
            else:
                print(f"✅ Column exists: {col_name} ({actual_columns[col_name]})")

        # Show common errors if any
        if 'common_errors' in schema:
            print(f"\n⚠️  Common Errors for {table_name}:")
            for error in schema['common_errors']:
                print(f"   - {error}")

        return all_columns_ok

    def validate_version_data(self) -> bool:
        """Validate sys_vars has correct version data"""
        print(f"\n{'='*60}")
        print(f"Validating version data in sys_vars")
        print(f"{'='*60}")

        if not self.table_exists('sys_vars'):
            self.errors.append("❌ Cannot validate versions: sys_vars table missing")
            return False

        cursor = self.connection.cursor()
        all_ok = True

        try:
            for var_code, expected_value in self.REQUIRED_VERSIONS.items():
                if self.db_type == 'postgresql':
                    cursor.execute("""
                        SELECT var_value FROM sys_vars
                        WHERE var_group = 'SYSTEM' AND var_code = %s
                    """, (var_code,))
                else:
                    cursor.execute("""
                        SELECT var_value FROM sys_vars
                        WHERE var_group = 'SYSTEM' AND var_code = ?
                    """, (var_code,))

                row = cursor.fetchone()

                if row is None:
                    self.errors.append(
                        f"❌ Missing version entry: SYSTEM.{var_code}"
                    )
                    print(f"❌ Missing: {var_code}")
                    all_ok = False
                elif row[0] != expected_value:
                    self.warnings.append(
                    self.errors.append(
                        f"❌ Wrong value for {var_code}: "
                        f"expected {expected_value}, got {row[0]}"
                    )
                    )
                    print(f"⚠️  {var_code} = '{row[0]}' (expected '{expected_value}')")
                else:
                    print(f"✅ {var_code} = '{row[0]}'")

        except Exception as e:
            self.errors.append(f"❌ Error reading version data: {e}")
            all_ok = False

        finally:
            cursor.close()

        return all_ok

    def validate(self) -> bool:
        """Run full validation"""
        print("\n" + "="*60)
        print("SENZING SCHEMA VALIDATOR")
        print("="*60)
        print(f"Database Type: {self.db_type}")
        print(f"Connection: {self.connection_string}")

        # Connect
        if not self.connect():
            return False

        # Validate each required table
        all_valid = True
        for table_name, schema in self.REQUIRED_SCHEMA.items():
            if not self.validate_table(table_name, schema):
                all_valid = False

        # Validate version data
        if not self.validate_version_data():
            all_valid = False

        # Print summary
        self.print_summary()

        return all_valid

    def print_summary(self):
        """Print validation summary"""
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)

        if self.info:
            print(f"\nℹ️  Information ({len(self.info)}):")
            for msg in self.info:
                print(f"   {msg}")

        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for msg in self.warnings:
                print(f"   {msg}")

        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for msg in self.errors:
                print(f"   {msg}")
            print("\n🔧 FIXES NEEDED:")
            self.print_fixes()
        else:
            print("\n✅ SCHEMA VALIDATION PASSED!")
            print("   Your database schema is correctly configured for Senzing SDK.")

    def print_fixes(self):
        """Print SQL fixes for common errors"""
        print("\nCommon fixes:\n")

        # Fix for sys_create_dt
        if any('sys_create_dt' in err for err in self.errors):
            print("Fix sys_cfg.sys_create_dt column:")
            print("```sql")
            print("-- Rename column if it exists as sys_create_date")
            print("ALTER TABLE sys_cfg RENAME COLUMN sys_create_date TO sys_create_dt;")
            print("")
            print("-- Or recreate table with correct name")
            print("DROP TABLE IF EXISTS sys_cfg;")
            print("CREATE TABLE sys_cfg (")
            print("    config_data_id BIGSERIAL PRIMARY KEY,")
            print("    config_data TEXT NOT NULL,")
            print("    config_comments TEXT,")
            print("    sys_create_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print(");")
            print("```\n")

        # Fix for code_id
        if any('code_id' in err for err in self.errors):
            print("Fix sys_codes_used.code_id column:")
            print("```sql")
            print("-- Add missing code_id column")
            print("ALTER TABLE sys_codes_used ADD COLUMN code_id BIGSERIAL;")
            print("")
            print("-- Or recreate table with correct structure")
            print("DROP TABLE IF EXISTS sys_codes_used;")
            print("CREATE TABLE sys_codes_used (")
            print("    code_type VARCHAR(50) NOT NULL,")
            print("    code VARCHAR(50) NOT NULL,")
            print("    code_id BIGSERIAL,")
            print("    PRIMARY KEY (code_type, code)")
            print(");")
            print("```\n")

        # Fix for missing version data
        if any('version entry' in err.lower() for err in self.errors):
            print("Fix missing version data:")
            print("```sql")
            print("-- Insert required version information")
            print("INSERT INTO sys_vars (var_group, var_code, var_value)")
            print("VALUES ('SYSTEM', 'VERSION', '4.2.1');")
            print("")
            print("INSERT INTO sys_vars (var_group, var_code, var_value)")
            print("VALUES ('SYSTEM', 'SCHEMA_VERSION', '4.0');")
            print("```\n")

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()


def main():
    parser = argparse.ArgumentParser(
        description='Validate Senzing database schema',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # PostgreSQL
  python validate_schema.py --database postgresql \\
    --connection "postgresql://senzing:pass@localhost:5432/senzing"

  # SQLite
  python validate_schema.py --database sqlite \\
    --connection "database/G2C.db"

  # PostgreSQL
  python validate_schema.py --database postgresql \\
    --connection "postgresql://senzing:pass@postgres:5432/senzing"
        """
    )

    parser.add_argument(
        '--database',
        required=True,
        choices=['postgresql', 'sqlite'],
        help='Database type'
    )

    parser.add_argument(
        '--connection',
        required=True,
        help='Database connection string'
    )

    args = parser.parse_args()

    # Run validation
    validator = SchemaValidator(args.database, args.connection)

    try:
        success = validator.validate()
        sys.exit(0 if success else 1)
    finally:
        validator.close()


if __name__ == '__main__':
    main()
