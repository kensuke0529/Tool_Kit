# Tool Kit

## Database Schema (DDL)

- The database schema (tables and relationships) is defined in [`Table.sql`](data_schema/SQL/tables.sql).
- Schema Viz: [Lucid ERD](https://lucid.app/lucidchart/c8f9a16b-6750-4a4a-a5bd-193fa2eaf2b2/edit?viewport_loc=-469%2C635%2C1109%2C559%2C94fcxOAn5dOq&invitationId=inv_f6e46a87-9759-4367-b821-42824750e3f7)

<img src="data_schema/Images/ERD.png" alt="ERD" width="400"/>

---

## Baserow API Pipeline

This pipeline fetches data from three Baserow tables:
- **Companies**
- **Tools**
- **Libraries**

The code for this pipeline is located in the `baserow_api` directory.
Outputs are saved to `baserow_api/data/snapshots/` as JSON.
In `baserow_api/data.ipynb`, we can see the data in a more readable format.

### Setup

Navigate to the `baserow_api` directory:

```bash
cd baserow_api
```

#### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 2. Configure Environment

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

### Usage

#### Run the Fetcher

Ensure you are in the `baserow_api` directory:

```bash
python3 scripts/baserow/fetch_baserow_tables.py
```

#### Expected Output

The script will:
1. Validate your token is configured
2. Fetch all rows from each table with pagination
3. Display progress for each page
4. Run data quality checks
5. Export to JSON format

### Output Files

After running, you'll find in `data/snapshots/`:

- `companies.json`
- `tools.json`
- `libraries.json`
