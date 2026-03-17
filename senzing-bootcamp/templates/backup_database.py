#!/usr/bin/env python3
"""
Backup Senzing Database

Creates backups of SQLite or PostgreSQL databases.

Usage:
    python backup_database.py --db-type sqlite --database database/G2C.db --output backups/G2C_backup.db
    python backup_database.py --db-type postgresql --connection "postgresql://user:pass@host:5432/db" --output backups/senzing_backup.sql
"""

import argparse
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def backup_sqlite(database_path: str, output_path: str) -> bool:
    """Backup SQLite database"""
    try:
        print(f"Backing up SQLite database...")
        print(f"  Source: {database_path}")
        print(f"  Destination: {output_path}")
        
        # Create output directory
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Copy database file
        shutil.copy2(database_path, output_path)
        
        # Get file size
        size_mb = Path(output_path).stat().st_size / (1024 * 1024)
        
        print(f"✅ Backup complete ({size_mb:.2f} MB)")
        return True
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False


def backup_postgresql(connection_string: str, output_path: str) -> bool:
    """Backup PostgreSQL database using pg_dump"""
    try:
        print(f"Backing up PostgreSQL database...")
        print(f"  Output: {output_path}")
        
        # Create output directory
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Use pg_dump
        cmd = ['pg_dump', connection_string, '-f', output_path]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            size_mb = Path(output_path).stat().st_size / (1024 * 1024)
            print(f"✅ Backup complete ({size_mb:.2f} MB)")
            return True
        else:
            print(f"❌ pg_dump failed: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ pg_dump not found. Install PostgreSQL client tools.")
        return False
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Backup Senzing database')
    
    parser.add_argument('--db-type', required=True, choices=['sqlite', 'postgresql'])
    parser.add_argument('--database', help='SQLite database path')
    parser.add_argument('--connection', help='PostgreSQL connection string')
    parser.add_argument('--output', help='Output backup file')
    parser.add_argument('--auto-name', action='store_true', help='Auto-generate backup filename')
    
    args = parser.parse_args()
    
    # Auto-generate output filename if requested
    if args.auto_name:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if args.db_type == 'sqlite':
            args.output = f"data/backups/G2C_backup_{timestamp}.db"
        else:
            args.output = f"data/backups/senzing_backup_{timestamp}.sql"
    
    if not args.output:
        print("❌ --output or --auto-name required")
        sys.exit(1)
    
    # Perform backup
    if args.db_type == 'sqlite':
        if not args.database:
            print("❌ --database required for SQLite")
            sys.exit(1)
        success = backup_sqlite(args.database, args.output)
    else:
        if not args.connection:
            print("❌ --connection required for PostgreSQL")
            sys.exit(1)
        success = backup_postgresql(args.connection, args.output)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
