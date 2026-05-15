"""
Example queries for the retail price data warehouse
====================================================

This file contains example SQL queries demonstrating various
analytical capabilities of the data warehouse.

Usage:
    Run these queries in your notebook or Python script:
    
    import sqlite3
    import pandas as pd
    
    conn = sqlite3.connect('data_warehouse.db')
    df = pd.read_sql_query(query, conn)
    print(df)
    conn.close()
"""

# ================================================================
# BASIC QUERIES
# ================================================================

# Get all products from a specific store
QUERY_STORE_PRODUCTS = """
SELECT DISTINCT 
    product_name,
    category_name,
    COUNT(*) as times_observed
FROM vw_price_details
WHERE store_name = 'Naivas'
GROUP BY product_name, category_name
ORDER BY product_name;
"""

# Get price history for a specific product
QUERY_PRODUCT_HISTORY = """
SELECT 
    date,
    store_name,
    price
FROM vw_price_details
WHERE product_name LIKE '%Maize Meal%'
ORDER BY date, store_name;
"""

# ================================================================
# COMPARATIVE ANALYSIS
# ================================================================

# Price comparison between stores (side-by-side)
QUERY_PRICE_COMPARISON = """
SELECT 
    product_name,
    category_name,
    MAX(CASE WHEN store_name = 'Naivas' THEN avg_price END) as naivas_avg,
    MAX(CASE WHEN store_name = 'Quickmart' THEN avg_price END) as quickmart_avg,
    ROUND(
        MAX(CASE WHEN store_name = 'Naivas' THEN avg_price END) - 
        MAX(CASE WHEN store_name = 'Quickmart' THEN avg_price END), 
        2
    ) as price_difference
FROM vw_product_price_comparison
WHERE observation_count > 3
GROUP BY product_name, category_name
HAVING naivas_avg IS NOT NULL AND quickmart_avg IS NOT NULL
ORDER BY ABS(price_difference) DESC
LIMIT 50;
"""

# Store with better pricing overall
QUERY_BETTER_PRICING = """
WITH store_stats AS (
    SELECT 
        store_name,
        COUNT(*) as total_observations,
        AVG(price) as avg_price,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) as median_price
    FROM vw_price_details
    GROUP BY store_name
)
SELECT * FROM store_stats
ORDER BY avg_price;
"""

# ================================================================
# TIME SERIES ANALYSIS
# ================================================================

# Daily price trends
QUERY_DAILY_TRENDS = """
SELECT 
    date,
    store_name,
    product_count,
    avg_price,
    min_price,
    max_price
FROM vw_daily_avg_prices
WHERE date >= DATE('now', '-30 days')
ORDER BY date DESC, store_name;
"""

# Monthly aggregation
QUERY_MONTHLY_AGGREGATION = """
SELECT 
    year,
    month,
    month_name,
    store_name,
    COUNT(*) as observations,
    ROUND(AVG(price), 2) as avg_price,
    ROUND(MIN(price), 2) as min_price,
    ROUND(MAX(price), 2) as max_price
FROM vw_price_details
GROUP BY year, month, month_name, store_name
ORDER BY year, month, store_name;
"""

# Week-over-week growth
QUERY_WOW_GROWTH = """
WITH weekly_avg AS (
    SELECT 
        week_of_year,
        store_name,
        AVG(price) as avg_price
    FROM vw_price_details
    GROUP BY week_of_year, store_name
),
lagged AS (
    SELECT 
        *,
        LAG(avg_price) OVER (PARTITION BY store_name ORDER BY week_of_year) as prev_week_price
    FROM weekly_avg
)
SELECT 
    week_of_year,
    store_name,
    ROUND(avg_price, 2) as current_avg,
    ROUND(prev_week_price, 2) as previous_avg,
    ROUND(((avg_price - prev_week_price) / prev_week_price) * 100, 2) as pct_change
FROM lagged
WHERE prev_week_price IS NOT NULL
ORDER BY week_of_year DESC, store_name;
"""

# ================================================================
# PRODUCT ANALYSIS
# ================================================================

# Top 20 most expensive products
QUERY_TOP_EXPENSIVE = """
SELECT 
    product_name,
    category_name,
    store_name,
    ROUND(avg_price, 2) as avg_price,
    observation_count
FROM vw_product_price_comparison
ORDER BY avg_price DESC
LIMIT 20;
"""

# Top 20 cheapest products
QUERY_TOP_CHEAPEST = """
SELECT 
    product_name,
    category_name,
    store_name,
    ROUND(avg_price, 2) as avg_price,
    observation_count
FROM vw_product_price_comparison
WHERE avg_price > 0
ORDER BY avg_price ASC
LIMIT 20;
"""

# Most frequently observed products
QUERY_MOST_OBSERVED = """
SELECT 
    product_name,
    category_name,
    COUNT(*) as total_observations,
    COUNT(DISTINCT store_name) as stores_available,
    ROUND(AVG(price), 2) as avg_price
FROM vw_price_details
GROUP BY product_name, category_name
ORDER BY total_observations DESC
LIMIT 30;
"""

