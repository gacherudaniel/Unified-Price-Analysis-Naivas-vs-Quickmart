"""
Retail Price Analytics Dashboard
Naivas vs Quickmart - Comprehensive Analysis Dashboard

Features:
- Time series analysis with forecasting
- Comparative store analysis
- Interactive filters and drill-downs
- Clustering analysis
- Anomaly detection
- Multiple advanced visualizations
"""

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.seasonal import seasonal_decompose
import scipy.stats as stats

warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Retail Price Analytics Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    h1 {
        color: #1f77b4;
        padding-bottom: 10px;
    }
    h2 {
        color: #ff7f0e;
        padding-top: 20px;
    }
    h3 {
        color: #2ca02c;
    }
    .highlight {
        background-color: #ffeaa7;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #fdcb6e;
    }
    </style>
""", unsafe_allow_html=True)

# Database connection and data loading
@st.cache_data(ttl=600)
def load_data():
    """Load data from SQLite warehouse"""
    conn = sqlite3.connect('data_warehouse.db')
    
    query = """
    SELECT 
        p.product_name,
        p.unit,
        p.quantity,
        CAST(p.quantity AS TEXT) || p.unit as size,
        c.category_name,
        s.store_name,
        d.date,
        d.year,
        d.month,
        d.week_of_year as week,
        f.price
    FROM fact_prices f
    JOIN dim_products p ON f.product_id = p.product_id
    JOIN dim_stores s ON f.store_id = s.store_id
    JOIN dim_dates d ON f.date_id = d.date_id
    JOIN dim_categories c ON p.category_id = c.category_id
    WHERE f.price > 0
    """
    
    df = pd.read_sql_query(query, conn)
    df['date'] = pd.to_datetime(df['date'])
    conn.close()
    
    return df

@st.cache_data
def load_master_data():
    """Load master data CSV as fallback"""
    try:
        df = pd.read_csv('Data/master_data.csv')
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.rename(columns={
            'Date': 'date',
            'Store': 'store_name',
            'Price': 'price',
            'Name': 'product_name',
            'Product_Category': 'category_name'
        })
        # Clean price column
        if df['price'].dtype == 'object':
            df['price'] = df['price'].str.replace(',', '').astype(float)
        df = df[df['price'] > 0]
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# Load data with error handling
try:
    df = load_data()
    if df.empty:
        raise Exception("Database is empty")
except:
    st.warning("Loading from master data file...")
    df = load_master_data()

if df.empty:
    st.error("❌ No data available. Please check data files.")
    st.stop()

# Sidebar filters
st.sidebar.title("🎛️ Dashboard Filters")
st.sidebar.markdown("---")

# Date range filter
min_date = df['date'].min()
max_date = df['date'].max()

st.sidebar.subheader("📅 Date Range")
date_range = st.sidebar.date_input(
    "Select date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date, end_date = date_range
    df_filtered = df[(df['date'] >= pd.to_datetime(start_date)) & 
                     (df['date'] <= pd.to_datetime(end_date))]
else:
    df_filtered = df.copy()

# Store filter
st.sidebar.subheader("🏪 Store Selection")
stores = ['All'] + sorted(df_filtered['store_name'].unique().tolist())
selected_store = st.sidebar.selectbox("Select Store", stores)

if selected_store != 'All':
    df_filtered = df_filtered[df_filtered['store_name'] == selected_store]

# Category filter
st.sidebar.subheader("📦 Category Selection")
categories = ['All'] + sorted(df_filtered['category_name'].unique().tolist())
selected_category = st.sidebar.selectbox("Select Category", categories)

if selected_category != 'All':
    df_filtered = df_filtered[df_filtered['category_name'] == selected_category]

# Product search
st.sidebar.subheader("🔍 Product Search")
product_search = st.sidebar.text_input("Search product name")

if product_search:
    df_filtered = df_filtered[
        df_filtered['product_name'].str.contains(product_search, case=False, na=False)
    ]

# Price range filter
st.sidebar.subheader("💰 Price Range")
price_min = float(df_filtered['price'].min())
price_max = float(df_filtered['price'].max())
price_range = st.sidebar.slider(
    "Select price range",
    min_value=price_min,
    max_value=price_max,
    value=(price_min, price_max)
)
df_filtered = df_filtered[
    (df_filtered['price'] >= price_range[0]) & 
    (df_filtered['price'] <= price_range[1])
]

st.sidebar.markdown("---")
st.sidebar.info(f"📊 **{len(df_filtered):,}** records after filtering")

# Main dashboard
st.title("🛒 Retail Price Analytics Dashboard")
st.markdown("### Naivas vs Quickmart - Comprehensive Price Analysis")
st.markdown("---")

# Key metrics
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Total Products",
        f"{df_filtered['product_name'].nunique():,}",
        delta=None
    )

with col2:
    st.metric(
        "Average Price",
        f"KES {df_filtered['price'].mean():.2f}",
        delta=None
    )

with col3:
    st.metric(
        "Price Range",
        f"KES {df_filtered['price'].min():.0f} - {df_filtered['price'].max():.0f}",
        delta=None
    )

with col4:
    st.metric(
        "Categories",
        f"{df_filtered['category_name'].nunique()}",
        delta=None
    )

with col5:
    st.metric(
        "Date Range",
        f"{(df_filtered['date'].max() - df_filtered['date'].min()).days} days",
        delta=None
    )

# Create tabs for different analyses
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Time Series Analysis",
    "⚖️ Comparative Analysis",
    "🎯 Clustering Analysis",
    "🚨 Anomaly Detection",
    "🔮 Price Forecasting",
    "📊 Advanced Analytics"
])

# TAB 1: TIME SERIES ANALYSIS
with tab1:
    st.header("📈 Time Series Analysis")
    
    # Time series aggregation
    ts_agg = st.radio(
        "Select aggregation level",
        ['Daily', 'Weekly', 'Monthly'],
        horizontal=True
    )
    
    if ts_agg == 'Daily':
        ts_data = df_filtered.groupby(['date', 'store_name'])['price'].mean().reset_index()
    elif ts_agg == 'Weekly':
        df_filtered['week_start'] = df_filtered['date'] - pd.to_timedelta(df_filtered['date'].dt.dayofweek, unit='d')
        ts_data = df_filtered.groupby(['week_start', 'store_name'])['price'].mean().reset_index()
        ts_data = ts_data.rename(columns={'week_start': 'date'})
    else:  # Monthly
        df_filtered['month_start'] = df_filtered['date'].dt.to_period('M').dt.to_timestamp()
        ts_data = df_filtered.groupby(['month_start', 'store_name'])['price'].mean().reset_index()
        ts_data = ts_data.rename(columns={'month_start': 'date'})
    
    # Plot time series
    fig_ts = px.line(
        ts_data,
        x='date',
        y='price',
        color='store_name',
        title=f'{ts_agg} Average Price Trends by Store',
        labels={'price': 'Average Price (KES)', 'date': 'Date', 'store_name': 'Store'},
        markers=True
    )
    fig_ts.update_layout(
        hovermode='x unified',
        height=500,
        xaxis_title="Date",
        yaxis_title="Average Price (KES)"
    )
    st.plotly_chart(fig_ts, width="stretch")
    
    # Category-wise time series
    st.subheader("Category-wise Price Trends")
    
    top_categories = df_filtered['category_name'].value_counts().head(5).index.tolist()
    df_cat_ts = df_filtered[df_filtered['category_name'].isin(top_categories)]
    
    if ts_agg == 'Daily':
        cat_ts_data = df_cat_ts.groupby(['date', 'category_name'])['price'].mean().reset_index()
    elif ts_agg == 'Weekly':
        cat_ts_data = df_cat_ts.groupby(['week_start', 'category_name'])['price'].mean().reset_index()
        cat_ts_data = cat_ts_data.rename(columns={'week_start': 'date'})
    else:
        cat_ts_data = df_cat_ts.groupby(['month_start', 'category_name'])['price'].mean().reset_index()
        cat_ts_data = cat_ts_data.rename(columns={'month_start': 'date'})
    
    fig_cat = px.line(
        cat_ts_data,
        x='date',
        y='price',
        color='category_name',
        title=f'Top 5 Categories - {ts_agg} Price Trends',
        labels={'price': 'Average Price (KES)', 'date': 'Date', 'category_name': 'Category'}
    )
    fig_cat.update_layout(height=500)
    st.plotly_chart(fig_cat, width="stretch")
    
    # Seasonal decomposition
    st.subheader("Seasonal Decomposition")
    
    if len(ts_data) > 14:  # Need enough data points
        try:
            # Prepare data for decomposition
            store_for_decomp = ts_data['store_name'].unique()[0]
            ts_series = ts_data[ts_data['store_name'] == store_for_decomp].set_index('date')['price']
            
            # Handle missing dates
            ts_series = ts_series.asfreq('D', method='ffill')
            
            if len(ts_series) >= 14:
                decomposition = seasonal_decompose(ts_series, model='additive', period=7)
                
                fig_decomp = make_subplots(
                    rows=4, cols=1,
                    subplot_titles=('Observed', 'Trend', 'Seasonal', 'Residual'),
                    vertical_spacing=0.05
                )
                
                fig_decomp.add_trace(
                    go.Scatter(x=decomposition.observed.index, y=decomposition.observed, name='Observed'),
                    row=1, col=1
                )
                fig_decomp.add_trace(
                    go.Scatter(x=decomposition.trend.index, y=decomposition.trend, name='Trend'),
                    row=2, col=1
                )
                fig_decomp.add_trace(
                    go.Scatter(x=decomposition.seasonal.index, y=decomposition.seasonal, name='Seasonal'),
                    row=3, col=1
                )
                fig_decomp.add_trace(
                    go.Scatter(x=decomposition.resid.index, y=decomposition.resid, name='Residual'),
                    row=4, col=1
                )
                
                fig_decomp.update_layout(height=800, showlegend=False, title_text=f"Seasonal Decomposition - {store_for_decomp}")
                st.plotly_chart(fig_decomp, width="stretch")
        except Exception as e:
            st.warning(f"Unable to perform seasonal decomposition: {e}")

# TAB 2: COMPARATIVE ANALYSIS
with tab2:
    st.header("⚖️ Comparative Store Analysis")
    
    # Overall price comparison
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Average Price by Store")
        store_avg = df_filtered.groupby('store_name')['price'].agg(['mean', 'median', 'std']).reset_index()
        
        fig_store = px.bar(
            store_avg,
            x='store_name',
            y='mean',
            error_y='std',
            title='Average Price by Store (with Std Dev)',
            labels={'mean': 'Average Price (KES)', 'store_name': 'Store'},
            color='store_name',
            text_auto='.2f'
        )
        fig_store.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_store, width="stretch")
        
        st.dataframe(
            store_avg.style.format({
                'mean': 'KES {:.2f}',
                'median': 'KES {:.2f}',
                'std': 'KES {:.2f}'
            }),
            width="stretch"
        )
    
    with col2:
        st.subheader("Price Distribution by Store")
        fig_box = px.box(
            df_filtered,
            x='store_name',
            y='price',
            color='store_name',
            title='Price Distribution Comparison',
            labels={'price': 'Price (KES)', 'store_name': 'Store'}
        )
        fig_box.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_box, width="stretch")
    
    # Category-wise comparison
    st.subheader("Category-wise Price Comparison")
    
    cat_comparison = df_filtered.groupby(['category_name', 'store_name'])['price'].mean().reset_index()
    cat_comparison_pivot = cat_comparison.pivot(index='category_name', columns='store_name', values='price')
    
    if len(cat_comparison_pivot.columns) >= 2:
        cat_comparison_pivot['Difference'] = cat_comparison_pivot.iloc[:, 0] - cat_comparison_pivot.iloc[:, 1]
        cat_comparison_pivot['Diff_%'] = (cat_comparison_pivot['Difference'] / cat_comparison_pivot.iloc[:, 1] * 100).round(2)
    
    fig_cat_comp = px.bar(
        cat_comparison,
        x='category_name',
        y='price',
        color='store_name',
        barmode='group',
        title='Average Price by Category and Store',
        labels={'price': 'Average Price (KES)', 'category_name': 'Category', 'store_name': 'Store'}
    )
    fig_cat_comp.update_layout(height=500, xaxis_tickangle=-45)
    st.plotly_chart(fig_cat_comp, width="stretch")
    
    # Statistical significance test
    if len(df_filtered['store_name'].unique()) == 2:
        st.subheader("Statistical Significance Test")
        
        stores = df_filtered['store_name'].unique()
        store1_prices = df_filtered[df_filtered['store_name'] == stores[0]]['price']
        store2_prices = df_filtered[df_filtered['store_name'] == stores[1]]['price']
        
        t_stat, p_value = stats.ttest_ind(store1_prices, store2_prices)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("T-Statistic", f"{t_stat:.4f}")
        with col2:
            st.metric("P-Value", f"{p_value:.4f}")
        with col3:
            significance = "Significant" if p_value < 0.05 else "Not Significant"
            st.metric("Result", significance)
        
        if p_value < 0.05:
            st.success(f"✅ The price difference between {stores[0]} and {stores[1]} is statistically significant (p < 0.05)")
        else:
            st.info(f"ℹ️ No statistically significant price difference found between stores (p >= 0.05)")
    
    # Top price differences
    st.subheader("Top Price Differences by Product")
    
    if len(df_filtered['store_name'].unique()) >= 2:
        product_comparison = df_filtered.groupby(['product_name', 'store_name'])['price'].mean().reset_index()
        product_pivot = product_comparison.pivot(index='product_name', columns='store_name', values='price')
        product_pivot = product_pivot.dropna()
        
        if len(product_pivot.columns) >= 2:
            product_pivot['Difference'] = abs(product_pivot.iloc[:, 0] - product_pivot.iloc[:, 1])
            product_pivot['Diff_%'] = (product_pivot['Difference'] / product_pivot.min(axis=1) * 100).round(2)
            
            top_diff = product_pivot.nlargest(10, 'Difference').reset_index()
            
            st.dataframe(
                top_diff.style.format({
                    product_pivot.columns[0]: 'KES {:.2f}',
                    product_pivot.columns[1]: 'KES {:.2f}',
                    'Difference': 'KES {:.2f}',
                    'Diff_%': '{:.2f}%'
                }),
                width="stretch"
            )

# TAB 3: CLUSTERING ANALYSIS
with tab3:
    st.header("🎯 Product Clustering Analysis")
    st.markdown("Grouping products based on price patterns and characteristics")
    
    # Prepare features for clustering
    product_features = df_filtered.groupby('product_name').agg({
        'price': ['mean', 'std', 'min', 'max'],
        'store_name': 'count',
        'category_name': 'first'
    }).reset_index()
    
    product_features.columns = ['product_name', 'price_mean', 'price_std', 'price_min', 'price_max', 'count', 'category']
    product_features['price_range'] = product_features['price_max'] - product_features['price_min']
    product_features['price_cv'] = product_features['price_std'] / product_features['price_mean']  # Coefficient of variation
    
    # Fill NaN values
    product_features = product_features.fillna(0)
    
    # Select features for clustering
    features_for_clustering = ['price_mean', 'price_std', 'price_range', 'price_cv']
    X = product_features[features_for_clustering].values
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Number of clusters
    n_clusters = st.slider("Select number of clusters", min_value=2, max_value=8, value=4)
    
    # Perform K-Means clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    product_features['cluster'] = kmeans.fit_predict(X_scaled)
    
    # Visualize clusters
    col1, col2 = st.columns(2)
    
    with col1:
        fig_cluster = px.scatter(
            product_features,
            x='price_mean',
            y='price_std',
            color='cluster',
            hover_data=['product_name', 'category'],
            title='Product Clusters (Price Mean vs Std Dev)',
            labels={'price_mean': 'Average Price (KES)', 'price_std': 'Price Std Dev (KES)', 'cluster': 'Cluster'},
            color_continuous_scale='viridis'
        )
        fig_cluster.update_layout(height=500)
        st.plotly_chart(fig_cluster, width="stretch")
    
    with col2:
        fig_cluster2 = px.scatter(
            product_features,
            x='price_mean',
            y='price_range',
            color='cluster',
            hover_data=['product_name', 'category'],
            title='Product Clusters (Price Mean vs Range)',
            labels={'price_mean': 'Average Price (KES)', 'price_range': 'Price Range (KES)', 'cluster': 'Cluster'},
            color_continuous_scale='viridis'
        )
        fig_cluster2.update_layout(height=500)
        st.plotly_chart(fig_cluster2, width="stretch")
    
    # Cluster characteristics
    st.subheader("Cluster Characteristics")
    
    cluster_summary = product_features.groupby('cluster').agg({
        'product_name': 'count',
        'price_mean': 'mean',
        'price_std': 'mean',
        'price_range': 'mean',
        'price_cv': 'mean'
    }).reset_index()
    
    cluster_summary.columns = ['Cluster', 'Product Count', 'Avg Price', 'Avg Std Dev', 'Avg Price Range', 'Avg CV']
    
    # Add cluster labels
    cluster_labels = []
    for idx, row in cluster_summary.iterrows():
        if row['Avg Price'] < product_features['price_mean'].quantile(0.33):
            if row['Avg CV'] < 0.2:
                label = "Budget - Stable"
            else:
                label = "Budget - Volatile"
        elif row['Avg Price'] < product_features['price_mean'].quantile(0.67):
            if row['Avg CV'] < 0.2:
                label = "Mid-Range - Stable"
            else:
                label = "Mid-Range - Volatile"
        else:
            if row['Avg CV'] < 0.2:
                label = "Premium - Stable"
            else:
                label = "Premium - Volatile"
        cluster_labels.append(label)
    
    cluster_summary['Segment'] = cluster_labels
    
    st.dataframe(
        cluster_summary.style.format({
            'Avg Price': 'KES {:.2f}',
            'Avg Std Dev': 'KES {:.2f}',
            'Avg Price Range': 'KES {:.2f}',
            'Avg CV': '{:.2f}'
        }),
        width="stretch"
    )
    
    # Products in each cluster
    st.subheader("Explore Products by Cluster")
    selected_cluster = st.selectbox("Select cluster to view products", range(n_clusters))
    
    cluster_products = product_features[product_features['cluster'] == selected_cluster][
        ['product_name', 'category', 'price_mean', 'price_std', 'price_range']
    ].sort_values('price_mean', ascending=False)
    
    st.dataframe(
        cluster_products.style.format({
            'price_mean': 'KES {:.2f}',
            'price_std': 'KES {:.2f}',
            'price_range': 'KES {:.2f}'
        }),
        width="stretch"
    )

# TAB 4: ANOMALY DETECTION
with tab4:
    st.header("🚨 Price Anomaly Detection")
    st.markdown("Identifying unusual price points and outliers")
    
    # Prepare data for anomaly detection
    anomaly_features = df_filtered[['product_name', 'price', 'date', 'store_name', 'category_name']].copy()
    
    # Add statistical features
    product_stats = df_filtered.groupby('product_name')['price'].agg(['mean', 'std']).reset_index()
    anomaly_features = anomaly_features.merge(product_stats, on='product_name', how='left')
    anomaly_features['z_score'] = (anomaly_features['price'] - anomaly_features['mean']) / anomaly_features['std']
    anomaly_features = anomaly_features.fillna(0)
    
    # Method selection
    method = st.radio(
        "Select anomaly detection method",
        ['Statistical (Z-Score)', 'Isolation Forest'],
        horizontal=True
    )
    
    if method == 'Statistical (Z-Score)':
        # Z-score threshold
        threshold = st.slider("Z-Score Threshold", min_value=1.5, max_value=4.0, value=2.5, step=0.1)
        
        anomaly_features['is_anomaly'] = abs(anomaly_features['z_score']) > threshold
        anomalies = anomaly_features[anomaly_features['is_anomaly']].copy()
        
        st.info(f"Found **{len(anomalies)}** anomalies using Z-Score > {threshold}")
    
    else:  # Isolation Forest
        # Prepare features
        X_anomaly = anomaly_features[['price']].values
        
        contamination = st.slider("Contamination (% of anomalies expected)", min_value=0.01, max_value=0.20, value=0.05, step=0.01)
        
        iso_forest = IsolationForest(contamination=contamination, random_state=42)
        anomaly_features['is_anomaly'] = iso_forest.fit_predict(X_anomaly) == -1
        anomalies = anomaly_features[anomaly_features['is_anomaly']].copy()
        
        st.info(f"Found **{len(anomalies)}** anomalies using Isolation Forest")
    
    # Visualize anomalies
    col1, col2 = st.columns(2)
    
    with col1:
        fig_anomaly = px.scatter(
            anomaly_features,
            x='date',
            y='price',
            color='is_anomaly',
            hover_data=['product_name', 'store_name'],
            title='Price Anomalies Over Time',
            labels={'price': 'Price (KES)', 'date': 'Date', 'is_anomaly': 'Anomaly'},
            color_discrete_map={True: 'red', False: 'blue'}
        )
        fig_anomaly.update_layout(height=500)
        st.plotly_chart(fig_anomaly, width="stretch")
    
    with col2:
        fig_anomaly_cat = px.histogram(
            anomalies,
            x='category_name',
            title='Anomalies by Category',
            labels={'category_name': 'Category', 'count': 'Number of Anomalies'},
            color='category_name'
        )
        fig_anomaly_cat.update_layout(height=500, showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig_anomaly_cat, width="stretch")
    
    # Top anomalies
    if len(anomalies) > 0:
        st.subheader("Top Price Anomalies")
        
        anomalies_sorted = anomalies.sort_values('z_score', ascending=False, key=abs).head(20)
        
        display_anomalies = anomalies_sorted[[
            'product_name', 'store_name', 'category_name', 'price', 'mean', 'z_score', 'date'
        ]].copy()
        
        st.dataframe(
            display_anomalies.style.format({
                'price': 'KES {:.2f}',
                'mean': 'KES {:.2f}',
                'z_score': '{:.2f}',
                'date': lambda x: x.strftime('%Y-%m-%d')
            }).background_gradient(subset=['z_score'], cmap='RdYlGn_r'),
            width="stretch"
        )
        
        # Anomaly by store
        st.subheader("Anomaly Distribution by Store")
        anomaly_store = anomalies.groupby('store_name').size().reset_index(name='count')
        
        fig_anomaly_store = px.pie(
            anomaly_store,
            values='count',
            names='store_name',
            title='Anomaly Distribution by Store'
        )
        st.plotly_chart(fig_anomaly_store, width="stretch")

# TAB 5: PRICE FORECASTING
with tab5:
    st.header("🔮 Price Forecasting")
    st.markdown("Predicting future price trends using time series models")
    
    # Select product or category for forecasting
    forecast_level = st.radio("Forecast level", ['Category Average', 'Specific Product'], horizontal=True)
    
    if forecast_level == 'Category Average':
        categories_list = sorted(df_filtered['category_name'].unique())
        selected_item = st.selectbox("Select category", categories_list)
        forecast_data = df_filtered[df_filtered['category_name'] == selected_item].groupby('date')['price'].mean().reset_index()
    else:
        products_list = sorted(df_filtered['product_name'].unique())
        selected_item = st.selectbox("Select product", products_list)
        forecast_data = df_filtered[df_filtered['product_name'] == selected_item].groupby('date')['price'].mean().reset_index()
    
    if len(forecast_data) < 10:
        st.warning("⚠️ Not enough data points for forecasting. Please select a different item or adjust filters.")
    else:
        # Prepare time series
        forecast_data = forecast_data.sort_values('date')
        forecast_data = forecast_data.set_index('date')
        ts_forecast = forecast_data['price'].asfreq('D', method='ffill')
        
        # Forecast parameters
        forecast_days = st.slider("Forecast horizon (days)", min_value=7, max_value=90, value=30)
        
        try:
            # Simple exponential smoothing
            model = ExponentialSmoothing(
                ts_forecast,
                seasonal_periods=7,
                trend='add',
                seasonal='add',
                initialization_method='estimated'
            )
            fitted_model = model.fit()
            
            # Generate forecast
            forecast = fitted_model.forecast(steps=forecast_days)
            
            # Create forecast dataframe
            last_date = ts_forecast.index[-1]
            future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=forecast_days, freq='D')
            forecast_df = pd.DataFrame({
                'date': future_dates,
                'forecast': forecast.values
            })
            
            # Calculate confidence intervals (simple approach)
            residuals = fitted_model.fittedvalues - ts_forecast
            std_error = residuals.std()
            forecast_df['lower_bound'] = forecast_df['forecast'] - 1.96 * std_error
            forecast_df['upper_bound'] = forecast_df['forecast'] + 1.96 * std_error
            
            # Plot
            fig_forecast = go.Figure()
            
            # Historical data
            fig_forecast.add_trace(go.Scatter(
                x=ts_forecast.index,
                y=ts_forecast.values,
                mode='lines',
                name='Historical',
                line=dict(color='blue')
            ))
            
            # Forecast
            fig_forecast.add_trace(go.Scatter(
                x=forecast_df['date'],
                y=forecast_df['forecast'],
                mode='lines',
                name='Forecast',
                line=dict(color='red', dash='dash')
            ))
            
            # Confidence interval
            fig_forecast.add_trace(go.Scatter(
                x=forecast_df['date'].tolist() + forecast_df['date'].tolist()[::-1],
                y=forecast_df['upper_bound'].tolist() + forecast_df['lower_bound'].tolist()[::-1],
                fill='toself',
                fillcolor='rgba(255,0,0,0.1)',
                line=dict(color='rgba(255,0,0,0)'),
                showlegend=True,
                name='95% CI'
            ))
            
            fig_forecast.update_layout(
                title=f'Price Forecast: {selected_item}',
                xaxis_title='Date',
                yaxis_title='Price (KES)',
                height=500,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_forecast, width="stretch")
            
            # Forecast summary
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Current Avg Price", f"KES {ts_forecast.iloc[-7:].mean():.2f}")
            
            with col2:
                st.metric("Forecast Avg Price", f"KES {forecast_df['forecast'].mean():.2f}")
            
            with col3:
                change = ((forecast_df['forecast'].mean() - ts_forecast.iloc[-7:].mean()) / ts_forecast.iloc[-7:].mean() * 100)
                st.metric("Expected Change", f"{change:.2f}%", delta=f"{change:.2f}%")
            
            with col4:
                st.metric("Forecast Range", f"KES {forecast_df['forecast'].min():.2f} - {forecast_df['forecast'].max():.2f}")
            
            # Detailed forecast table
            with st.expander("View detailed forecast data"):
                st.dataframe(
                    forecast_df.style.format({
                        'forecast': 'KES {:.2f}',
                        'lower_bound': 'KES {:.2f}',
                        'upper_bound': 'KES {:.2f}'
                    }),
                    width="stretch"
                )
        
        except Exception as e:
            st.error(f"Unable to generate forecast: {e}")
            st.info("This may be due to insufficient data or irregular time series. Try selecting a different product or category.")

# TAB 6: ADVANCED ANALYTICS
with tab6:
    st.header("📊 Advanced Analytics")
    
    # Price volatility analysis
    st.subheader("Price Volatility Analysis")
    
    volatility = df_filtered.groupby('product_name')['price'].agg(['std', 'mean']).reset_index()
    volatility['cv'] = (volatility['std'] / volatility['mean']) * 100  # Coefficient of variation as percentage
    volatility = volatility.sort_values('cv', ascending=False).head(20)
    
    fig_volatility = px.bar(
        volatility,
        x='product_name',
        y='cv',
        title='Top 20 Most Volatile Products (Coefficient of Variation)',
        labels={'cv': 'Coefficient of Variation (%)', 'product_name': 'Product'},
        color='cv',
        color_continuous_scale='Reds'
    )
    fig_volatility.update_layout(height=500, xaxis_tickangle=-45, showlegend=False)
    st.plotly_chart(fig_volatility, width="stretch")
    
    # Price correlation heatmap (if multiple stores)
    if len(df_filtered['store_name'].unique()) >= 2:
        st.subheader("Store Price Correlation")
        
        # Get products available in both stores
        products_by_store = df_filtered.groupby('product_name')['store_name'].nunique()
        common_products = products_by_store[products_by_store >= 2].index.tolist()
        
        if len(common_products) > 5:
            df_common = df_filtered[df_filtered['product_name'].isin(common_products[:20])]
            
            price_pivot = df_common.pivot_table(
                index='date',
                columns='store_name',
                values='price',
                aggfunc='mean'
            )
            
            correlation = price_pivot.corr()
            
            fig_corr = px.imshow(
                correlation,
                text_auto='.3f',
                title='Price Correlation Between Stores',
                color_continuous_scale='RdBu_r',
                aspect='auto'
            )
            fig_corr.update_layout(height=400)
            st.plotly_chart(fig_corr, width="stretch")
    
    # Market basket analysis
    st.subheader("Category Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        category_dist = df_filtered.groupby('category_name').size().reset_index(name='count')
        category_dist = category_dist.sort_values('count', ascending=False)
        
        fig_cat_dist = px.pie(
            category_dist.head(10),
            values='count',
            names='category_name',
            title='Top 10 Categories by Product Count'
        )
        st.plotly_chart(fig_cat_dist, width="stretch")
    
    with col2:
        category_price = df_filtered.groupby('category_name')['price'].mean().reset_index()
        category_price = category_price.sort_values('price', ascending=False).head(10)
        
        fig_cat_price = px.bar(
            category_price,
            x='category_name',
            y='price',
            title='Top 10 Most Expensive Categories (Avg Price)',
            labels={'price': 'Average Price (KES)', 'category_name': 'Category'},
            color='price',
            color_continuous_scale='Blues'
        )
        fig_cat_price.update_layout(xaxis_tickangle=-45, showlegend=False)
        st.plotly_chart(fig_cat_price, width="stretch")
    
    # Price distribution histogram
    st.subheader("Overall Price Distribution")
    
    fig_hist = px.histogram(
        df_filtered,
        x='price',
        nbins=50,
        title='Price Distribution',
        labels={'price': 'Price (KES)', 'count': 'Frequency'},
        marginal='box'
    )
    fig_hist.update_layout(height=400)
    st.plotly_chart(fig_hist, width="stretch")
    
    # Summary statistics
    st.subheader("Summary Statistics")
    
    summary_stats = df_filtered['price'].describe()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Mean", f"KES {summary_stats['mean']:.2f}")
        st.metric("Std Dev", f"KES {summary_stats['std']:.2f}")
    
    with col2:
        st.metric("Median", f"KES {summary_stats['50%']:.2f}")
        st.metric("IQR", f"KES {summary_stats['75%'] - summary_stats['25%']:.2f}")
    
    with col3:
        st.metric("Min", f"KES {summary_stats['min']:.2f}")
        st.metric("25th Percentile", f"KES {summary_stats['25%']:.2f}")
    
    with col4:
        st.metric("Max", f"KES {summary_stats['max']:.2f}")
        st.metric("75th Percentile", f"KES {summary_stats['75%']:.2f}")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: gray;'>
        <p>🛒 Retail Price Analytics Dashboard | Data Analytics Project</p>
        <p>Naivas vs Quickmart Price Comparison | Last Updated: {}</p>
    </div>
""".format(datetime.now().strftime('%Y-%m-%d %H:%M')), unsafe_allow_html=True)
