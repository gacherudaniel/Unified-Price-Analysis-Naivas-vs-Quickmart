"""
ETL Script: Load Data from Pandas DataFrame to Data Warehouse
=============================================================

This script handles the Extract-Transform-Load process from
cleaned pandas DataFrames into a SQLite data warehouse.

Usage:
    from scripts.etl_to_warehouse import DataWarehouseETL
    
    etl = DataWarehouseETL('data_warehouse.db')
    etl.load_data(df_clean)
"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path


class DataWarehouseETL:
    """ETL pipeline for loading data into the data warehouse"""
    
    def __init__(self, db_path='data_warehouse.db'):
        """
        Initialize the ETL pipeline
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        print(f"✓ Connected to database: {self.db_path}")
        
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("✓ Database connection closed")
            
    def initialize_schema(self, schema_file='sql/schema.sql'):
        """
        Initialize database schema from SQL file
        
        Args:
            schema_file (str): Path to SQL schema file
        """
        print("\n" + "="*70)
        print("Initializing Data Warehouse Schema")
        print("="*70)
        
        # Read schema file
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        # Execute schema
        self.cursor.executescript(schema_sql)
        self.conn.commit()
        print("✓ Schema initialized successfully")
        
    def populate_dim_stores(self, df):
        """Populate store dimension"""
        stores = df['Store'].unique()
        for store in stores:
            self.cursor.execute("""
                INSERT OR IGNORE INTO dim_stores (store_name)
                VALUES (?)
            """, (store,))
        self.conn.commit()
        print(f"✓ Loaded {len(stores)} stores into dim_stores")
        
    def populate_dim_categories(self, df):
        """Populate category dimension"""
        categories = df['Category'].dropna().unique()
        for category in categories:
            self.cursor.execute("""
                INSERT OR IGNORE INTO dim_categories (category_name)
                VALUES (?)
            """, (category,))
        self.conn.commit()
        print(f"✓ Loaded {len(categories)} categories into dim_categories")
        
    def populate_dim_dates(self, df):
        """Populate date dimension with calendar information"""
        dates = pd.to_datetime(df['Date']).dt.date.unique()
        
        for date in dates:
            date_obj = pd.to_datetime(date)
            self.cursor.execute("""
                INSERT OR IGNORE INTO dim_dates 
                (date, year, month, day, quarter, day_of_week, week_of_year, 
                 month_name, is_weekend)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                date,
                date_obj.year,
                date_obj.month,
                date_obj.day,
                date_obj.quarter,
                date_obj.dayofweek,
                date_obj.isocalendar()[1],
                date_obj.strftime('%B'),
                1 if date_obj.dayofweek >= 5 else 0
            ))
        self.conn.commit()
        print(f"✓ Loaded {len(dates)} dates into dim_dates")
        
    def populate_dim_products(self, df):
        """Populate product dimension"""
        # Group by product name to get unique products
        products = df.groupby('Product_Name').agg({
            'Category': 'first',
            'Unit': 'first',
            'Quantity': 'first'
        }).reset_index()
        
        for _, row in products.iterrows():
            # Get category_id
            category_id = None
            if pd.notna(row['Category']):
                self.cursor.execute("""
                    SELECT category_id FROM dim_categories 
                    WHERE category_name = ?
                """, (row['Category'],))
                result = self.cursor.fetchone()
                if result:
                    category_id = result[0]
            
            # Insert product
            self.cursor.execute("""
                INSERT OR IGNORE INTO dim_products 
                (product_name, category_id, unit, quantity)
                VALUES (?, ?, ?, ?)
            """, (
                row['Product_Name'],
                category_id,
                row['Unit'] if pd.notna(row['Unit']) else None,
                row['Quantity'] if pd.notna(row['Quantity']) else None
            ))
        
        self.conn.commit()
        print(f"✓ Loaded {len(products)} products into dim_products")
        
    def populate_fact_prices(self, df):
        """Populate fact table with price observations"""
        print("\nLoading fact_prices...")
        total = len(df)
        loaded = 0
        skipped = 0
        
        for idx, row in df.iterrows():
            # Skip rows with missing critical data
            if pd.isna(row['Price']) or pd.isna(row['Product_Name']):
                skipped += 1
                continue
            
            # Get dimension IDs
            # Date ID
            self.cursor.execute("""
                SELECT date_id FROM dim_dates WHERE date = ?
            """, (row['Date'].date(),))
            date_result = self.cursor.fetchone()
            if not date_result:
                skipped += 1
                continue
            date_id = date_result[0]
            
            # Store ID
            self.cursor.execute("""
                SELECT store_id FROM dim_stores WHERE store_name = ?
            """, (row['Store'],))
            store_result = self.cursor.fetchone()
            if not store_result:
                skipped += 1
                continue
            store_id = store_result[0]
            
            # Product ID
            self.cursor.execute("""
                SELECT product_id FROM dim_products WHERE product_name = ?
            """, (row['Product_Name'],))
            product_result = self.cursor.fetchone()
            if not product_result:
                skipped += 1
                continue
            product_id = product_result[0]
            
            # Insert fact
            self.cursor.execute("""
                INSERT INTO fact_prices 
                (date_id, store_id, product_id, price, source_file)
                VALUES (?, ?, ?, ?, ?)
            """, (
                date_id,
                store_id,
                product_id,
                row['Price'],
                row['Source_File'] if pd.notna(row['Source_File']) else None
            ))
            
            loaded += 1
            
            # Progress indicator
            if (idx + 1) % 10000 == 0:
                print(f"  Processed {idx + 1:,} / {total:,} records...")
        
        self.conn.commit()
        print(f"✓ Loaded {loaded:,} price records into fact_prices")
        if skipped > 0:
            print(f"⚠ Skipped {skipped:,} records due to missing data")
            
    def load_data(self, df, schema_file='sql/schema.sql'):
        """
        Complete ETL pipeline to load data into warehouse
        
        Args:
            df (pd.DataFrame): Cleaned DataFrame with columns:
                - Date, Store, Product_Name, Price, Category, Unit, Quantity, Source_File
            schema_file (str): Path to SQL schema file
        """
        print("\n" + "="*70)
        print("DATA WAREHOUSE ETL PIPELINE")
        print("="*70)
        
        # Connect to database
        self.connect()
        
        # Initialize schema
        self.initialize_schema(schema_file)
        
        # Load dimensions (order matters due to foreign keys)
        print("\nLoading Dimension Tables:")
        print("-" * 70)
        self.populate_dim_stores(df)
        self.populate_dim_categories(df)
        self.populate_dim_dates(df)
        self.populate_dim_products(df)
        
        # Load fact table
        print("\nLoading Fact Table:")
        print("-" * 70)
        self.populate_fact_prices(df)
        
        # Summary
        print("\n" + "="*70)
        print("ETL COMPLETE - Data Warehouse Summary")
        print("="*70)
        self.print_summary()
        
        # Disconnect
        self.disconnect()
        
    def print_summary(self):
        """Print data warehouse summary statistics"""
        tables = ['dim_stores', 'dim_categories', 'dim_dates', 'dim_products', 'fact_prices']
        
        for table in tables:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = self.cursor.fetchone()[0]
            print(f"  {table:.<30} {count:>10,} records")
            
    def execute_query(self, query):
        """
        Execute a SQL query and return results as DataFrame
        
        Args:
            query (str): SQL query to execute
            
        Returns:
            pd.DataFrame: Query results
        """
        return pd.read_sql_query(query, self.conn)


# Example usage function
def main():
    """Example usage of the ETL pipeline"""
    print("This is the ETL module for loading data into the warehouse.")
    print("Import this module in your notebook or script to use it.")
    print("\nExample:")
    print("  from scripts.etl_to_warehouse import DataWarehouseETL")
    print("  etl = DataWarehouseETL('data_warehouse.db')")
    print("  etl.load_data(df_clean)")


if __name__ == "__main__":
    main()