# Price volatility (products with highest price variance)
QUERY_PRICE_VOLATILITY = """
SELECT 
    product_name,
    category_name,
    store_name,
    COUNT(*) as observations,
    ROUND(MIN(price), 2) as min_price,
    ROUND(MAX(price), 2) as max_price,
    ROUND(MAX(price) - MIN(price), 2) as price_range,
    ROUND(AVG(price), 2) as avg_price,
    ROUND(((MAX(price) - MIN(price)) / AVG(price)) * 100, 2) as volatility_pct
FROM vw_price_details
GROUP BY product_name, category_name, store_name
HAVING observations > 5
ORDER BY volatility_pct DESC
LIMIT 30;
"""

# ================================================================
# CATEGORY ANALYSIS
# ================================================================

# Category-level statistics
QUERY_CATEGORY_STATS = """
SELECT 
    category_name,
    COUNT(DISTINCT product_name) as unique_products,
    COUNT(*) as total_observations,
    ROUND(AVG(price), 2) as avg_price,
    ROUND(MIN(price), 2) as min_price,
    ROUND(MAX(price), 2) as max_price,
    ROUND(STDEV(price), 2) as price_stddev
FROM vw_price_details
WHERE category_name IS NOT NULL
GROUP BY category_name
ORDER BY avg_price DESC;
"""

# Category comparison by store
QUERY_CATEGORY_BY_STORE = """
SELECT 
    category_name,
    store_name,
    COUNT(DISTINCT product_name) as product_count,
    ROUND(AVG(price), 2) as avg_price
FROM vw_price_details
WHERE category_name IS NOT NULL
GROUP BY category_name, store_name
ORDER BY category_name, store_name;
"""

# ================================================================
# TEMPORAL PATTERNS
# ================================================================

# Weekend vs Weekday pricing
QUERY_WEEKEND_WEEKDAY = """
SELECT 
    store_name,
    CASE WHEN is_weekend = 1 THEN 'Weekend' ELSE 'Weekday' END as day_type,
    COUNT(*) as observations,
    ROUND(AVG(price), 2) as avg_price,
    ROUND(MIN(price), 2) as min_price,
    ROUND(MAX(price), 2) as max_price
FROM vw_price_details
GROUP BY store_name, day_type
ORDER BY store_name, day_type;
"""

# Day-of-week patterns
QUERY_DAY_OF_WEEK = """
SELECT 
    day_of_week,
    CASE day_of_week
        WHEN 0 THEN 'Monday'
        WHEN 1 THEN 'Tuesday'
        WHEN 2 THEN 'Wednesday'
        WHEN 3 THEN 'Thursday'
        WHEN 4 THEN 'Friday'
        WHEN 5 THEN 'Saturday'
        WHEN 6 THEN 'Sunday'
    END as day_name,
    store_name,
    COUNT(*) as observations,
    ROUND(AVG(price), 2) as avg_price
FROM vw_price_details
GROUP BY day_of_week, store_name
ORDER BY day_of_week, store_name;
"""

# ================================================================
# DATA QUALITY CHECKS
# ================================================================

# Check for missing prices
QUERY_MISSING_PRICES = """
SELECT 
    store_name,
    COUNT(*) as total_records,
    SUM(CASE WHEN price IS NULL THEN 1 ELSE 0 END) as missing_prices,
    ROUND(SUM(CASE WHEN price IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as missing_pct
FROM vw_price_details
GROUP BY store_name;
"""

# Products with incomplete data
QUERY_INCOMPLETE_PRODUCTS = """
SELECT 
    product_name,
    COUNT(*) as total_obs,
    SUM(CASE WHEN category_name IS NULL THEN 1 ELSE 0 END) as missing_category,
    SUM(CASE WHEN unit IS NULL THEN 1 ELSE 0 END) as missing_unit,
    SUM(CASE WHEN quantity IS NULL THEN 1 ELSE 0 END) as missing_quantity
FROM vw_price_details
GROUP BY product_name
HAVING missing_category > 0 OR missing_unit > 0 OR missing_quantity > 0
ORDER BY total_obs DESC;
"""

# Date coverage gaps
QUERY_DATE_GAPS = """
WITH date_range AS (
    SELECT 
        MIN(date) as min_date,
        MAX(date) as max_date,
        JULIANDAY(MAX(date)) - JULIANDAY(MIN(date)) + 1 as expected_days
    FROM dim_dates
),
actual_dates AS (
    SELECT COUNT(DISTINCT date) as actual_days
    FROM dim_dates
)
SELECT 
    dr.min_date,
    dr.max_date,
    dr.expected_days,
    ad.actual_days,
    dr.expected_days - ad.actual_days as missing_days
FROM date_range dr, actual_dates ad;
"""

# ================================================================
# SUMMARY STATISTICS
# ================================================================

# Overall warehouse summary
QUERY_WAREHOUSE_SUMMARY = """
SELECT 
    'Total Products' as metric,
    COUNT(DISTINCT product_name) as value
FROM vw_price_details
UNION ALL
SELECT 
    'Total Observations',
    COUNT(*)
FROM fact_prices
UNION ALL
SELECT 
    'Date Range',
    MAX(date) || ' to ' || MIN(date)
FROM dim_dates
UNION ALL
SELECT 
    'Stores',
    COUNT(*)
FROM dim_stores
UNION ALL
SELECT 
    'Categories',
    COUNT(*)
FROM dim_categories;
"""
