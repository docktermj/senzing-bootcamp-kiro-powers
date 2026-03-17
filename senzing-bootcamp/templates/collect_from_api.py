#!/usr/bin/env python3
"""
Collect Data from REST APIs

Fetches data from REST APIs and saves to JSON files.
Handles pagination, authentication, and rate limiting.

Usage:
    python collect_from_api.py --url "https://api.example.com/customers" \
        --output data/raw/customers.json --auth-token "token" \
        --max-records 10000
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("❌ requests library not installed")
    print("Install with: pip install requests")
    sys.exit(1)


class APICollector:
    """Collects data from REST APIs"""

    def __init__(
        self,
        base_url: str,
        auth_token: Optional[str] = None,
        auth_header: str = "Authorization",
        rate_limit: float = 0.0
    ):
        self.base_url = base_url
        self.auth_token = auth_token
        self.auth_header = auth_header
        self.rate_limit = rate_limit
        self.session = requests.Session()

        # Set up authentication
        if auth_token:
            if auth_header.lower() == "authorization":
                self.session.headers['Authorization'] = f"Bearer {auth_token}"
            else:
                self.session.headers[auth_header] = auth_token

    def fetch_page(self, url: str, params: Optional[Dict] = None) -> Dict:
        """Fetch a single page from API"""
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            # Rate limiting
            if self.rate_limit > 0:
                time.sleep(self.rate_limit)

            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"❌ API request failed: {e}")
            raise

    def fetch_all(
        self,
        endpoint: str,
        pagination_key: Optional[str] = None,
        data_key: Optional[str] = None,
        max_pages: Optional[int] = None
    ) -> List[Dict]:
        """Fetch all pages from API with pagination"""

        all_data = []
        page = 1
        next_url = urljoin(self.base_url, endpoint)

        print(f"Fetching data from: {next_url}")

        while next_url and (max_pages is None or page <= max_pages):
            print(f"  Fetching page {page}...")

            try:
                response_data = self.fetch_page(next_url)

                # Extract data from response
                if data_key:
                    page_data = response_data.get(data_key, [])
                elif isinstance(response_data, list):
                    page_data = response_data
                else:
                    page_data = [response_data]

                all_data.extend(page_data)
                print(f"    Retrieved {len(page_data)} records (total: {len(all_data)})")

                # Check for next page
                if pagination_key:
                    next_url = response_data.get(pagination_key)
                else:
                    # No pagination, stop after first page
                    break

                page += 1

            except Exception as e:
                print(f"❌ Error on page {page}: {e}")
                break

        print(f"✅ Fetched {len(all_data)} total records")
        return all_data

    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            print(f"Testing connection to: {self.base_url}")
            response = self.session.get(self.base_url, timeout=10)

            if response.status_code == 200:
                print(f"✅ Connection successful (status: {response.status_code})")
                return True
            elif response.status_code == 401:
                print(f"❌ Authentication failed (status: {response.status_code})")
                print("   Check your API token")
                return False
            else:
                print(f"⚠️  Unexpected status: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Connection failed: {e}")
            return False


def save_json(data: List[Dict], output_file: str, format_type: str = 'jsonl'):
    """Save data to JSON file"""

    # Create output directory
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    print(f"\nSaving data to: {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        if format_type == 'jsonl':
            # JSON Lines format (one object per line)
            for record in data:
                f.write(json.dumps(record) + '\n')
        else:
            # Standard JSON array
            json.dump(data, f, indent=2)

    print(f"✅ Saved {len(data)} records")


def create_sample(input_file: str, output_file: str, sample_size: int):
    """Create sample file from collected data"""

    print(f"\nCreating sample file...")

    with open(input_file, 'r', encoding='utf-8') as f:
        # Read first N lines (JSONL format)
        sample_data = []
        for i, line in enumerate(f):
            if i >= sample_size:
                break
            sample_data.append(json.loads(line))

    save_json(sample_data, output_file, format_type='jsonl')
    print(f"✅ Sample created: {len(sample_data)} records")


def main():
    parser = argparse.ArgumentParser(
        description='Collect data from REST APIs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic fetch
  python collect_from_api.py \\
    --url "https://api.example.com/customers" \\
    --output data/raw/customers.json

  # With authentication
  python collect_from_api.py \\
    --url "https://api.example.com/customers" \\
    --output data/raw/customers.json \\
    --auth-token "your_api_token"

  # With pagination
  python collect_from_api.py \\
    --url "https://api.example.com/customers" \\
    --output data/raw/customers.json \\
    --pagination-key "next" \\
    --data-key "results"

  # Test connection only
  python collect_from_api.py \\
    --url "https://api.example.com" \\
    --test-only
        """
    )

    parser.add_argument(
        '--url',
        required=True,
        help='API endpoint URL'
    )

    parser.add_argument(
        '--output',
        help='Output JSON file path'
    )

    parser.add_argument(
        '--auth-token',
        help='Authentication token'
    )

    parser.add_argument(
        '--auth-header',
        default='Authorization',
        help='Authentication header name (default: Authorization)'
    )

    parser.add_argument(
        '--pagination-key',
        help='JSON key for next page URL (e.g., "next", "next_page")'
    )

    parser.add_argument(
        '--data-key',
        help='JSON key containing data array (e.g., "results", "data")'
    )

    parser.add_argument(
        '--max-pages',
        type=int,
        help='Maximum number of pages to fetch'
    )

    parser.add_argument(
        '--rate-limit',
        type=float,
        default=0.0,
        help='Seconds to wait between requests (default: 0)'
    )

    parser.add_argument(
        '--format',
        choices=['json', 'jsonl'],
        default='jsonl',
        help='Output format (default: jsonl)'
    )

    parser.add_argument(
        '--sample',
        type=int,
        help='Create sample file with N records'
    )

    parser.add_argument(
        '--test-only',
        action='store_true',
        help='Only test connection, do not fetch data'
    )

    args = parser.parse_args()

    # Parse URL
    parsed_url = urlparse(args.url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    endpoint = parsed_url.path

    # Create collector
    collector = APICollector(
        base_url=base_url,
        auth_token=args.auth_token,
        auth_header=args.auth_header,
        rate_limit=args.rate_limit
    )

    # Test connection
    if not collector.test_connection():
        sys.exit(1)

    if args.test_only:
        print("\n✅ Connection test complete!")
        return

    if not args.output:
        print("❌ --output required when fetching data")
        sys.exit(1)

    # Fetch data
    try:
        data = collector.fetch_all(
            endpoint=endpoint,
            pagination_key=args.pagination_key,
            data_key=args.data_key,
            max_pages=args.max_pages
        )

        if not data:
            print("⚠️  No data retrieved")
            sys.exit(1)

        # Save data
        save_json(data, args.output, format_type=args.format)

        # Create sample if requested
        if args.sample:
            sample_file = args.output.replace('.json', '_sample.json')
            create_sample(args.output, sample_file, args.sample)

        print(f"\n✅ Data collection complete!")
        print(f"\nNext steps:")
        print(f"1. Review collected data: {args.output}")
        print(f"2. Proceed to Module 3 (Data Quality Evaluation)")
        print(f"3. Then Module 4 (Data Mapping)")

    except Exception as e:
        print(f"\n❌ Data collection failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
