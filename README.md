# Baserow API test

## Overview

This pipeline fetches data from three Baserow tables:
- **Companies**
- **Tools**
- **Libraries**

Outputs are saved to `data/snapshots/` as JSON.
In data.ipynb, we can see the data in a more readable format.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and add your token:

```bash
cp .env.example .env
```

Edit `.env` and add your Baserow token:

```
BASEROW_TOKEN=your_actual_token_here
BASEROW_BASE_URL=https://api.baserow.io
BASEROW_PAGE_SIZE=100
BASEROW_OUTPUT_DIR=data/snapshots
```

## Usage

### Run the Fetcher

Run the script using `python3`:

```bash
python3 scripts/baserow/fetch_baserow_tables.py
```

### Expected Output

The script will:
1. Validate your token is configured
2. Fetch all rows from each table with pagination
3. Display progress for each page
4. Run data quality checks
5. Export to JSON format


## Output Files

After running, you'll find in `data/snapshots/`:

- `companies.json`
- `tools.json`
- `libraries.json`

