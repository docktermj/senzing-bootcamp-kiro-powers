#!/usr/bin/env python3
"""
Collect Data from Databases

Queries databases and exports results to CSV or JSON.
Supports PostgreSQL, MySQL, SQLite, SQL Server, Oracle.

Usage:
    python collect_from_database.py --db-type postgresql --connection "postgresql://user:pass@host:5432/db" --query "SELECT * FROM customers" --output data/raw/customers.csv
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional

# Database connectors (optional imports)
DB_DRIVERS = {}

try:
    import psycopg2
    DB_DRIVERS['postgresql'] = psycopg2
except ImportError:
    pass

try:
    import mysql.connector
    DB_DRIVERS['mysql'] = mysql.connector
except ImportError:
    pass

try:
    import sqlite3
    DB_DRIVERS['sqlite'] = sqlite3
except ImportError:
    pass

try:
    import pyodbc
    DB_DRIVERS['sqlserver'] = pyodbc
except ImportError:
    pass


class DatabaseCollector:
    """Collects data from databases"""
    
    def __init__(self, db_type: str, connection_string: str):
        self.db_type = db_type.lower()
        self.connection_string = connection_string
        self.connection = None
        
        if self.db_type not in DB_DRIVERS:
            raise ValueError(
                f"Database driver not available for {db_type}. "
                f"Install with: pip install {self._get_driver_package()}"
            )
    
    def _get_driver_package(self) -> str:
        """Get pip package name for database driver"""
        packages = {
            'postgresql': 'psycopg2-binary',
            'mysql': 'mysql-connector-python',
            'sqlite': 'built-in',
            'sqlserver': 'pyodbc',
            'oracle': 'cx_Oracle'
        }
        return packages.get(self.db_type, 'unknown')
    
    def connect(self) -> bool:
        """Connect to database"""
        try:
            if self.db_type == 'postgresql':
                self.connection = psycopg2.connect(self.connection_string)
            elif self.db_type == 'mysql':
                # Parse connection string
                self.connection = mysql.connector.connect(self.connection_string)
            elif self.db_type == 'sqlite':
                self.connection = sqlite3.connect(self.connection_string)
            elif self.db_type == 'sqlserver':
                self.connection = pyodbc.connect(self.connection_string)
            
            print(f"✅ Connected to {self.db_type} database")
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def execute_query(self, query: str, limit: Optional[int] = None) -> tuple:
        """Execute query and return results with column names"""
        cursor = self.connection.cursor()
        
        try:
            # Add LIMIT if specified
            if limit:
                if 'LIMIT' not in query.upper():
                    query = f"{query.rstrip(';')} LIMIT {limit}"
            
            print(f"Executing query...")
            print(f"  {query[:100]}{'...' if len(query) > 100 else ''}")
            
            cursor.execute(query)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            
            # Fetch all rows
            rows = cursor.fetchall()
            
            print(f"✅ Retrieved {len(rows)} rows, {len(columns)} columns")
            
            return columns, rows
            
        except Exception as e:
            print(f"❌ Query failed: {e}")
            raise
        finally:
            cursor.close()
    
    def test_connection(self) -> bool:
        """Test database connection"""
        if not self.connect():
            return False
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            print("✅ Connection test successful")
            return True
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()


def save_to_csv(columns: List[str], rows: List[tuple], output_file: str):
    """Save query results to CSV"""
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)
    
    print(f"✅ Saved to CSV: {output_file}")


def save_to_json(columns: List[str], rows: List[tuple], output_file: str, format_type: str = 'jsonl'):
    """Save query results to JSON"""
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Convert rows to dictionaries
    data = [dict(zip(columns, row)) for row in rows]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        if format_type == 'jsonl':
            for record in data:
                f.write(json.dumps(record, default=str) + '\n')
        else:
            json.dump(data, f, indent=2, default=str)
    
    print(f"✅ Saved to JSON: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Collect data from databases',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # PostgreSQL
  python collect_from_database.py \\
    --db-type postgresql \\
    --connection "postgresql://user:pass@localhost:5432/mydb" \\
    --query "SELECT * FROM customers" \\
    --output data/raw/customers.csv
  
  # MySQL
  python collect_from_database.py \\
    --db-type mysql \\
    --connection "mysql://user:pass@localhost:3306/mydb" \\
    --query "SELECT * FROM customers" \\
    --output data/raw/customers.json
  
  # SQLite
  python collect_from_database.py \\
    --db-type sqlite \\
    --connection "database/mydb.db" \\
    --query "SELECT * FROM customers" \\
    --output data/raw/customers.csv
  
  # With limit
  python collect_from_database.py \\
    --db-type postgresql \\
    --connection "postgresql://user:pass@localhost:5432/mydb" \\
    --query "SELECT * FROM customers" \\
    --output data/raw/customers.csv \\
    --limit 1000
        """
    )
    
    parser.add_argument(
        '--db-type',
        required=True,
        choices=['postgresql', 'mysql', 'sqlite', 'sqlserver', 'oracle'],
        help='Database type'
    )
    
    parser.add_argument(
        '--connection',
        required=True,
        help='Database connection string'
    )
    
    parser.add_argument(
        '--query',
        help='SQL query to execute'
    )
    
    parser.add_argument(
        '--query-file',
        help='File containing SQL query'
    )
    
    parser.add_argument(
        '--output',
        help='Output file path (.csv or .json)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of rows'
    )
    
    parser.add_argument(
        '--format',
        choices=['csv', 'json', 'jsonl'],
        help='Output format (auto-detected from file extension if not specified)'
    )
    
    parser.add_argument(
        '--test-only',
        action='store_true',
        help='Only test connection, do not execute query'
    )
    
    args = parser.parse_args()
    
    # Get query
    if args.query_file:
        with open(args.query_file, 'r') as f:
            query = f.read()
    elif args.query:
        query = args.query
    elif not args.test_only:
        print("❌ Either --query or --query-file required")
        sys.exit(1)
    else:
        query = None
    
    # Create collector
    collector = DatabaseCollector(args.db_type, args.connection)
    
    # Test connection
    if not collector.test_connection():
        sys.exit(1)
    
    if args.test_only:
        print("\n✅ Connection test complete!")
        collector.close()
        return
    
    if not args.output:
        print("❌ --output required when executing query")
        sys.exit(1)
    
    # Execute query
    try:
        columns, rows = collector.execute_query(query, limit=args.limit)
        
        if not rows:
            print("⚠️  Query returned no rows")
            sys.exit(1)
        
        # Determine output format
        output_format = args.format
        if not output_format:
            if args.output.endswith('.csv'):
                output_format = 'csv'
            elif args.output.endswith('.json'):
                output_format = 'json'
            elif args.output.endswith('.jsonl'):
                output_format = 'jsonl'
            else:
                output_format = 'csv'
        
        # Save results
        if output_format == 'csv':
            save_to_csv(columns, rows, args.output)
        else:
            save_to_json(columns, rows, args.output, format_type=output_format)
        
        print(f"\n✅ Data collection complete!")
        print(f"\nNext steps:")
        print(f"1. Review collected data: {args.output}")
        print(f"2. Proceed to Module 3 (Data Quality Evaluation)")
        print(f"3. Then Module 4 (Data Mapping)")
        
    except Exception as e:
        print(f"\n❌ Data collection failed: {e}")
        sys.exit(1)
    finally:
        collector.close()


if __name__ == '__main__':
    main()
