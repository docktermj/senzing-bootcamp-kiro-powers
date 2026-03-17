#!/usr/bin/env python3
"""
Collect Data from CSV Files

Reads CSV files and prepares them for transformation.
Handles various CSV formats, encodings, and delimiters.

Usage:
    python collect_from_csv.py --input data/raw/customers.csv --output data/samples/customers_sample.csv --sample 1000
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Optional


def detect_delimiter(file_path: str, sample_size: int = 5) -> str:
    """Detect CSV delimiter by analyzing first few lines"""
    with open(file_path, 'r', encoding='utf-8') as f:
        sample = [f.readline() for _ in range(sample_size)]
    
    # Try common delimiters
    delimiters = [',', ';', '\t', '|']
    delimiter_counts = {}
    
    for delimiter in delimiters:
        count = sum(line.count(delimiter) for line in sample)
        delimiter_counts[delimiter] = count
    
    # Return delimiter with highest count
    best_delimiter = max(delimiter_counts, key=delimiter_counts.get)
    print(f"Detected delimiter: '{best_delimiter}'")
    return best_delimiter


def detect_encoding(file_path: str) -> str:
    """Detect file encoding"""
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read(1024)  # Try reading first 1KB
            print(f"Detected encoding: {encoding}")
            return encoding
        except UnicodeDecodeError:
            continue
    
    print("Warning: Could not detect encoding, using utf-8")
    return 'utf-8'


def analyze_csv(file_path: str, delimiter: str, encoding: str):
    """Analyze CSV file structure"""
    print(f"\nAnalyzing CSV file: {file_path}")
    print("=" * 60)
    
    with open(file_path, 'r', encoding=encoding) as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        
        # Get headers
        headers = reader.fieldnames
        print(f"\nColumns ({len(headers)}):")
        for i, header in enumerate(headers, 1):
            print(f"  {i}. {header}")
        
        # Count rows
        row_count = sum(1 for _ in reader)
        print(f"\nTotal rows: {row_count:,}")
        
        # Sample first row
        f.seek(0)
        reader = csv.DictReader(f, delimiter=delimiter)
        first_row = next(reader, None)
        
        if first_row:
            print(f"\nSample row:")
            for key, value in first_row.items():
                print(f"  {key}: {value}")
    
    return row_count, headers


def create_sample(
    input_file: str,
    output_file: str,
    sample_size: int,
    delimiter: str,
    encoding: str
):
    """Create sample file with specified number of rows"""
    print(f"\nCreating sample file...")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print(f"Sample size: {sample_size:,} rows")
    
    # Create output directory if needed
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    with open(input_file, 'r', encoding=encoding) as infile, \
         open(output_file, 'w', encoding='utf-8', newline='') as outfile:
        
        reader = csv.DictReader(infile, delimiter=delimiter)
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
        
        # Write header
        writer.writeheader()
        
        # Write sample rows
        rows_written = 0
        for row in reader:
            writer.writerow(row)
            rows_written += 1
            
            if rows_written >= sample_size:
                break
            
            if rows_written % 1000 == 0:
                print(f"  Processed {rows_written:,} rows...")
    
    print(f"✅ Sample file created: {rows_written:,} rows")


def validate_csv(file_path: str, delimiter: str, encoding: str) -> bool:
    """Validate CSV file can be read"""
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            
            # Try reading first row
            first_row = next(reader, None)
            if first_row is None:
                print("❌ CSV file is empty")
                return False
            
            # Check for headers
            if not reader.fieldnames:
                print("❌ CSV file has no headers")
                return False
            
            print("✅ CSV file is valid")
            return True
            
    except Exception as e:
        print(f"❌ Error validating CSV: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Collect data from CSV files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze CSV file
  python collect_from_csv.py --input data/raw/customers.csv --analyze
  
  # Create sample file
  python collect_from_csv.py --input data/raw/customers.csv \\
    --output data/samples/customers_sample.csv --sample 1000
  
  # Specify delimiter and encoding
  python collect_from_csv.py --input data/raw/customers.csv \\
    --output data/samples/customers_sample.csv --sample 1000 \\
    --delimiter ";" --encoding "latin-1"
        """
    )
    
    parser.add_argument(
        '--input',
        required=True,
        help='Input CSV file path'
    )
    
    parser.add_argument(
        '--output',
        help='Output sample file path'
    )
    
    parser.add_argument(
        '--sample',
        type=int,
        default=1000,
        help='Number of rows to sample (default: 1000)'
    )
    
    parser.add_argument(
        '--delimiter',
        help='CSV delimiter (auto-detected if not specified)'
    )
    
    parser.add_argument(
        '--encoding',
        help='File encoding (auto-detected if not specified)'
    )
    
    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Only analyze file, do not create sample'
    )
    
    args = parser.parse_args()
    
    # Check input file exists
    if not Path(args.input).exists():
        print(f"❌ Input file not found: {args.input}")
        sys.exit(1)
    
    # Detect delimiter and encoding if not specified
    delimiter = args.delimiter or detect_delimiter(args.input)
    encoding = args.encoding or detect_encoding(args.input)
    
    # Validate CSV
    if not validate_csv(args.input, delimiter, encoding):
        sys.exit(1)
    
    # Analyze file
    row_count, headers = analyze_csv(args.input, delimiter, encoding)
    
    # Create sample if requested
    if not args.analyze and args.output:
        create_sample(
            args.input,
            args.output,
            min(args.sample, row_count),
            delimiter,
            encoding
        )
        print(f"\n✅ Data collection complete!")
        print(f"\nNext steps:")
        print(f"1. Review sample file: {args.output}")
        print(f"2. Proceed to Module 3 (Data Quality Evaluation)")
        print(f"3. Then Module 4 (Data Mapping)")
    
    elif args.analyze:
        print(f"\n✅ Analysis complete!")
        print(f"\nTo create a sample file, run:")
        print(f"python collect_from_csv.py --input {args.input} \\")
        print(f"  --output data/samples/sample.csv --sample 1000")


if __name__ == '__main__':
    main()
