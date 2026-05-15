# Retail Price Comparison: Naivas vs Quickmart
## A Data Analytics Study of Essential Goods Pricing in Kenya
### Masters Project Submission — May 2026

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Data Sources](#2-data-sources)
3. [Project Workflow & Methodology](#3-project-workflow--methodology)
4. [Data Pipeline & Warehouse](#4-data-pipeline--warehouse)
5. [Essential Basket Definition](#5-essential-basket-definition)
6. [Analysis 1 — Basket-Level Comparison](#6-analysis-1--basket-level-comparison)
7. [Analysis 2 — Brand-Level Comparison](#7-analysis-2--brand-level-comparison)
8. [Reconciliation of Findings](#8-reconciliation-of-findings)
9. [Price Trends & Forecasting](#9-price-trends--forecasting)
10. [Interactive Dashboard](#10-interactive-dashboard)
11. [Conclusion & Recommendations](#11-conclusion--recommendations)
12. [Limitations & Future Work](#12-limitations--future-work)

---

## 1. Project Overview

This project investigates whether **Naivas** or **Quickmart** — two of Kenya's largest supermarket chains — offers lower prices on essential household goods. The study focuses on a basket of **10 core items** aligned with Kenya's Consumer Price Index (CPI) and spans **approximately four months** of daily price data collected from January to April 2026.

The central research question is deceptively simple: *"Which store is cheaper?"* In practice, the answer depends critically on **how the comparison is framed**. This project demonstrates that two analytically valid methodologies — basket-level analysis and brand-level analysis — can yield different conclusions simultaneously, and explains why both results are correct.

The project was conducted in two phases:
- **Phase 1:** Exploratory analysis in Jupyter notebooks (`01` through `05`)
- **Phase 2:** Transition to a production-ready interactive Streamlit dashboard for dynamic filtering and presentation

---

## 2. Data Sources

### 2.1 Naivas Supermarket
- **Website:** [www.naivas.co.ke](https://www.naivas.co.ke)
- **Data format:** Microsoft Excel (`.xlsx`), one file per collection date
- **Date format in filename:** `YYYY-MM-DD` (e.g., `Naivas_CPI_2026-01-15.xlsx`)
- **Collection period:** January 1 – April 23, 2026
- **Files collected:** 148 files
- **Total raw price records loaded:** 193,681
- **Unique products identified:** 6,245
- **Observation days:** 64

### 2.2 Quickmart Supermarket
- **Website:** [www.quickmart.co.ke](https://www.quickmart.co.ke)
- **Data format:** Microsoft Excel (`.xlsx`), one file per collection date
- **Date format in filename:** `DD-MM-YYYY` (e.g., `Quickmart_02-02-2026.xlsx`)
- **Collection period:** January 1 – April 23, 2026
- **Files collected:** 147 files
- **Total raw price records loaded:** 428,787
- **Unique products identified:** 14,444
- **Observation days:** 51

### 2.3 Combined Dataset

| Metric | Naivas | Quickmart | Combined |
|---|---|---|---|
| Price Records | 193,681 | 428,787 | **622,468** |
| Unique Products | 6,245 | 14,444 | — |
| Data Files | 148 | 147 | 295 |
| Observation Days | 64 | 51 | — |

> **Note:** Quickmart had roughly twice the record volume of Naivas, partly reflecting a broader product range and more frequent listing updates on their website. The difference in observation days reflects gaps in file availability for each store during the collection period.

---

## 3. Project Workflow & Methodology

The project followed a structured analytical pipeline progressing from raw data extraction through to interactive visualisation.

### 3.1 Phase 1 — Jupyter Notebook Analysis

The initial analysis was conducted in five Jupyter notebooks, each building on the previous:

| Notebook | Purpose |
|---|---|
| `01_etl_pipeline.ipynb` | Extracted data from Excel files, standardised schemas, handled date format differences, and produced `master_data.csv` |
| `02_warehouse_queries.ipynb` | Explored the data warehouse using SQL queries; validated schema and data quality |
| `03_brand_analysis.ipynb` | Identified common brands across both stores; computed brand overlap statistics and per-brand price comparisons |
| `04_essential_basket_analysis.ipynb` | Defined the 10-item CPI basket, matched products using keyword rules, removed outliers, and computed daily basket costs |
| `05_unified_price_analysis.ipynb` | Consolidated basket-level and brand-level findings; reconciled apparent contradictions between the two approaches |

Each notebook was used to validate logic, explore edge cases, and generate intermediate output files (stored in `outputs/`) before the analysis was finalised.

### 3.2 Phase 2 — Transition to Interactive Dashboard

After completing the notebook analysis, the full pipeline was re-implemented as a **Streamlit web application** (`dashboard_unified.py`). This transition served several purposes:
- Enabled **dynamic filtering** by date range and basket item
- Made findings accessible to non-technical stakeholders without requiring Python knowledge
- Allowed real-time exploration of smoothed price trends and forecasts
- Provided a deployable, shareable URL via Streamlit Community Cloud

---

## 4. Data Pipeline & Warehouse

### 4.1 ETL Process

The Extract, Transform, Load (ETL) pipeline (`etl_pipeline.py` and `scripts/etl_to_warehouse.py`) performed the following steps:

**Extract**
- Iterated over all `.xlsx` files in `Data/Naivas/` and `Data/Quickmart/`
- Parsed dates from filenames using two regex patterns to handle the differing formats (`YYYY-MM-DD` for Naivas, `DD-MM-YYYY` for Quickmart)
- Standardised column names across both sources

**Transform**
- Normalised units (e.g., `KG`, `Kg`, `kg` → `kg`)
- Parsed product quantity (e.g., `"2.0kg"` → `quantity=2.0`, `unit="kg"`)
- Extracted brand names using a curated keyword lookup against 34 known Kenyan retail brands
- Assigned products to categories using keyword rules
- Flagged and removed statistical outliers per item using predefined price bounds aligned to CPI data

**Load**
- Loaded transformed data into a **SQLite data warehouse** (`data_warehouse.db`, 69 MB) using a **star schema**:
  - `dim_stores` — store dimension
  - `dim_products` — product dimension (name, unit, quantity, category)
  - `dim_categories` — category dimension
  - `dim_dates` — date dimension (date, year, month)
  - `fact_prices` — central fact table (price records with foreign keys to all dimensions)

### 4.2 Data Warehouse Schema

```
fact_prices
  ├── store_id    → dim_stores (store_name)
  ├── product_id  → dim_products (product_name, unit, quantity, category_id)
  │                    └── category_id → dim_categories (category_name)
  ├── date_id     → dim_dates (date, year, month)
  └── price
```

---

## 5. Essential Basket Definition

The 10-item basket was constructed to mirror Kenya's National CPI basket categories, focusing on staple foods that represent a significant share of household expenditure for low- and middle-income families.

| Basket Item | Size | CPI Code | Price Range (KES) |
|---|---|---|---|
| Maize Flour | 2 kg | 12 | 80 – 350 |
| Sugar | 2 kg | 84 | 120 – 400 |
| Cooking Fat | 1 kg | 46 | 180 – 600 |
| Cooking Oil | 1 L | 47 | 150 – 500 |
| UHT Milk | 1 L | 40 | 80 – 250 |
| Rice | 2 kg | 2 | 100 – 500 |
| Wheat Flour | 2 kg | 14 | 80 – 350 |
| Tea Leaves | 250 g | 94 | 50 – 400 |
| Beans | 2 kg | 77 | 100 – 500 |
| Pasta | 500 g | 22 | 50 – 300 |

Products were matched to basket items using a rule-based keyword matching function applied to product names and size strings (e.g., a product named `"Pembe Maize Flour"` with size `"2.0Kg"` was assigned to `Maize Flour 2kg`). Prices outside the defined range were treated as outliers and excluded.

After matching and outlier removal, **4,995 observations** were retained:

| Store | Observations | Unique Products |
|---|---|---|
| Naivas | 2,038 | 38 |
| Quickmart | 2,957 | 66 |

> Quickmart had a substantially wider product range within the basket categories (66 products vs Naivas's 38), reflecting a broader brand assortment, particularly in Rice and Maize Flour.

---

## 6. Analysis 1 — Basket-Level Comparison

### 6.1 Methodology

For each observation day and each store, the average price per basket item (across all available brands) was computed, and the 10 item-averages were summed to produce a **daily total basket cost**. The mean daily basket cost was then compared between stores, and a Welch's independent-samples t-test was used to assess statistical significance.

### 6.2 Results

| Store | Average Daily Basket Cost (KES) |
|---|---|
| **Naivas** | **1,250.00** |
| Quickmart | 2,011.63 |

**Naivas is cheaper by KES 761.63 per basket** — a difference of approximately **61%**.

- **T-statistic:** −13.10
- **P-value:** < 0.0001
- **Conclusion:** The difference is **highly statistically significant** (α = 0.05)

At this savings rate, a household shopping once a week would save approximately **KES 39,605 per year** by choosing Naivas over Quickmart.

### 6.3 Item-Level Breakdown (All Brands)

| Item | Naivas Avg (KES) | Quickmart Avg (KES) | Cheaper Store |
|---|---|---|---|
| Cooking Fat 1kg | 287.91 | 328.00 | Naivas |
| Cooking Oil 1L | — | 436.43 | Quickmart only |
| Maize Flour 2kg | 165.11 | 157.34 | Quickmart |
| Pasta 500g | 289.90 | 200.00 | Quickmart |
| Rice 2kg | 301.48 | 340.51 | Naivas |
| Sugar 2kg | 226.54 | 235.54 | Naivas |
| Tea Leaves 250g | — | 172.19 | Quickmart only |
| UHT Milk 1L | 169.00 | 154.39 | Quickmart |
| Wheat Flour 2kg | 161.10 | 159.86 | Comparable |

> **Note:** Cooking Oil 1L and Tea Leaves 250g fell exclusively within Quickmart's matched basket items after outlier filtering; Naivas products in these categories were either outside the size specification or outside the valid price range. Beans 2kg did not return sufficient matched records after filtering in either store.

The large overall basket cost gap is driven substantially by the Rice category and Pasta category, where Quickmart's average prices — when pooled across all its brands — exceed or are comparable to Naivas's. However, this picture changes substantially when brand is controlled for (see Section 7).

---

## 7. Analysis 2 — Brand-Level Comparison

### 7.1 Methodology

Brand names were extracted from product names using a curated keyword list of 34 Kenyan retail brands (e.g., "Pembe", "Jogoo", "Brookside", "Mumias"). For each basket item, only brands available at **both stores** were included in the comparison, ensuring that price differences reflect genuine pricing decisions rather than product mix differences. Welch's t-tests were applied per item.

### 7.2 Brand Overlap

A key finding is that **brand overlap between the two stores is low overall**, particularly for some categories:

| Item | Common Brands | Naivas Only | Quickmart Only | Overlap % |
|---|---|---|---|---|
| Maize Flour 2kg | 11 | 2 | 7 | **55.0%** |
| UHT Milk 1L | 2 (Bio, Brookside) | 1 | 2 | 40.0% |
| Cooking Fat 1kg | 1 (Blue Band) | 1 | 5 | 14.3% |
| Rice 2kg | 3 (Basmati, Daawat, Pishori) | 7 | 18 | 10.7% |
| Sugar 2kg | 1 (Mumias) | 4 | 5 | 10.0% |
| Cooking Oil 1L | 0 | 3 | 2 | 0% |
| Pasta 500g | 0 | 8 | 1 | 0% |
| Tea Leaves 250g | 0 | 0 | 7 | 0% |
| Wheat Flour 2kg | 0 | 5 | 1 | 0% |

Only **5 of the 10 basket items** had common brands for comparison, and for half the basket there was **zero overlap** — meaning it is impossible to make a like-for-like brand comparison for those items.

### 7.3 Results (Common Brands Only)

| Item | Naivas Avg (KES) | Quickmart Avg (KES) | Difference | % Diff | Significant |
|---|---|---|---|---|---|
| Rice 2kg | 1,627.79 | 754.35 | +873.43 | +115.8% | **Yes** (p < 0.0001) |
| UHT Milk 1L | 204.16 | 159.10 | +45.06 | +28.3% | **Yes** (p = 0.0002) |
| Maize Flour 2kg | 267.04 | 230.76 | +36.29 | +15.7% | **Yes** (p = 0.0001) |
| Cooking Fat 1kg | 370.00 | 359.62 | +10.38 | +2.9% | No (p = 0.70) |
| Sugar 2kg | 228.69 | 225.84 | +2.86 | +1.3% | No (p = 0.80) |

**For every item where a valid brand-level comparison was possible, Naivas was more expensive than Quickmart.** Three of these differences were statistically significant:
- **Rice 2kg** — Naivas charges 115.8% more than Quickmart for the same rice brands (Basmati, Daawat, Pishori)
- **UHT Milk 1L** — Naivas charges 28.3% more than Quickmart for Bio and Brookside
- **Maize Flour 2kg** — Naivas charges 15.7% more than Quickmart for shared brands (Jogoo, Pembe, Soko, etc.)

---

## 8. Reconciliation of Findings

The two analyses appear to produce contradictory conclusions:

| Analysis | Winner | Basis |
|---|---|---|
| Basket Analysis | **Naivas** (KES 1,250 vs KES 2,011) | Total cost, all brands |
| Brand Analysis | **Quickmart** (cheaper on 5/5 items) | Same brand, like-for-like |

Both findings are valid simultaneously — they measure different things.

### 8.1 Explanation

The reconciliation centres on **brand mix**. Naivas's basket items are served by a narrower range of products (38 unique products vs Quickmart's 66). Crucially, Naivas's matched basket products skew towards **budget and mid-tier brands**, while Quickmart stocks a broader range that includes more **premium international brands** at higher price points.

The Rice category illustrates this most clearly:
- In the **basket analysis**, Naivas's average rice price is KES 301 because it predominantly matches budget local rice brands.
- In the **brand analysis**, when the comparison is restricted to the three common brands (Basmati, Daawat, Pishori) — all of which are premium — Naivas charges KES 1,628 versus Quickmart's KES 754. Quickmart appears to discount premium rice more aggressively.

The same pattern holds for Maize Flour and Milk: Naivas has more budget-brand representation in its matched data, pulling its all-brand average down, but when the same premium brands are compared directly, Quickmart prices them lower.

### 8.2 Summary

> The answer to *"which store is cheaper?"* depends on the shopper:
>
> - A **price-sensitive, brand-flexible shopper** finds Naivas significantly cheaper overall (KES 761 per basket, a 61% difference).
> - A **brand-loyal shopper** seeking specific brands (Brookside milk, Pembe maize flour, premium rice) will find those same products priced lower at Quickmart in statistically significant terms.

---

## 9. Price Trends & Forecasting

### 9.1 Temporal Coverage

Price data spans **January 1 to April 23, 2026** — approximately 16 weeks. The monthly record distribution shows consistent data availability across both stores:

| Month | Naivas Records | Quickmart Records |
|---|---|---|
| January 2026 | 81,700 | 66,538 |
| February 2026 | 58,691 | 108,504 |
| March 2026 | 52,397 | 159,487 |
| April 2026 | 893 | 94,258 |

> Naivas data collection was significantly reduced in April, resulting in very few Naivas records for that month.

### 9.2 Price Trend Analysis

The dashboard includes item-specific price trend charts with a configurable rolling-mean window (1–14 days). This allows the user to smooth out day-to-day noise and observe underlying trends. Key observable patterns include:
- Maize Flour prices showed relative stability across both stores.
- Rice prices at Naivas were notably more volatile across the observation period.
- Sugar prices remained broadly comparable and stable at both stores.

### 9.3 Price Forecasting

A **Holt-Winters triple exponential smoothing** model (additive trend + additive weekly seasonality, period = 7) was fitted per item-store pair using daily average prices. The model projects prices forward up to 30 days.

The model captures:
- **Level:** The current baseline price
- **Trend:** A rising or falling directional component
- **Seasonality:** Weekly promotional or restocking cycles

> Forecasts should be interpreted as continuations of observed patterns and do not account for exogenous events such as supply disruptions, policy changes, or seasonal harvests.

---

## 10. Interactive Dashboard

Following the Jupyter notebook analysis, the full pipeline was packaged into an interactive **Streamlit** web application (`dashboard_unified.py`) and deployed to **Streamlit Community Cloud**.

### 10.1 Dashboard Structure

The dashboard is organised into six tabs:

| Tab | Content |
|---|---|
| **Overview** | Dataset summary metrics, observation counts by store, brand selection comparison |
| **Basket Analysis** | Daily basket costs, t-test results, distribution charts, time-series trends |
| **Brand Analysis** | Brand overlap statistics, common-brand price comparison, visualisations |
| **Reconciliation** | Side-by-side summary of both analyses, explanation of why results may differ |
| **Recommendations** | Actionable shopping strategies for budget shoppers, brand-loyal shoppers, and strategic shoppers |
| **Advanced Analytics** | Per-item price trends with rolling mean, Holt-Winters price forecasting |

### 10.2 Interactive Features

- **Date range filter** — restrict analysis to any sub-period within the data
- **Item filter** — focus on one or more of the 10 basket items
- **Rolling mean slider** — smooth price trend charts (1–14 day window)
- **Forecast horizon slider** — extend price forecasts up to 30 days
- **Collapsible methodology expanders** — transparent documentation of each analytical method within the relevant tab

### 10.3 Technology Stack

| Component | Technology |
|---|---|
| Data store | SQLite (star schema, `data_warehouse.db`) |
| Dashboard framework | Streamlit ≥ 1.30 |
| Data manipulation | Pandas, NumPy |
| Visualisation | Plotly (Express + Graph Objects) |
| Statistical tests | SciPy (`ttest_ind`) |
| Forecasting | Statsmodels (`ExponentialSmoothing`) |
| Version control | Git / GitHub |

---

## 11. Conclusion & Recommendations

### 11.1 Conclusion

This study analysed 622,468 price records from Naivas and Quickmart supermarkets across a four-month period (January–April 2026), focusing on a 10-item essential goods basket aligned to Kenya's CPI.

The key findings are:

1. **Basket Analysis (all brands):** Naivas is substantially and significantly cheaper. The average daily basket at Naivas costs **KES 1,250** compared to **KES 2,011** at Quickmart — a difference of **KES 762 (61.0%)**, statistically significant at p < 0.0001. Annualised, this represents a potential saving of approximately **KES 39,600** for a household shopping weekly.

2. **Brand Analysis (matched brands):** Quickmart is significantly cheaper. For the three statistically significant comparisons — Rice, Milk, and Maize Flour — Quickmart prices the same brands considerably lower than Naivas, by 115.8%, 28.3%, and 15.7% respectively.

3. **Reconciliation:** These findings are not contradictory. The basket result is driven by Naivas's skew towards budget-brand products. The brand result reflects the fact that when the same premium brands are sold at both stores, Quickmart prices them more competitively. The two stores are targeting different shopper segments.

4. **Brand overlap is limited:** For 5 of the 10 basket items (Cooking Oil, Pasta, Tea, Wheat Flour, and Beans), there were **no common brands** between the two stores, making a like-for-like comparison impossible for half the basket.

### 11.2 Recommendations for Consumers

**Budget Shoppers (price-sensitive, brand-flexible):**
> Shop at **Naivas**. The total basket cost is significantly lower when brand preference is flexible. The estimated annual saving of ~KES 39,600 is meaningful for low- and middle-income households.

**Brand-Loyal Shoppers (committed to specific brands):**
> Shop at **Quickmart** for the brands where a significant price advantage exists — particularly:
> - Premium rice brands (Basmati, Daawat, Pishori): **115.8% cheaper at Quickmart**
> - Brookside / Bio UHT Milk: **28.3% cheaper at Quickmart**
> - Major maize flour brands (Jogoo, Pembe, Soko etc.): **15.7% cheaper at Quickmart**

**Strategic Shoppers:**
> Split shopping between stores. Buy flexible-brand staples (cooking fat, sugar, local maize flour) at Naivas, and purchase specific premium brands — especially rice and milk — at Quickmart.

### 11.3 Recommendations for Retailers

**For Naivas:**
- The current budget-brand assortment is a significant competitive advantage for cost-conscious shoppers and should be retained and emphasised in marketing.
- Consider introducing competitive pricing on the three premium brand categories (rice, milk, maize flour) where Quickmart currently holds a significant price advantage among brand-loyal customers.

**For Quickmart:**
- Despite having lower prices on matched premium brands, Quickmart's overall basket cost is significantly higher due to its product mix skewing towards premium and international brands.
- Introducing or expanding economy-tier SKUs across more basket categories would attract the large segment of budget-sensitive shoppers who currently favour Naivas.
- The broader product range (66 vs 38 products in the basket categories) is a strength for selection but risks positioning the store as expensive for everyday staples.

---

## 12. Limitations & Future Work

### 12.1 Limitations

- **Web scraping variance:** Prices were collected from online listings, which may not always match in-store shelf prices due to online-exclusive promotions or delayed website updates.
- **Incomplete basket coverage:** Beans, Cooking Oil, and Tea Leaves had poor data coverage in one or both stores, limiting comparisons for approximately 30% of the target basket.
- **Short observation period:** Four months of data may not capture seasonal price dynamics (e.g., post-harvest maize flour price drops, festive sugar demand spikes).
- **No location control:** Both chains operate multiple branches across Kenya. The price data may aggregate across branches with different regional pricing, introducing noise.
- **Brand matching limitations:** Brand extraction relied on keyword matching. Products with non-standard naming may have been mis-assigned or grouped under the fallback "first word" heuristic.
- **Unequal observation days:** Naivas had 64 observation days versus 51 for Quickmart. This asymmetry was managed by averaging over all available days, but could introduce temporal bias if the missing days were not random.

### 12.2 Future Work

- **Extend the time series** to 12+ months to capture seasonal effects and longer-term price trends.
- **Geotagging:** Collect store-level data to compare specific Naivas and Quickmart branches in the same geographic area for a more controlled comparison.
- **CPI benchmarking:** Compare observed basket costs against Kenya National Bureau of Statistics (KNBS) official CPI data to contextualise how both stores track national inflation.
- **Consumer surplus analysis:** Combine price data with sales volume data to estimate the total consumer welfare impact of the pricing differences.
- **Automated pipeline:** Schedule the ETL pipeline to collect data automatically at defined intervals, enabling a continuously updated live dashboard.

---

*Prepared by: Daniel Gacheru*  
*Programme: Masters of Science in Computer Science*  
*Date: May 2026*  
*Dashboard: [Streamlit Community Cloud — Unified Price Analysis](https://share.streamlit.io)*  
*Repository: [github.com/gacherudaniel/Unified-Price-Analysis-Naivas-vs-Quickmart](https://github.com/gacherudaniel/Unified-Price-Analysis-Naivas-vs-Quickmart)*
