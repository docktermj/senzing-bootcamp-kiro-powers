#!/usr/bin/env python3
"""
Collect Data from JSON Files

Reads JSON files (standard JSON or JSON Lines) and prepares them for transformation.

Usage:
    python collect_from_json.py --input data/raw/customers.json \
        --output data/samples/customers_sample.json --sample 1000
"""

import argparse
import json
import sys
from pathlib import Path


def detect_format(file_path: str) -> str:
    """Detect if file is JSON or JSON Lines"""
    with open(file_path, 'r', encoding='utf-8') as f:
        first_line = f.readline().strip()

        # Try parsing as single JSON object
        try:
            json.loads(first_line)
            # Check if next line is also valid JSON
            second_line = f.readline().strip()
            if second_line:
                try:
                    json.loads(second_line)
                    return 'jsonl'
                except:
                    return 'json'
            return 'jsonl'
        except:
            return 'json'


def read_json(file_path: str) -> list:
    """Read JSON file (handles both formats)"""
    format_type = detect_format(file_path)
    print(f"Detected format: {format_type}")

    with open(file_path, 'r', encoding='utf-8') as f:
        if format_type == 'jsonl':
            return [json.loads(line) for line in f if line.strip()]
        else:
            data = json.load(f)
            return data if isinstance(data, list) else [data]


def analyze_json(data: list):
    """Analyze JSON data structure"""
    print(f"\nAnalyzing JSON data...")
    print("=" * 60)
    print(f"Total records: {len(data):,}")

    if data:
        first_record = data[0]
        print(f"\nFields ({len(first_record)}):")
        for key in first_record.keys():
            value = first_record[key]
            value_type = type(value).__name__
            print(f"  {key}: {value_type}")

        print(f"\nSample record:")
        print(json.dumps(first_record, indent=2))


def create_sample(data: list, output_file: str, sample_size: int):
    """Create sample file"""
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    sample_data = data[:sample_size]

    with open(output_file, 'w', encoding='utf-8') as f:
        for record in sample_data:
            f.write(json.dumps(record) + '\n')

    print(f"✅ Sample created: {len(sample_data)} records")


def main():
    parser = argparse.ArgumentParser(description='Collect data from JSON files')
    parser.add_argument('--input', required=True, help='Input JSON file')
    parser.add_argument('--output', help='Output sample file')
    parser.add_argument('--sample', type=int, default=1000, help='Sample size')
    parser.add_argument('--analyze', action='store_true', help='Only analyze')

    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"❌ File not found: {args.input}")
        sys.exit(1)

    data = read_json(args.input)
    analyze_json(data)

    if not args.analyze and args.output:
        create_sample(data, args.output, min(args.sample, len(data)))


if __name__ == '__main__':
    main()
