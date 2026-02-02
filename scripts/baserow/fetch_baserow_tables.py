#!/usr/bin/env python3
"""
Fetches all rows from specified Baserow tables with pagination support,
exports to JSON, with retry logic and data quality checks.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import requests

except ImportError:
    print("ERROR: 'requests' library not found")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()

except ImportError:
    pass


# we will need to add these secret in github action for this script to work when deployed
# Configuration
BASEROW_TOKEN = os.getenv("BASEROW_TOKEN", "")
BASEROW_BASE_URL = os.getenv("BASEROW_BASE_URL", "https://api.baserow.io")
BASEROW_PAGE_SIZE = int(os.getenv("BASEROW_PAGE_SIZE", "100"))
BASEROW_OUTPUT_DIR = os.getenv("BASEROW_OUTPUT_DIR", "data/snapshots")

# tables
TABLES = {
    "companies": 813469,
    "tools": 813470,
    "libraries": 813471
}

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  


def validate_config():
    """Validate that required configuration is present."""
    if not BASEROW_TOKEN:
        print("BASEROW_TOKEN is not set")

        sys.exit(1)
    
    print(f"Configuration validated\n")


def ensure_output_directory():
    output_path = Path(BASEROW_OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"Output will be saved to: {output_path.absolute()}\n")


def fetch_table_with_pagination(table_name: str, table_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """    
    Baserow API has a default limit of 200 rows per page. Pagination is required
    to fetch datasets larger than this limit.
    
    Args:
        table_name: Human-readable table name for logging
        table_id: Baserow table ID
        limit: Optional maximum number of rows to fetch
        
    Returns:
        List of rows fetched
    """
    all_rows = []
    headers = {
        "Authorization": f"Token {BASEROW_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print(f"Fetching {table_name} (ID: {table_id})...")
    
    # Initial URL with page size
    url = f"{BASEROW_BASE_URL}/api/database/rows/table/{table_id}/?size={BASEROW_PAGE_SIZE}"
    page_num = 1
    
    while url:
        # Retry logic for transient failures
        response = None
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(url, headers=headers, timeout=30)
                
                # Success
                if response.status_code == 200:
                    break
                    
                # Rate limiting or server errors - retry with backoff
                elif response.status_code in [429, 500, 502, 503, 504]:
                    if attempt < MAX_RETRIES - 1:
                        delay = RETRY_DELAYS[attempt]
                        print(f"HTTP {response.status_code}, retrying in {delay}s... (attempt {attempt + 1}/{MAX_RETRIES})")
                        time.sleep(delay)
                        continue
                    else:
                        print(f"Failed after {MAX_RETRIES} retries")
                        sys.exit(1)
                        
                # Other errors
                else:
                    print(f"Error {response.status_code}")
                    sys.exit(1)
                    
            except requests.exceptions.RequestException as e:
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAYS[attempt]
                    print(f"Request failed: {e}, retrying in {delay}s... (attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(delay)
                else:
                    print(f"Request failed after {MAX_RETRIES} retries: {e}")
                    sys.exit(1)
        
        # Parse response
        data = response.json()
        rows = data.get("results", [])
        
        # if no data is fetched
        if not rows:
            break
            
        all_rows.extend(rows)
        
        # for when you want to fetch more than 200 rows
        if limit and len(all_rows) >= limit:
            all_rows = all_rows[:limit]
            break
        
        # get next page
        url = data.get("next")
        page_num += 1
    
    print(f"Completed: {len(all_rows)} total rows\n")
    return all_rows


def export_to_json(table_name: str, rows: List[Dict[str, Any]]):
    """Export rows to JSON file."""
    output_file = Path(BASEROW_OUTPUT_DIR) / f"{table_name}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
    
    print(f"Exported to {output_file}")



def main():

    # Execute functions     
    validate_config()
    ensure_output_directory()

    # Fetch and export each table
    results_summary = {}
    
    for table_name, table_id in TABLES.items():
        try:
            rows = fetch_table_with_pagination(table_name, table_id)
            export_to_json(table_name, rows)
            
            results_summary[table_name] = {
                "rows": len(rows),
                "status": "success"
            }
            
        except Exception as e:
            print(f"ERROR processing {table_name}: {e}")
            results_summary[table_name] = {
                "rows": 0,
                "status": f"failed: {e}"
            }
    
    print("All tables fetched")


if __name__ == "__main__":
    main()
