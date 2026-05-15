"""
Unified Price Analysis Dashboard
Naivas vs Quickmart - Reconciling Basket-Level and Brand-Level Comparisons

Based on: unified_price_analysis.ipynb
"""

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import warnings
from scipy import stats
from statsmodels.tsa.holtwinters import ExponentialSmoothing

warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Unified Price Analysis Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {padding: 0rem 1rem;}
    .stMetric {background-color: #f0f2f6; padding: 10px; border-radius: 5px;}
    h1 {color: #1f77b4; padding-bottom: 10px;}
    h2 {color: #ff7f0e; padding-top: 20px;}
    h3 {color: #2ca02c;}
    .highlight-box {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
        color: #212529 !important;
    }
    .highlight-box h4, .highlight-box p, .highlight-box li, .highlight-box strong {
        color: #212529 !important;
    }
    .winner-box {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
        color: #212529 !important;
    }
    .winner-box h3, .winner-box p, .winner-box li, .winner-box strong {
        color: #212529 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Essential basket items definition
ESSENTIAL_BASKET = {
    'Maize Flour 2kg': {'size': '2.0kg', 'cpi_code': 12, 'price_range': (80, 350)},
    'Sugar 2kg': {'size': '2.0kg', 'cpi_code': 84, 'price_range': (120, 400)},
    'Cooking Fat 1kg': {'size': '1.0kg', 'cpi_code': 46, 'price_range': (180, 600)},
    'Cooking Oil 1L': {'size': '1.0l', 'cpi_code': 47, 'price_range': (150, 500)},
    'UHT Milk 1L': {'size': '1.0l', 'cpi_code': 40, 'price_range': (80, 250)},
    'Rice 2kg': {'size': '2.0kg', 'cpi_code': 2, 'price_range': (100, 500)},
    'Wheat Flour 2kg': {'size': '2.0kg', 'cpi_code': 14, 'price_range': (80, 350)},
    'Tea Leaves 250g': {'size': '250.0g', 'cpi_code': 94, 'price_range': (50, 400)},
    'Beans 2kg': {'size': '2.0kg', 'cpi_code': 77, 'price_range': (100, 500)},
    'Pasta 500g': {'size': '500.0g', 'cpi_code': 22, 'price_range': (50, 300)}
}

@st.cache_data(ttl=600)
def load_data():
    """Load and prepare data from warehouse"""
    try:
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
            f.price
        FROM fact_prices f
        JOIN dim_products p ON f.product_id = p.product_id
        JOIN dim_stores s ON f.store_id = s.store_id
        LEFT JOIN dim_categories c ON p.category_id = c.category_id
        JOIN dim_dates d ON f.date_id = d.date_id
        WHERE f.price > 0
        ORDER BY d.date, s.store_name, p.product_name
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        df['date'] = pd.to_datetime(df['date'])
        return df
    
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

def match_essential_item(row):
    """Match product to essential basket items"""
    prod = str(row['product_name']).lower().strip() if pd.notna(row['product_name']) else ''
    size = str(row['size']).lower().strip() if pd.notna(row['size']) else ''
    
    if not prod or not size:
        return None
    
    # Matching logic
    if 'maize' in prod and size == '2.0kg' and ('flour' in prod or 'meal' in prod):
        return 'Maize Flour 2kg'
    if 'sugar' in prod and size == '2.0kg' and 'icing' not in prod:
        return 'Sugar 2kg'
    if size == '1.0kg' and 'fat' in prod and 'cooking' in prod:
        return 'Cooking Fat 1kg'
    if size == '1.0l' and 'oil' in prod and any(x in prod for x in ['cooking', 'salad', 'vegetable', 'sunflower']):
        return 'Cooking Oil 1L'
    if size == '1.0l' and 'milk' in prod and ('uht' in prod or 'long' in prod):
        return 'UHT Milk 1L'
    if size == '2.0kg' and 'rice' in prod and 'flour' not in prod:
        return 'Rice 2kg'
    if size == '2.0kg' and 'flour' in prod and 'wheat' in prod:
        return 'Wheat Flour 2kg'
    if size == '250.0g' and 'tea' in prod:
        return 'Tea Leaves 250g'
    if size == '2.0kg' and 'bean' in prod and 'coffee' not in prod:
        return 'Beans 2kg'
    if size == '500.0g' and any(x in prod for x in ['pasta', 'spaghetti', 'macaroni']):
        return 'Pasta 500g'
    
    return None

def extract_brand(product_name):
    """Extract brand from product name"""
    if pd.isna(product_name):
        return 'Unknown'
    
    name = str(product_name).upper().strip()
    brands = [
        'RAHA', 'SOKO', 'TAIFA', 'PEMBE', 'JOGOO', 'HOSTESS', 'MUMIAS', 'KABRAS',
        'SONY', 'BLUE BAND', 'BLUEBAND', 'KIMBO', 'COWBOY', 'ELIANTO', 'GOLDEN FRY',
        'GOLDENFRY', 'SALIT', 'RINA', 'FRESH FRI', 'BROOKSIDE', 'KCC', 'DAIMA',
        'TUZO', 'PISHORI', 'SINDANO', 'CAPWELL', 'BASMATI', 'KETEPA', 'KERICHO',
        'SAFARI', 'PASTA KING', 'PEPTANG', 'BARILLA'
    ]
    
    for brand in brands:
        if brand in name:
            return brand.title()
    
    words = name.split()
    return words[0].title() if words else 'Unknown'

@st.cache_data
def prepare_basket_data(df):
    """Prepare and filter data for essential basket analysis"""
    # Match basket items
    df['basket_item'] = df.apply(match_essential_item, axis=1)
    df_basket = df[df['basket_item'].notna()].copy()
    
    # Remove outliers
    for item, details in ESSENTIAL_BASKET.items():
        min_price, max_price = details['price_range']
        mask = (df_basket['basket_item'] == item) & \
               ((df_basket['price'] < min_price) | (df_basket['price'] > max_price))
        df_basket = df_basket[~mask]
    
    # Extract brands
    df_basket['brand'] = df_basket['product_name'].apply(extract_brand)
    
    return df_basket

# Load data
df_all = load_data()

if df_all.empty:
    st.error("❌ No data available. Please check database connection.")
    st.stop()

# Prepare basket data
df_basket = prepare_basket_data(df_all)

if df_basket.empty:
    st.warning("⚠️ No basket items matched. Please check data quality.")
    st.stop()

# Sidebar
st.sidebar.title("🎛️ Analysis Filters")
st.sidebar.markdown("---")

# Date range filter
min_date = df_basket['date'].min()
max_date = df_basket['date'].max()

st.sidebar.subheader("📅 Date Range")
date_range = st.sidebar.date_input(
    "Select date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date, end_date = date_range
    df_filtered = df_basket[(df_basket['date'] >= pd.to_datetime(start_date)) & 
                            (df_basket['date'] <= pd.to_datetime(end_date))]
else:
    df_filtered = df_basket.copy()

# Item filter
st.sidebar.subheader("📦 Basket Items")
selected_items = st.sidebar.multiselect(
    "Select items (leave empty for all)",
    options=sorted(df_filtered['basket_item'].unique()),
    default=[]
)

if selected_items:
    df_filtered = df_filtered[df_filtered['basket_item'].isin(selected_items)]

st.sidebar.markdown("---")
st.sidebar.info(f"📊 **{len(df_filtered):,}** observations")

# Main dashboard
st.title("🛒 Unified Price Analysis: Naivas vs Quickmart")
st.markdown("### Reconciling Basket-Level and Brand-Level Pricing Comparisons")
st.markdown("---")

# Introduction box
st.markdown("""
<div class="highlight-box">
<h4>🎯 Which Store Is Cheaper?</h4>
The answer depends on <strong>HOW you shop</strong>:
<ul>
    <li><strong>Budget Shoppers:</strong> Total basket cost matters → Basket Analysis</li>
    <li><strong>Brand-Loyal Shoppers:</strong> Same brand pricing matters → Brand Analysis</li>
    <li><strong>Strategic Shoppers:</strong> Optimize across both approaches</li>
</ul>
</div>
""", unsafe_allow_html=True)

# Create tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Overview",
    "🛒 Basket Analysis",
    "🏷️ Brand Analysis",
    "🔄 Reconciliation",
    "💡 Recommendations",
    "📈 Advanced Analytics"
])

# TAB 1: OVERVIEW
with tab1:
    st.header("📊 Data Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Observations", f"{len(df_filtered):,}")
    
    with col2:
        st.metric("Basket Items", f"{df_filtered['basket_item'].nunique()}")
    
    with col3:
        st.metric("Unique Brands", f"{df_filtered['brand'].nunique()}")
    
    with col4:
        date_span = (df_filtered['date'].max() - df_filtered['date'].min()).days
        st.metric("Date Range (days)", f"{date_span}")
    
    # Essential basket items
    st.subheader("Essential Basket Items (Kenya CPI Aligned)")
    
    basket_info = []
    for item, details in ESSENTIAL_BASKET.items():
        count = len(df_filtered[df_filtered['basket_item'] == item])
        basket_info.append({
            'Item': item,
            'CPI Code': details['cpi_code'],
            'Size': details['size'],
            'Observations': count
        })
    
    df_basket_info = pd.DataFrame(basket_info)
    st.dataframe(df_basket_info, width="stretch")
    
    # Data volume by store
    st.subheader("Data Volume by Store")
    
    store_volume = df_filtered.groupby('store_name').agg({
        'price': 'count',
        'product_name': 'nunique',
        'brand': 'nunique'
    }).reset_index()
    store_volume.columns = ['Store', 'Total Observations', 'Unique Products', 'Unique Brands']
    
    fig_volume = px.bar(
        store_volume,
        x='Store',
        y='Total Observations',
        color='Store',
        title='Observations by Store',
        text_auto=True
    )
    fig_volume.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig_volume, width="stretch")
    
    # Brand selection comparison
    st.subheader("Brand Selection per Item")
    
    brand_counts = df_filtered.groupby(['basket_item', 'store_name'])['brand'].nunique().reset_index()
    brand_pivot = brand_counts.pivot(index='basket_item', columns='store_name', values='brand').fillna(0)
    
    fig_brands = go.Figure()
    for store in brand_pivot.columns:
        fig_brands.add_trace(go.Bar(
            name=store,
            x=brand_pivot.index,
            y=brand_pivot[store],
            text=brand_pivot[store].astype(int),
            textposition='auto'
        ))
    
    fig_brands.update_layout(
        title='Number of Brands per Item by Store',
        xaxis_title='Basket Item',
        yaxis_title='Number of Brands',
        barmode='group',
        height=500,
        xaxis_tickangle=-45
    )
    st.plotly_chart(fig_brands, width="stretch")

# TAB 2: BASKET ANALYSIS
with tab2:
    st.header("🛒 Basket-Level Analysis")

    with st.expander("📋 Methodology", expanded=False):
        st.markdown("""
        **How this analysis works:**

        1. **Data collection** — Daily prices for 10 essential goods (aligned to Kenya's CPI basket) are sourced from both Naivas and Quickmart.
        2. **Averaging across brands** — For each item on each day, prices across *all* available brands are averaged into a single representative price. This reflects the experience of a shopper who picks whichever brand is available.
        3. **Basket cost** — The 10 item averages are summed to produce a single daily total basket cost per store.
        4. **Comparison** — The mean basket cost across all observation days is compared between stores.
        5. **Statistical test** — An independent-samples **t-test** (Welch's) checks whether the observed price difference is statistically significant (α = 0.05).

        > **Limitation:** Because it pools all brands, a store with more budget/economy brands will appear cheaper even if its premium brands are more expensive.
        """)
    
    # Calculate daily basket costs
    df_daily = df_filtered.groupby(['date', 'store_name', 'basket_item'])['price'].mean().reset_index()
    df_basket_totals = df_daily.groupby(['date', 'store_name'])['price'].sum().reset_index()
    df_basket_totals.columns = ['date', 'store_name', 'basket_cost']
    
    # Statistics
    basket_stats = df_basket_totals.groupby('store_name')['basket_cost'].describe()
    
    st.subheader("Basket Cost Statistics")
    st.dataframe(basket_stats.style.format("{:.2f}"), width="stretch")
    
    # Comparison
    store_means = df_basket_totals.groupby('store_name')['basket_cost'].mean()
    
    if len(store_means) >= 2:
        stores = store_means.index.tolist()
        diff = store_means.iloc[0] - store_means.iloc[1]
        cheaper_store_basket = stores[0] if diff < 0 else stores[1]
        savings = abs(diff)
        
        st.markdown(f"""
        <div class="winner-box">
        <h3>📊 Basket Analysis Result</h3>
        <p><strong>{cheaper_store_basket}</strong> is cheaper on average</p>
        <ul>
            <li><strong>Average savings:</strong> KES {savings:.2f} per basket</li>
            <li><strong>Annual savings (52 weeks):</strong> KES {savings * 52:.2f}</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Statistical test
        store1_costs = df_basket_totals[df_basket_totals['store_name'] == stores[0]]['basket_cost']
        store2_costs = df_basket_totals[df_basket_totals['store_name'] == stores[1]]['basket_cost']
        
        t_stat, p_value = stats.ttest_ind(store1_costs, store2_costs)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("T-Statistic", f"{t_stat:.4f}")
        with col2:
            st.metric("P-Value", f"{p_value:.6f}")
        with col3:
            sig = "✅ Significant" if p_value < 0.05 else "❌ Not Significant"
            st.metric("Statistical Test (α=0.05)", sig)
        
        # Visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Basket Cost Distribution")
            fig_dist = go.Figure()
            
            for store in stores:
                data = df_basket_totals[df_basket_totals['store_name'] == store]['basket_cost']
                fig_dist.add_trace(go.Histogram(
                    x=data,
                    name=store,
                    opacity=0.7,
                    nbinsx=20
                ))
            
            fig_dist.update_layout(
                barmode='overlay',
                xaxis_title='Basket Cost (KES)',
                yaxis_title='Frequency',
                height=400
            )
            st.plotly_chart(fig_dist, width="stretch")
        
        with col2:
            st.subheader("Basket Cost Over Time")
            smooth_window = st.slider(
                "Rolling Mean Window (days)", min_value=1, max_value=14, value=7,
                help="1 = raw data, higher = smoother (rolling average over N days)"
            )
            fig_time = go.Figure()
            for store in stores:
                store_data = df_basket_totals[df_basket_totals['store_name'] == store].sort_values('date')
                raw = store_data['basket_cost']
                smoothed = raw.rolling(window=smooth_window, center=True, min_periods=1).mean()
                # Raw data as faint background trace
                fig_time.add_trace(go.Scatter(
                    x=store_data['date'], y=raw,
                    mode='markers', name=f'{store} (raw)',
                    opacity=0.25, showlegend=False,
                    marker=dict(size=4)
                ))
                # Smoothed line as main trace
                fig_time.add_trace(go.Scatter(
                    x=store_data['date'], y=smoothed,
                    mode='lines', name=store,
                    line=dict(width=2.5),
                    line_shape='spline'
                ))
            fig_time.update_layout(
                title=f'Daily Basket Cost Trends ({smooth_window}-day Rolling Mean)',
                xaxis_title='date', yaxis_title='basket_cost',
                height=400
            )
            st.plotly_chart(fig_time, width="stretch")
        
        # Item-level breakdown
        st.subheader("Item-Level Price Comparison (All Brands)")
        
        item_comparison = df_filtered.groupby(['basket_item', 'store_name'])['price'].mean().reset_index()
        item_pivot = item_comparison.pivot(index='basket_item', columns='store_name', values='price')
        
        fig_items = go.Figure()
        for store in item_pivot.columns:
            fig_items.add_trace(go.Bar(
                name=store,
                x=item_pivot.index,
                y=item_pivot[store],
                text=[f'KES {v:.2f}' for v in item_pivot[store]],
                textposition='auto'
            ))
        
        fig_items.update_layout(
            title='Average Price per Item (All Brands)',
            xaxis_title='Item',
            yaxis_title='Average Price (KES)',
            barmode='group',
            height=500,
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig_items, width="stretch")

# TAB 3: BRAND ANALYSIS
with tab3:
    st.header("🏷️ Brand-Level Analysis")

    with st.expander("📋 Methodology", expanded=False):
        st.markdown("""
        **How this analysis works:**

        1. **Brand identification** — Brand names are extracted from product names using keyword matching (e.g., "Pembe Maize Flour" → brand = "Pembe").
        2. **Overlap detection** — For each basket item, the brands stocked at *both* stores are identified. Only these *common brands* are used in the price comparison, which eliminates the effect of different brand mixes.
        3. **Price comparison** — Average prices for each common brand-item pair are computed per store, then compared.
        4. **Difference calculation** — Expressed as: *Naivas price − Quickmart price* (negative = Naivas is cheaper).
        5. **Statistical test** — An independent-samples **t-test** is run per item to check whether the difference is statistically significant (α = 0.05).

        > **Advantage:** Controlling for brand removes selection bias — both stores are compared on a level playing field.
        > **Limitation:** Requires the same brand at both stores, which can reduce sample size for items with low brand overlap.
        """)
    
    # Identify common brands
    brand_overlap = []
    
    for item in sorted(df_filtered['basket_item'].unique()):
        df_item = df_filtered[df_filtered['basket_item'] == item]
        
        naivas_brands = set(df_item[df_item['store_name'] == 'Naivas']['brand'].unique())
        quickmart_brands = set(df_item[df_item['store_name'] == 'Quickmart']['brand'].unique())
        
        common_brands = naivas_brands & quickmart_brands
        total_brands = naivas_brands | quickmart_brands
        overlap_pct = len(common_brands) / len(total_brands) * 100 if total_brands else 0
        
        brand_overlap.append({
            'Item': item,
            'Naivas Brands': len(naivas_brands),
            'Quickmart Brands': len(quickmart_brands),
            'Common Brands': len(common_brands),
            'Overlap %': round(overlap_pct, 1),
            'Common List': ', '.join(sorted(common_brands)) if common_brands else 'None'
        })
    
    df_overlap = pd.DataFrame(brand_overlap)
    
    st.subheader("Brand Overlap Analysis")
    st.dataframe(df_overlap, width="stretch")
    
    # === BRAND VISUALIZATIONS ===
    st.subheader("📊 Brand Distribution Visualizations")
    
    # Get all unique brands by store
    brand_counts = df_filtered.groupby(['store_name', 'basket_item', 'brand']).size().reset_index(name='count')
    
    # 1. Total unique brands per store
    col1, col2 = st.columns(2)
    
    with col1:
        unique_brands_by_store = df_filtered.groupby('store_name')['brand'].nunique().reset_index()
        unique_brands_by_store.columns = ['Store', 'Unique Brands']
        
        fig_brands_store = px.bar(
            unique_brands_by_store,
            x='Store',
            y='Unique Brands',
            title='Total Unique Brands by Store',
            color='Store',
            text='Unique Brands',
            color_discrete_map={'Naivas': '#1f77b4', 'Quickmart': '#ff7f0e'}
        )
        fig_brands_store.update_traces(textposition='outside')
        fig_brands_store.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_brands_store, use_container_width=True)
    
    with col2:
        # Unique brands per item
        brands_per_item = df_filtered.groupby('basket_item')['brand'].nunique().reset_index()
        brands_per_item.columns = ['Item', 'Unique Brands']
        brands_per_item = brands_per_item.sort_values('Unique Brands', ascending=False)
        
        fig_brands_item = px.bar(
            brands_per_item,
            x='Unique Brands',
            y='Item',
            orientation='h',
            title='Unique Brands per Essential Item',
            text='Unique Brands',
            color='Unique Brands',
            color_continuous_scale='Blues'
        )
        fig_brands_item.update_traces(textposition='outside')
        fig_brands_item.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_brands_item, use_container_width=True)
    
    # 2. Brand variety comparison by item and store
    st.markdown("### Brand Variety by Item and Store")
    
    brands_by_item_store = df_filtered.groupby(['basket_item', 'store_name'])['brand'].nunique().reset_index()
    brands_by_item_store.columns = ['Item', 'Store', 'Unique Brands']
    
    fig_variety = px.bar(
        brands_by_item_store,
        x='Item',
        y='Unique Brands',
        color='Store',
        barmode='group',
        title='Brand Variety Comparison: Naivas vs Quickmart',
        text='Unique Brands',
        color_discrete_map={'Naivas': '#1f77b4', 'Quickmart': '#ff7f0e'}
    )
    fig_variety.update_traces(textposition='outside')
    fig_variety.update_layout(height=500, xaxis_tickangle=-45)
    st.plotly_chart(fig_variety, use_container_width=True)
    
    # 3. Top brands by frequency (most common brands)
    st.markdown("### Top Brands by Product Count")
    
    col3, col4 = st.columns(2)
    
    with col3:
        # Naivas top brands
        naivas_brands = df_filtered[df_filtered['store_name'] == 'Naivas']
        naivas_top_brands = naivas_brands.groupby('brand').size().reset_index(name='Product Count')
        naivas_top_brands = naivas_top_brands.sort_values('Product Count', ascending=False).head(10)
        
        fig_naivas_brands = px.bar(
            naivas_top_brands,
            x='Product Count',
            y='brand',
            orientation='h',
            title='Top 10 Brands at Naivas',
            text='Product Count',
            color_discrete_sequence=['#1f77b4']
        )
        fig_naivas_brands.update_traces(textposition='outside')
        fig_naivas_brands.update_layout(height=400, yaxis_title='Brand')
        st.plotly_chart(fig_naivas_brands, use_container_width=True)
    
    with col4:
        # Quickmart top brands
        quickmart_brands = df_filtered[df_filtered['store_name'] == 'Quickmart']
        quickmart_top_brands = quickmart_brands.groupby('brand').size().reset_index(name='Product Count')
        quickmart_top_brands = quickmart_top_brands.sort_values('Product Count', ascending=False).head(10)
        
        fig_quickmart_brands = px.bar(
            quickmart_top_brands,
            x='Product Count',
            y='brand',
            orientation='h',
            title='Top 10 Brands at Quickmart',
            text='Product Count',
            color_discrete_sequence=['#ff7f0e']
        )
        fig_quickmart_brands.update_traces(textposition='outside')
        fig_quickmart_brands.update_layout(height=400, yaxis_title='Brand')
        st.plotly_chart(fig_quickmart_brands, use_container_width=True)
    
    # 4. Brand overlap sunburst chart
    st.markdown("### Brand Overlap Distribution")
    
    # Prepare data for sunburst
    all_brands = df_filtered.groupby(['basket_item', 'brand', 'store_name']).size().reset_index(name='count')
    
    # Determine overlap category for each brand
    brand_store_map = all_brands.groupby(['basket_item', 'brand'])['store_name'].apply(set).reset_index()
    brand_store_map['availability'] = brand_store_map['store_name'].apply(
        lambda x: 'Both Stores' if len(x) == 2 else ('Naivas Only' if 'Naivas' in x else 'Quickmart Only')
    )
    
    overlap_summary = brand_store_map.groupby('availability').size().reset_index(name='Brand Count')
    
    fig_sunburst = px.pie(
        overlap_summary,
        values='Brand Count',
        names='availability',
        title='Brand Availability Across Stores',
        color='availability',
        color_discrete_map={
            'Both Stores': '#2ca02c',
            'Naivas Only': '#1f77b4',
            'Quickmart Only': '#ff7f0e'
        },
        hole=0.4
    )
    fig_sunburst.update_traces(textposition='inside', textinfo='label+percent+value')
    fig_sunburst.update_layout(height=450)
    st.plotly_chart(fig_sunburst, use_container_width=True)
    
    # === END BRAND VISUALIZATIONS ===
    
    # Filter to common brands
    common_brand_data = []
    
    for item in df_filtered['basket_item'].unique():
        df_item = df_filtered[df_filtered['basket_item'] == item]
        
        naivas_brands = set(df_item[df_item['store_name'] == 'Naivas']['brand'].unique())
        quickmart_brands = set(df_item[df_item['store_name'] == 'Quickmart']['brand'].unique())
        common_brands = naivas_brands & quickmart_brands
        
        df_common = df_item[df_item['brand'].isin(common_brands)]
        common_brand_data.append(df_common)
    
    if common_brand_data:
        df_common_brands = pd.concat(common_brand_data, ignore_index=True)
        
        # Price comparison
        brand_comparison = []
        
        for item in sorted(df_common_brands['basket_item'].unique()):
            df_item = df_common_brands[df_common_brands['basket_item'] == item]
            
            naivas_prices = df_item[df_item['store_name'] == 'Naivas']['price']
            quickmart_prices = df_item[df_item['store_name'] == 'Quickmart']['price']
            
            if len(naivas_prices) > 0 and len(quickmart_prices) > 0:
                naivas_mean = naivas_prices.mean()
                quickmart_mean = quickmart_prices.mean()
                diff = naivas_mean - quickmart_mean
                diff_pct = (diff / quickmart_mean) * 100
                
                if len(naivas_prices) > 1 and len(quickmart_prices) > 1:
                    t_stat, p_val = stats.ttest_ind(naivas_prices, quickmart_prices)
                    significant = "Yes" if p_val < 0.05 else "No"
                else:
                    p_val = np.nan
                    significant = "N/A"
                
                brand_comparison.append({
                    'Item': item,
                    'Naivas_Avg': naivas_mean,
                    'Quickmart_Avg': quickmart_mean,
                    'Difference': diff,
                    'Diff_%': diff_pct,
                    'P_Value': p_val,
                    'Significant': significant
                })
        
        df_brand_comp = pd.DataFrame(brand_comparison)
        
        if len(df_brand_comp) > 0:
            st.subheader("Price Comparison: Common Brands Only")
            
            display_df = df_brand_comp.copy()
            display_df['Naivas_Avg'] = display_df['Naivas_Avg'].apply(lambda x: f"KES {x:.2f}")
            display_df['Quickmart_Avg'] = display_df['Quickmart_Avg'].apply(lambda x: f"KES {x:.2f}")
            display_df['Difference'] = display_df['Difference'].apply(lambda x: f"KES {x:.2f}")
            display_df['Diff_%'] = display_df['Diff_%'].apply(lambda x: f"{x:.1f}%")
            display_df['P_Value'] = display_df['P_Value'].apply(lambda x: f"{x:.4f}" if not pd.isna(x) else "N/A")
            
            st.dataframe(display_df, width="stretch")
            
            # Summary
            cheaper_naivas = len(df_brand_comp[df_brand_comp['Difference'] < 0])
            cheaper_quickmart = len(df_brand_comp[df_brand_comp['Difference'] > 0])
            
            if cheaper_naivas > cheaper_quickmart:
                cheaper_store_brand = 'Naivas'
            elif cheaper_quickmart > cheaper_naivas:
                cheaper_store_brand = 'Quickmart'
            else:
                cheaper_store_brand = 'Neither (tied)'
            
            st.markdown(f"""
            <div class="winner-box">
            <h3>📊 Brand Analysis Result</h3>
            <p><strong>{cheaper_store_brand}</strong> has better pricing for same brands</p>
            <ul>
                <li><strong>Items cheaper at Naivas:</strong> {cheaper_naivas}/{len(df_brand_comp)}</li>
                <li><strong>Items cheaper at Quickmart:</strong> {cheaper_quickmart}/{len(df_brand_comp)}</li>
                <li><strong>Statistically significant:</strong> {len(df_brand_comp[df_brand_comp['Significant'] == 'Yes'])}/{len(df_brand_comp)}</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            
            # Visualization
            fig_brand = go.Figure()
            
            colors = ['green' if d < 0 else 'red' for d in df_brand_comp['Difference']]
            
            fig_brand.add_trace(go.Bar(
                x=df_brand_comp['Item'],
                y=df_brand_comp['Difference'],
                marker_color=colors,
                text=[f"KES {d:.2f}" for d in df_brand_comp['Difference']],
                textposition='outside'
            ))
            
            fig_brand.add_hline(y=0, line_dash="dash", line_color="black")
            
            fig_brand.update_layout(
                title='Price Difference (Naivas - Quickmart)<br>Green = Naivas Cheaper, Red = Quickmart Cheaper',
                xaxis_title='Item',
                yaxis_title='Price Difference (KES)',
                height=500,
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig_brand, width="stretch")
        else:
            st.warning("⚠️ No common brands found for selected items.")
    else:
        st.warning("⚠️ No common brands available for comparison.")

# TAB 4: RECONCILIATION
with tab4:
    st.header("🔄 Reconciliation: Understanding the Differences")

    with st.expander("📋 Methodology", expanded=False):
        st.markdown("""
        **Why the two analyses can give different results — and why both are valid:**

        | | Basket Analysis | Brand Analysis |
        |---|---|---|
        | **Unit of comparison** | Total basket cost | Price of identical brand-item |
        | **Brands included** | All brands (pooled) | Common brands only |
        | **What drives the result** | Brand mix + pricing | Pricing power alone |
        | **Most relevant for** | Budget shoppers | Brand-loyal shoppers |

        **Example:** Store A stocks mostly budget brands → lower average basket cost.
        Store B has better prices on shared premium brands → wins brand analysis.
        Both findings can be simultaneously true.
        """)

    st.markdown("""
    <div class="highlight-box">
    <h4>🔍 Why Two Analyses Can Show Different Results</h4>
    <p><strong>Both analyses can be correct simultaneously!</strong> They measure different things:</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get results from both analyses
    if 'cheaper_store_basket' in locals() and 'cheaper_store_brand' in locals():
        
        st.subheader("Summary of Findings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            ### 🛒 Basket Analysis
            **Winner:** {cheaper_store_basket}  
            **Savings:** KES {savings:.2f} per basket  
            **What this measures:** Total checkout cost
            """)
        
        with col2:
            if len(df_brand_comp) > 0:
                st.markdown(f"""
                ### 🏷️ Brand Analysis
                **Winner:** {cheaper_store_brand}  
                **What this measures:** Pricing for identical products
                """)
        
        # Check if results differ
        if cheaper_store_basket != cheaper_store_brand and cheaper_store_brand != 'Neither (tied)':
            st.markdown("""
            <div class="highlight-box">
            <h4>⚠️ RESULTS DIFFER - Here's Why:</h4>
            <ul>
                <li><strong>Basket Analysis Winner:</strong> Lower total cost due to better brand mix (more budget options)</li>
                <li><strong>Brand Analysis Winner:</strong> Better pricing power for premium/same brands</li>
                <li><strong>Key Insight:</strong> Different winners for different shopping styles!</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.subheader("Likely Explanation")
            
            st.write(f"""
            - **{cheaper_store_basket}** likely stocks more budget/economy brands
            - This lowers their **average basket cost**
            - BUT **{cheaper_store_brand}** has better pricing for **identical premium brands**
            - **Result:** Different winners depending on shopping style
            """)
        else:
            st.markdown(f"""
            <div class="winner-box">
            <h4>✅ RESULTS AGREE: {cheaper_store_basket} wins both analyses</h4>
            <p>{cheaper_store_basket} has both:</p>
            <ul>
                <li>Lower total basket cost (better brand mix)</li>
                <li>Better pricing for same brands (pricing power)</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
    
    # Visualization: Brand mix comparison
    st.subheader("Brand Selection Comparison")
    
    brand_counts_pivot = df_filtered.groupby(['basket_item', 'store_name'])['brand'].nunique().unstack(fill_value=0)
    
    fig_mix = go.Figure()
    
    for store in brand_counts_pivot.columns:
        fig_mix.add_trace(go.Bar(
            name=store,
            x=brand_counts_pivot.index,
            y=brand_counts_pivot[store],
            text=brand_counts_pivot[store],
            textposition='auto'
        ))
    
    fig_mix.update_layout(
        title='Number of Brands per Item by Store<br>(More brands = More choice, potential for budget options)',
        xaxis_title='Item',
        yaxis_title='Number of Brands',
        barmode='group',
        height=500,
        xaxis_tickangle=-45
    )
    st.plotly_chart(fig_mix, width="stretch")

# TAB 5: RECOMMENDATIONS
with tab5:
    st.header("💡 Strategic Recommendations")
    
    st.subheader("🛒 For Consumers")
    
    if 'cheaper_store_basket' in locals():
        
        st.markdown(f"""
        ### 1. Budget Shoppers (Price-sensitive, brand-flexible)
        
        **Recommendation:** Shop at **{cheaper_store_basket}**
        
        - **Reason:** Lower total basket cost
        - **Savings:** KES {savings:.2f} per basket, ~KES {savings * 52:.0f} annually
        - **Strategy:** Be flexible with brands, choose store's budget options
        """)
        
        if 'cheaper_store_brand' in locals() and len(df_brand_comp) > 0:
            st.markdown(f"""
            ### 2. Brand-Loyal Shoppers (Prefer specific brands)
            
            **Recommendation:** Shop at **{cheaper_store_brand}** (for common brands)
            
            - **Reason:** Better pricing for same brands
            - **Strategy:** Check which store stocks your preferred brands at lower prices
            """)
            
            # Show item-by-item recommendations
            if len(df_brand_comp[df_brand_comp['Significant'] == 'Yes']) > 0:
                st.markdown("**Item-by-item recommendations:**")
                
                for _, row in df_brand_comp[df_brand_comp['Significant'] == 'Yes'].iterrows():
                    winner = 'Naivas' if row['Difference'] < 0 else 'Quickmart'
                    st.write(f"- **{row['Item']}:** Buy at {winner} (KES {abs(row['Difference']):.2f} savings)")
        
        st.markdown(f"""
        ### 3. Strategic Shoppers (Optimize across stores)
        
        **Recommendation:** Split shopping between stores
        
        - **Strategy:** Leverage each store's strengths
        """)
        
        if 'cheaper_store_brand' in locals() and cheaper_store_basket != cheaper_store_brand:
            st.write(f"- Buy budget brands at: **{cheaper_store_basket}**")
            st.write(f"- Buy premium brands at: **{cheaper_store_brand}**")
        else:
            st.write(f"- **{cheaper_store_basket}** wins both - no need to split")
    
    st.markdown("---")
    st.subheader("📊 For Retailers")
    
    if 'cheaper_store_basket' in locals() and len(store_means) >= 2:
        loser_basket = [s for s in stores if s != cheaper_store_basket][0]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            #### {cheaper_store_basket} (Lower basket cost)
            
            **Strengths:**
            - Better brand mix attracts budget shoppers
            - Competitive on total basket cost
            
            **Strategy:**
            - Emphasize value proposition in marketing
            - Consider adding mid-tier brands for upselling
            
            **Risk:**
            - May be perceived as lower quality
            """)
        
        with col2:
            st.markdown(f"""
            #### {loser_basket} (Higher basket cost)
            
            **Challenge:**
            - Higher average basket cost
            
            **Strategy:**
            - Introduce economy tier for price-sensitive shoppers
            - Promote premium quality positioning
            
            **Opportunity:**
            - Target quality-conscious consumers
            """)

# TAB 6: ADVANCED ANALYTICS
with tab6:
    st.header("📈 Advanced Analytics")
    
    # Price trends over time
    st.subheader("Price Trends Over Time")
    
    selected_item_trend = st.selectbox(
        "Select item for trend analysis",
        options=sorted(df_filtered['basket_item'].unique())
    )
    
    df_trend = df_filtered[df_filtered['basket_item'] == selected_item_trend]
    df_trend_daily = df_trend.groupby(['date', 'store_name'])['price'].mean().reset_index()
    
    trend_smooth_window = st.slider(
        "Rolling Mean Window (days)", min_value=1, max_value=14, value=7,
        help="1 = raw data, higher = smoother (rolling average over N days)",
        key="trend_smooth"
    )
    fig_trend = go.Figure()
    for store in df_trend_daily['store_name'].unique():
        store_data = df_trend_daily[df_trend_daily['store_name'] == store].sort_values('date')
        raw = store_data['price']
        smoothed = raw.rolling(window=trend_smooth_window, center=True, min_periods=1).mean()
        fig_trend.add_trace(go.Scatter(
            x=store_data['date'], y=raw,
            mode='markers', name=f'{store} (raw)',
            opacity=0.25, showlegend=False,
            marker=dict(size=4)
        ))
        fig_trend.add_trace(go.Scatter(
            x=store_data['date'], y=smoothed,
            mode='lines', name=store,
            line=dict(width=2.5),
            line_shape='spline'
        ))
    fig_trend.update_layout(
        title=f'Price Trends: {selected_item_trend} ({trend_smooth_window}-day Rolling Mean)',
        xaxis_title='date', yaxis_title='price',
        height=400
    )
    st.plotly_chart(fig_trend, width="stretch")
    
    # Price forecasting
    st.subheader("🔮 Price Forecasting")

    with st.expander("📋 Forecasting Methodology", expanded=False):
        st.markdown("""
        **Holt-Winters Exponential Smoothing** forecasts future average prices for a selected item and store.

        - **Data preparation:** Daily average prices are computed by averaging across all brands for the selected item-store pair. Missing days are forward-filled.
        - **Model:** Triple exponential smoothing (Holt-Winters Additive) — it decomposes prices into three components:
          - **Level** — the baseline price at any point in time
          - **Trend** — whether prices are rising or falling over time
          - **Seasonality** — recurring weekly patterns (period = 7 days)
        - **Fitting:** Model parameters (α for level, β for trend, γ for seasonality) are optimised automatically via maximum likelihood estimation.
        - **Output:** The fitted model extrapolates the trend and seasonal pattern forward by the selected number of days.
        - **Minimum data:** At least 14 daily observations are required to estimate all three components reliably.

        > **Note:** Forecasts assume past patterns continue. Sudden supply shocks, promotions, or seasonal events will not be captured.
        """)
    
    selected_item_forecast = st.selectbox(
        "Select item for forecasting",
        options=sorted(df_filtered['basket_item'].unique()),
        key='forecast_item'
    )
    
    selected_store_forecast = st.selectbox(
        "Select store",
        options=sorted(df_filtered['store_name'].unique())
    )
    
    df_forecast = df_filtered[
        (df_filtered['basket_item'] == selected_item_forecast) &
        (df_filtered['store_name'] == selected_store_forecast)
    ].groupby('date')['price'].mean().reset_index().set_index('date')
    
    if len(df_forecast) >= 14:
        forecast_days = st.slider("Forecast horizon (days)", 7, 30, 14)
        
        try:
            ts_data = df_forecast['price'].asfreq('D', method='ffill')
            
            model = ExponentialSmoothing(
                ts_data,
                seasonal_periods=7,
                trend='add',
                seasonal='add',
                initialization_method='estimated'
            )
            fitted_model = model.fit()
            forecast = fitted_model.forecast(steps=forecast_days)
            
            fig_forecast = go.Figure()
            
            fig_forecast.add_trace(go.Scatter(
                x=ts_data.index,
                y=ts_data.values,
                mode='lines',
                name='Historical',
                line=dict(color='blue')
            ))
            
            future_dates = pd.date_range(
                start=ts_data.index[-1] + pd.Timedelta(days=1),
                periods=forecast_days,
                freq='D'
            )
            
            fig_forecast.add_trace(go.Scatter(
                x=future_dates,
                y=forecast.values,
                mode='lines',
                name='Forecast',
                line=dict(color='red', dash='dash')
            ))
            
            fig_forecast.update_layout(
                title=f'Price Forecast: {selected_item_forecast} at {selected_store_forecast}',
                xaxis_title='Date',
                yaxis_title='Price (KES)',
                height=400
            )
            st.plotly_chart(fig_forecast, width="stretch")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Current Avg Price", f"KES {ts_data.iloc[-7:].mean():.2f}")
            with col2:
                st.metric("Forecast Avg Price", f"KES {forecast.mean():.2f}")
                
        except Exception as e:
            st.warning(f"Unable to generate forecast: {e}")
    else:
        st.warning("Not enough data points for forecasting. Need at least 14 observations.")

# Footer
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: gray;'>
    <p>🛒 Unified Price Analysis Dashboard | Based on unified_price_analysis.ipynb</p>
    <p>Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</div>
""", unsafe_allow_html=True)
