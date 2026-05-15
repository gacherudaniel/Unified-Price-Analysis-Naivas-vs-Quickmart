# Retail Price Data Analytics Project
## Naivas & Quickmart Price Tracking and Analysis

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0-green.svg)](https://pandas.pydata.org/)
[![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey.svg)](https://www.sqlite.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red.svg)](https://streamlit.io/)

---

## Overview

A complete **ETL pipeline**, **data warehouse**, and **interactive dashboards** for analyzing retail price data from Naivas and Quickmart supermarkets in Kenya.

---

## Project Structure

```
├── README.md                        # This file
├── requirements.txt                 # Python dependencies
│
├── dashboard.py                     # Streamlit dashboard (full analytics)
├── dashboard_unified.py             # Streamlit dashboard (unified price analysis)
├── etl_pipeline.py                  # Standalone ETL script
├── start_dashboard.sh               # Launch dashboard.py
├── start_unified_dashboard.sh       # Launch dashboard_unified.py
│
├── notebooks/                       # Jupyter notebooks (run in order)
│   ├── 01_etl_pipeline.ipynb        # Extract, transform, load data
│   ├── 02_warehouse_queries.ipynb   # SQL queries on the warehouse
│   ├── 03_brand_analysis.ipynb      # Brand overlap & price comparison
│   ├── 04_essential_basket_analysis.ipynb  # Essential goods basket analysis
│   └── 05_unified_price_analysis.ipynb     # Unified store comparison
│
├── scripts/                         # Python modules
│   ├── etl_to_warehouse.py          # Loads data into SQLite warehouse
│   └── example_queries.py           # Reference SQL query examples
│
├── sql/
│   └── schema.sql                   # Data warehouse schema
│
├── Data/                            # Raw source data
│   ├── Naivas/                      # Naivas Excel files (YYYY-MM-DD format)
│   ├── Quickmart/                   # Quickmart Excel files (DD-MM-YYYY format)
│   └── master_data.csv              # Combined master dataset
│
└── outputs/                         # Generated reports & exports
    ├── essential_basket_analysis.html
    ├── unified_price_analysis.html
    ├── brand_overlap_summary.csv
    ├── outliers_removed.csv
    ├── price_comparison_common_brands.csv
    └── weighted_price_analysis.csv
```

---

## Quick Start

### 1. Install dependencies

```bash
python3 -m venv dashboard_env
source dashboard_env/bin/activate
pip install -r requirements.txt
```

### 2. Run the ETL pipeline (first time only)

Open and run `notebooks/01_etl_pipeline.ipynb` to load data into the warehouse.

Or run the standalone script:
```bash
python etl_pipeline.py
```

### 3. Launch a dashboard

```bash
# Full analytics dashboard
./start_dashboard.sh

# Unified price comparison dashboard
./start_unified_dashboard.sh
```

Access at: **http://localhost:8501**

---

## Notebooks (run in order)

| # | Notebook | Description |
|---|----------|-------------|
| 01 | `01_etl_pipeline.ipynb` | ETL: reads Excel files → cleans data → loads into SQLite warehouse |
| 02 | `02_warehouse_queries.ipynb` | Analytical SQL queries: trends, comparisons, summaries |
| 03 | `03_brand_analysis.ipynb` | Brand availability overlap, price comparison by brand |
| 04 | `04_essential_basket_analysis.ipynb` | Essential goods basket (maize, sugar, oil, etc.) tracking |
| 05 | `05_unified_price_analysis.ipynb` | Reconciles basket-level and brand-level price comparisons |

---

## Dashboards

| Script | Description |
|--------|-------------|
| `dashboard.py` | Full analytics: time series, clustering, anomaly detection, 15+ charts |
| `dashboard_unified.py` | Focused on essential basket comparison between stores |

---

## Data Warehouse Schema

Star schema with 4 dimension tables and 1 fact table:

- `dim_stores` — store names (Naivas, Quickmart)
- `dim_categories` — product categories
- `dim_products` — product names, units, quantities
- `dim_dates` — calendar dimensions (year, month, week, etc.)
- `fact_prices` — price observations (links to all dimensions)

Views: `vw_price_details`, `vw_daily_avg_prices`, `vw_product_price_comparison`

---

## Requirements

See `requirements.txt`. Key dependencies:
- `pandas`, `numpy` — data manipulation
- `streamlit`, `plotly` — dashboards & charts
- `scikit-learn`, `statsmodels`, `scipy` — ML & statistics
- `openpyxl` — Excel file reading
# Unified-Price-Analysis-Naivas-vs-Quickmart
