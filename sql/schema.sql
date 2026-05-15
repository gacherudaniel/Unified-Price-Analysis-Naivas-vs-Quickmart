-- ================================================================
-- DATA WAREHOUSE SCHEMA
-- Retail Price Tracking Data Warehouse for Naivas & Quickmart
-- ================================================================

-- Drop existing tables if they exist (for fresh start)
DROP TABLE IF EXISTS fact_prices;
DROP TABLE IF EXISTS dim_products;
DROP TABLE IF EXISTS dim_stores;
DROP TABLE IF EXISTS dim_dates;
DROP TABLE IF EXISTS dim_categories;

-- ================================================================
-- DIMENSION TABLES
-- ================================================================

-- Dimension: Stores
-- Contains information about retail stores
CREATE TABLE dim_stores (
    store_id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Categories
-- Product categories for classification
CREATE TABLE dim_categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Products
-- Master product catalog with standardized information
CREATE TABLE dim_products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name VARCHAR(500) NOT NULL,
    category_id INTEGER,
    unit VARCHAR(50),
    quantity REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES dim_categories(category_id)
);

-- Dimension: Dates
-- Date dimension for time-series analysis
CREATE TABLE dim_dates (
    date_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,
    year INTEGER,
    month INTEGER,
    day INTEGER,
    quarter INTEGER,
    day_of_week INTEGER,
    week_of_year INTEGER,
    month_name VARCHAR(20),
    is_weekend BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================
-- FACT TABLE
-- ================================================================

-- Fact: Prices
-- Central fact table containing price observations
CREATE TABLE fact_prices (
    price_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_id INTEGER NOT NULL,
    store_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    price REAL NOT NULL,
    source_file VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (date_id) REFERENCES dim_dates(date_id),
    FOREIGN KEY (store_id) REFERENCES dim_stores(store_id),
    FOREIGN KEY (product_id) REFERENCES dim_products(product_id)
);

-- ================================================================
-- INDEXES FOR QUERY PERFORMANCE
-- ================================================================

CREATE INDEX idx_fact_prices_date ON fact_prices(date_id);
CREATE INDEX idx_fact_prices_store ON fact_prices(store_id);
CREATE INDEX idx_fact_prices_product ON fact_prices(product_id);
CREATE INDEX idx_fact_prices_date_store ON fact_prices(date_id, store_id);
CREATE INDEX idx_dim_dates_date ON dim_dates(date);
CREATE INDEX idx_dim_products_name ON dim_products(product_name);

-- ================================================================
-- VIEWS FOR COMMON QUERIES
-- ================================================================

-- Drop existing views if they exist
DROP VIEW IF EXISTS vw_price_details;
DROP VIEW IF EXISTS vw_daily_avg_prices;
DROP VIEW IF EXISTS vw_product_price_comparison;

-- View: Complete price information with all dimensions
CREATE VIEW vw_price_details AS
SELECT 
    fp.price_id,
    dd.date,
    dd.year,
    dd.month,
    dd.quarter,
    ds.store_name,
    dp.product_name,
    dc.category_name,
    dp.unit,
    dp.quantity,
    fp.price,
    fp.source_file
FROM fact_prices fp
JOIN dim_dates dd ON fp.date_id = dd.date_id
JOIN dim_stores ds ON fp.store_id = ds.store_id
JOIN dim_products dp ON fp.product_id = dp.product_id
LEFT JOIN dim_categories dc ON dp.category_id = dc.category_id;

-- View: Daily average prices by store
CREATE VIEW vw_daily_avg_prices AS
SELECT 
    dd.date,
    ds.store_name,
    COUNT(*) as product_count,
    AVG(fp.price) as avg_price,
    MIN(fp.price) as min_price,
    MAX(fp.price) as max_price
FROM fact_prices fp
JOIN dim_dates dd ON fp.date_id = dd.date_id
JOIN dim_stores ds ON fp.store_id = ds.store_id
GROUP BY dd.date, ds.store_name;

-- View: Product price comparison across stores
CREATE VIEW vw_product_price_comparison AS
SELECT 
    dp.product_name,
    dc.category_name,
    ds.store_name,
    AVG(fp.price) as avg_price,
    MIN(fp.price) as min_price,
    MAX(fp.price) as max_price,
    COUNT(*) as observation_count
FROM fact_prices fp
JOIN dim_products dp ON fp.product_id = dp.product_id
JOIN dim_stores ds ON fp.store_id = ds.store_id
LEFT JOIN dim_categories dc ON dp.category_id = dc.category_id
GROUP BY dp.product_name, dc.category_name, ds.store_name;
