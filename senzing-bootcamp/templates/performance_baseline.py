#!/usr/bin/env python3
"""
Performance Baseline Test

Quick performance test to establish baseline metrics.

Usage:
    python performance_baseline.py \
        --config-json '{"SQL":{"CONNECTION":"sqlite3://na:na@database/G2C.db"}}'
"""

import argparse
import json
import time
import sys
from senzing import SzError
from senzing_core import SzAbstractFactoryCore


def generate_test_records(count: int) -> list:
    """Generate test records"""
    records = []
    for i in range(count):
        record = {
            "DATA_SOURCE": "TEST",
            "RECORD_ID": f"TEST-{i:06d}",
            "NAME_FULL": f"Test Person {i}",
            "ADDR_FULL": f"{i} Test Street, Test City, TS 12345",
            "PHONE_NUMBER": f"555-{i:04d}"
        }
        records.append(record)
    return records


def test_loading(engine, records: list) -> dict:
    """Test loading performance"""
    print("\nTesting loading performance...")

    start_time = time.time()

    for record in records:
        engine.add_record(
            record["DATA_SOURCE"],
            record["RECORD_ID"],
            json.dumps(record)
        )

    elapsed = time.time() - start_time
    rate = len(records) / elapsed if elapsed > 0 else 0

    return {
        'records': len(records),
        'elapsed': elapsed,
        'rate': rate
    }


def test_queries(engine, record_count: int) -> dict:
    """Test query performance"""
    print("\nTesting query performance...")

    queries = []

    # Test getRecord
    start = time.time()
    for i in range(min(100, record_count)):
        engine.get_record("TEST", f"TEST-{i:06d}")
    elapsed = time.time() - start
    queries.append(('getRecord', elapsed, 100))

    # Test searchByAttributes
    start = time.time()
    for i in range(10):
        engine.search_by_attributes(json.dumps({"NAME_FULL": f"Test Person {i}"}))
    elapsed = time.time() - start
    queries.append(('searchByAttributes', elapsed, 10))

    return {
        'queries': queries,
        'avg_latency': sum(q[1] for q in queries) / len(queries)
    }


def cleanup(engine, record_count: int):
    """Remove test records"""
    print("\nCleaning up test records...")
    for i in range(record_count):
        try:
            engine.delete_record("TEST", f"TEST-{i:06d}")
        except:
            pass


def run_baseline(engine_config: str):
    """Run complete baseline test"""

    print("="*60)
    print("SENZING PERFORMANCE BASELINE TEST")
    print("="*60)

    # Initialize engine
    sz_factory = SzAbstractFactoryCore("BaselineTest", engine_config)
    engine = sz_factory.create_engine()

    try:
        # Generate test data
        print("\nGenerating test data...")
        records = generate_test_records(1000)
        print(f"  Generated {len(records)} test records")

        # Test loading
        load_results = test_loading(engine, records)

        # Test queries
        query_results = test_queries(engine, len(records))

        # Print results
        print("\n" + "="*60)
        print("BASELINE RESULTS")
        print("="*60)

        print("\nLoading Performance:")
        print(f"  Records loaded: {load_results['records']:,}")
        print(f"  Time elapsed: {load_results['elapsed']:.2f} seconds")
        print(f"  Loading rate: {load_results['rate']:.1f} records/sec")

        print("\nQuery Performance:")
        for query_name, elapsed, count in query_results['queries']:
            avg_ms = (elapsed / count) * 1000
            print(f"  {query_name}: {avg_ms:.2f} ms average")

        print("\n" + "="*60)
        print("INTERPRETATION")
        print("="*60)

        # Provide interpretation
        if load_results['rate'] < 50:
            print("⚠️  Loading rate is low. Consider:")
            print("   - Using PostgreSQL instead of SQLite")
            print("   - Increasing batch size")
            print("   - Adding more CPU/memory")
        elif load_results['rate'] < 200:
            print("✅ Loading rate is acceptable for development")
        else:
            print("✅ Loading rate is good")

        avg_query_ms = (query_results['avg_latency'] / 10) * 1000
        if avg_query_ms > 100:
            print("⚠️  Query latency is high. Consider:")
            print("   - Adding database indexes")
            print("   - Using faster storage (SSD)")
            print("   - Optimizing queries")
        else:
            print("✅ Query latency is acceptable")

        print("\n💡 Tip: Run this test periodically to track performance changes")

        # Cleanup
        cleanup(engine, len(records))

    finally:
        sz_factory.destroy()


def main():
    parser = argparse.ArgumentParser(description='Performance baseline test')
    parser.add_argument('--config-json', required=True, help='Engine configuration JSON')

    args = parser.parse_args()

    try:
        run_baseline(args.config_json)
    except Exception as e:
        print(f"\n❌ Baseline test failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
