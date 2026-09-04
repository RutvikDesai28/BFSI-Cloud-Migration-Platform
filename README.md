# BFSI Cloud Migration Platform

Portfolio project: legacy on-prem SQL Server property management migration to an Azure medallion architecture.

All sample records are synthetic and created for portfolio demonstration only.

## Business Case

Banks, insurers, and REIT asset managers often run critical property and lease operations on legacy SQL Server systems. Reporting can become slow, inconsistent, and difficult to audit when finance teams rely on manual extracts across property, lease, rent, and valuation data.

This project shows a practical migration pattern:

1. Land legacy extracts in a Bronze layer.
2. Standardize and join property and lease data in a Silver layer with PySpark.
3. Publish Gold SQL views for finance and asset management reporting.
4. Add data quality tests so migration issues are caught early.

The first vertical slice answers a simple business question: Which properties generate income, how occupied are they, and what is the annualized yield against market value?

## Architecture

```text
Legacy SQL Server
    -> Bronze raw extracts
    -> Silver PySpark transformations
    -> Gold Synapse-style SQL views
    -> Property income reporting
```

Current repository slice:

```text
sample_data/
  legacy_property.csv
  legacy_lease.csv
src/
  transformations/
    bronze_to_silver_property.py
sql/
  gold_views/
    vw_property_income_summary.sql
tests/
  test_data_quality.py
docs/
  architecture.md
```

## How To Run

Run the data quality tests:

```powershell
python -m unittest discover -s tests
```

Or, if `pytest` is installed:

```powershell
pytest
```

Run the PySpark Silver transformation:

```powershell
pip install -r requirements.txt
python src/transformations/bronze_to_silver_property.py
```

By default, the transformation reads:

- `sample_data/legacy_property.csv`
- `sample_data/legacy_lease.csv`

It writes the Silver property income dataset to:

- `output/silver/property_income`

To write CSV instead of Parquet:

```powershell
python src/transformations/bronze_to_silver_property.py --output-format csv
```

## Gold View

The Gold SQL view is in `sql/gold_views/vw_property_income_summary.sql`.

It expects a Silver table or external table named:

```sql
silver.property_income
```

The view exposes portfolio-ready metrics such as active lease count, occupancy rate, monthly rent roll, annualized rent, market value, income yield, and occupancy band.

## What This Demonstrates

- BFSI / REIT migration storytelling
- Azure medallion architecture thinking
- PySpark transformation structure
- Synapse-style SQL serving layer
- Data quality checks for migration confidence
- A compact, commit-ready vertical slice
