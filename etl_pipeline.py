#!/usr/bin/env python3
"""
Retail Price ETL Pipeline - Standalone Script
==============================================

This script performs the complete ETL process for retail price data
from Naivas and Quickmart stores.

Usage:
    python etl_pipeline.py

Requirements:
    - pandas
    - openpyxl (for Excel files)
    - Scripts/etl_to_warehouse.py

Author: Data Analytics Project
Date: April 2026
"""

import pandas as pd
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent / 'scripts'))
from etl_to_warehouse import DataWarehouseETL


class RetailPriceETL:
    """Main ETL pipeline for retail price data"""
    
    def __init__(self, data_folder='Data', db_path='data_warehouse.db'):
        """
        Initialize ETL pipeline
        
        Args:
            data_folder (str): Path to folder containing Naivas/Quickmart data
            db_path (str): Path to SQLite database
        """
        self.data_folder = data_folder
        self.db_path = db_path
        self.df_master = None
        self.df_clean = None
        
    def extract_date_from_filename(self, filename):
        """
        Extract date from filename handling multiple date formats.
        
        Supports:
            - YYYY-MM-DD (e.g., Naivas_CPI_2026-01-01.xlsx)
            - DD-MM-YYYY (e.g., Quickmart_02-02-2026.xlsx)
        
        Args:
            filename (str): Filename to extract date from
            
        Returns:
            pd.Timestamp or None: Extracted date or None if not found
        """
        # Try YYYY-MM-DD format first
        match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if match:
            return pd.to_datetime(match.group(1), format='%Y-%m-%d')
        
        # Try DD-MM-YYYY format
        match = re.search(r'(\d{2}-\d{2}-\d{4})', filename)
        if match:
            return pd.to_datetime(match.group(1), format='%d-%m-%Y')
        
        # If no date found, return None
        print(f"Warning: Could not extract date from filename: {filename}")
        return None
    
    def extract_from_folder(self, folder_path, store_name):
        """
        Extract data from all files in a folder
        
        Args:
            folder_path (str): Path to folder containing data files
            store_name (str): Name of the store (Naivas/Quickmart)
            
        Returns:
            pd.DataFrame: Combined data from all files
        """
        all_data = []
        skipped_files = []
        
        print(f"\n{'='*50}")
        print(f"Extracting {store_name} data from: {folder_path}")
        print(f"{'='*50}")
        
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        for filename in os.listdir(folder_path):
            if filename.endswith(".xlsx") or filename.endswith(".csv"):
                try:
                    # Extract date from filename
                    file_date = self.extract_date_from_filename(filename)
                    
                    if file_date is None:
                        skipped_files.append(filename)
                        continue
                    
                    # Read the file
                    file_path = os.path.join(folder_path, filename)
                    if filename.endswith(".xlsx"):
                        df = pd.read_excel(file_path)
                    else:
                        df = pd.read_csv(file_path)
                    
                    # Add metadata columns
                    df['Date'] = file_date
                    df['Store'] = store_name
                    df['Source_File'] = filename
                    
                    all_data.append(df)
                    print(f"✓ Processed: {filename} ({len(df)} rows)")
                    
                except Exception as e:
                    print(f"✗ Error processing {filename}: {str(e)}")
                    skipped_files.append(filename)
        
        if skipped_files:
            print(f"\n⚠ Skipped {len(skipped_files)} files:")
            for f in skipped_files:
                print(f"  - {f}")
        
        if not all_data:
            raise ValueError(f"No valid data files found in {folder_path}")
        
        # Combine all data
        result_df = pd.concat(all_data, ignore_index=True)
        print(f"\n✓ Total rows extracted: {len(result_df):,}")
        print(f"✓ Date range: {result_df['Date'].min()} to {result_df['Date'].max()}")
        
        return result_df
    
    def extract_all(self):
        """Extract data from all stores"""
        print("\n" + "="*70)
        print("PHASE 1: EXTRACT - Loading Raw Data")
        print("="*70)
        
        # Extract from both stores
        df_naivas = self.extract_from_folder(
            os.path.join(self.data_folder, 'Naivas'), 
            'Naivas'
        )
        df_quickmart = self.extract_from_folder(
            os.path.join(self.data_folder, 'Quickmart'), 
            'Quickmart'
        )
        
        # Combine into master dataframe
        self.df_master = pd.concat([df_naivas, df_quickmart], ignore_index=True)
        self.df_master = self.df_master.sort_values(['Date', 'Store']).reset_index(drop=True)
        
        print("\n" + "="*70)
        print("Extraction Complete!")
        print("="*70)
        print(f"Total Records: {len(self.df_master):,}")
        print(f"Stores: {self.df_master['Store'].unique()}")
        print(f"Date Range: {self.df_master['Date'].min()} to {self.df_master['Date'].max()}")
        
    def clean_price(self, row):
        """
        Clean and extract numeric price from both text and numeric formats
        
        Args:
            row: DataFrame row
            
        Returns:
            float or None: Cleaned price value
        """
        # Try Price column first (can be numeric or text)
        if pd.notna(row['Price']):
            price_val = row['Price']
            # If already numeric, return it
            if isinstance(price_val, (int, float)):
                return float(price_val)
            # If text, clean it
            price_str = str(price_val)
            # Remove "KES", "KSH", non-breaking spaces (\xa0), commas, regular spaces
            price_str = price_str.replace('KES', '').replace('KSH', '').replace('\xa0', '').replace(',', '').strip()
            try:
                return float(price_str)
            except:
                pass
        
        # Try lowercase price column (Quickmart format)
        if pd.notna(row['price']):
            price_str = str(row['price'])
            price_str = price_str.replace('KES', '').replace('KSH', '').replace('\xa0', '').replace(',', '').strip()
            try:
                return float(price_str)
            except:
                pass
        
        return None
    
    def transform(self):
        """Transform and clean the data"""
        print("\n" + "="*70)
        print("PHASE 2: TRANSFORM - Cleaning & Standardizing Data")
        print("="*70)
        
        if self.df_master is None:
            raise ValueError("No data to transform. Run extract_all() first.")
        
        # Step 1: Combine overlapping columns
        print("\n✓ Step 1: Combining overlapping columns...")
        self.df_master['Final_Name'] = self.df_master['Name'].fillna(self.df_master['product_name'])
        self.df_master['Final_Category'] = self.df_master['category'].fillna(self.df_master['Product_Category'])
        self.df_master['Final_Unit'] = self.df_master['Unit'].fillna(self.df_master['unit'])
        self.df_master['Final_Qty'] = self.df_master['Quantity'].fillna(self.df_master['quantity'])
        
        # Step 2: Clean prices
        print("✓ Step 2: Cleaning prices (removing currency symbols, converting to numeric)...")
        self.df_master['Final_Price'] = self.df_master.apply(self.clean_price, axis=1)
        
        # Step 3: Create clean DataFrame
        print("✓ Step 3: Creating standardized DataFrame...")
        self.df_clean = self.df_master[[
            'Date', 'Store', 'Final_Name', 'Final_Price', 
            'Final_Category', 'Final_Unit', 'Final_Qty', 'Source_File'
        ]].copy()
        
        # Rename columns
        self.df_clean.columns = [
            'Date', 'Store', 'Product_Name', 'Price', 
            'Category', 'Unit', 'Quantity', 'Source_File'
        ]
        
        # Data quality report
        print("\n" + "="*70)
        print("Transformation Complete!")
        print("="*70)
        print(f"Total Records: {len(self.df_clean):,}")
        print(f"Records with valid prices: {self.df_clean['Price'].notna().sum():,}")
        print(f"Records with missing prices: {self.df_clean['Price'].isna().sum():,}")
        
        print("\n📊 Price Statistics by Store:")
        print(self.df_clean.groupby('Store')['Price'].agg(['count', 'mean', 'min', 'max']))
        
    def load_to_warehouse(self):
        """Load cleaned data into data warehouse"""
        print("\n" + "="*70)
        print("PHASE 3: LOAD - Inserting into Data Warehouse")
        print("="*70)
        
        if self.df_clean is None:
            raise ValueError("No cleaned data to load. Run transform() first.")
        
        # Initialize warehouse ETL
        etl = DataWarehouseETL(self.db_path)
        
        # Load data
        etl.load_data(self.df_clean)
        
        print("\n✓ Data successfully loaded into warehouse!")
        
    def export_clean_data(self, output_path='Data/master_data_clean.csv'):
        """
        Export cleaned data to CSV
        
        Args:
            output_path (str): Path to save CSV file
        """
        if self.df_clean is None:
            raise ValueError("No cleaned data to export. Run transform() first.")
        
        self.df_clean.to_csv(output_path, index=False)
        print(f"\n✓ Cleaned data exported to: {output_path}")
        
    def run_full_pipeline(self, export_csv=True):
        """
        Run the complete ETL pipeline
        
        Args:
            export_csv (bool): Whether to export cleaned data to CSV
        """
        start_time = datetime.now()
        
        print("\n" + "="*70)
        print("RETAIL PRICE ETL PIPELINE")
        print("="*70)
        print(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Extract
            self.extract_all()
            
            # Transform
            self.transform()
            
            # Load
            self.load_to_warehouse()
            
            # Optional: Export to CSV
            if export_csv:
                self.export_clean_data()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print("\n" + "="*70)
            print("🎉 ETL PIPELINE COMPLETED SUCCESSFULLY!")
            print("="*70)
            print(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Duration: {duration:.2f} seconds")
            print(f"\nNext step: Run warehouse_queries.ipynb for analysis")
            
        except Exception as e:
            print("\n" + "="*70)
            print("❌ ETL PIPELINE FAILED")
            print("="*70)
            print(f"Error: {str(e)}")
            raise


def main():
    """Main entry point for the script"""
    print("Retail Price ETL Pipeline - Standalone Script")
    print("=" * 70)
    
    # Initialize and run pipeline
    etl = RetailPriceETL(
        data_folder='Data',
        db_path='data_warehouse.db'
    )
    
    # Run full pipeline
    etl.run_full_pipeline(export_csv=True)


if __name__ == "__main__":
    main()
