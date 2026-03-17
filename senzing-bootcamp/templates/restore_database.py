#!/usr/bin/env python3
"""
Restore Senzing Database

Restores SQLite or PostgreSQL databases from backups.

Usage:
    python restore_database.py --db-type sqlite --backup backups/G2C_backup.db --database database/G2C.db
    python restore_database.py --db-type postgresql --backup backups/senzing_backup.sql --connection "postgresql://user:pass@host:5432/db"
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def restore_sqlite(backup_path: str, database_path: str, confirm: bool = True) -> bool:
    """Restore SQLite database"""
    try:
        if confirm:
            response = input(f"⚠️  This will overwrite {database_path}. Continue? (yes/no): ")
            if response.lower() != 'yes':
                print("Restore cancelled")
                return False
        
        print(f"Restoring SQLite database...")
        print(f"  Source: {backup_path}")
        print(f"  Destination: {database_path}")
        
        # Create directory if needed
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Copy backup to database location
        shutil.copy2(backup_path, database_path)
        
        print(f"✅ Restore complete")
        return True
        
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        return False


def restore_postgresql(backup_path: str, connection_string: str, confirm: bool = True) -> bool:
    """Restore PostgreSQL database using psql"""
    try:
        if confirm:
            response = input(f"⚠️  This will overwrite the database. Continue? (yes/no): ")
            if response.lower() != 'yes':
                print("Restore cancelled")
                return False
        
        print(f"Restoring PostgreSQL database...")
        print(f"  Backup: {backup_path}")
        
        # Use psql to restore
        cmd = ['psql', connection_string, '-f', backup_path]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Restore complete")
            return True
        else:
            print(f"❌ psql failed: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ psql not found. Install PostgreSQL client tools.")
        return False
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Restore Senzing database')
    
    parser.add_argument('--db-type', required=True, choices=['sqlite', 'postgresql'])
    parser.add_argument('--backup', required=True, help='Backup file path')
    parser.add_argument('--database', help='SQLite database path')
    parser.add_argument('--connection', help='PostgreSQL connection string')
    parser.add_argument('--yes', action='store_true', help='Skip confirmation')
    
    args = parser.parse_args()
    
    if not Path(args.backup).exists():
        print(f"❌ Backup file not found: {args.backup}")
        sys.exit(1)
    
    # Perform restore
    if args.db_type == 'sqlite':
        if not args.database:
            print("❌ --database required for SQLite")
            sys.exit(1)
        success = restore_sqlite(args.backup, args.database, confirm=not args.yes)
    else:
        if not args.connection:
            print("❌ --connection required for PostgreSQL")
            sys.exit(1)
        success = restore_postgresql(args.backup, args.connection, confirm=not args.yes)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
