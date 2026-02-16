import pandas as pd
import panel as pn
import hvplot.pandas
from pathlib import Path
import numpy as np
from scipy import stats
import re

pn.extension('tabulator', sizing_mode='stretch_width')

# Data Loading and Preprocessing
data_dir = Path('../baserow_api/data/snapshots')
tools_df = pd.read_json(data_dir / 'tools.json')

# Feature extraction functions
def extract_company(company_list):
    return company_list[0].get('value', 'Unknown') if company_list else 'No Company Data'

def extract_tags_list(tags_list):
    return [tag.get('value', '') for tag in tags_list] if tags_list else []

def extract_tags_str(tags_list):
    tags = extract_tags_list(tags_list)
    return ', '.join(tags) if tags else 'Uncategorized'

# Data transformation pipeline
df = tools_df.copy()
df['Company'] = df['ToolCompany'].apply(extract_company)
df['TagsList'] = df['Tool Tags'].apply(extract_tags_list)
df['Tags'] = df['Tool Tags'].apply(extract_tags_str)
df['Cost'] = pd.to_numeric(df['Annual License Cost'], errors='coerce')
df['Rating'] = pd.to_numeric(df['Overall Rating'], errors='coerce')
df['HasCompany'] = df['Company'] != 'No Company Data'
df['HasTags'] = df['Tags'] != 'Uncategorized'
df['HasCost'] = df['Cost'].notna()
df['HasDescription'] = df['ToolDescription_long'].notna() & (df['ToolDescription_long'] != '')
df['HasRating'] = (df['Rating'].notna()) & (df['Rating'] > 0)

# Market segmentation by cost
def categorize_cost(cost):
    if pd.isna(cost): return 'Unknown'
    if cost == 0: return 'Free'
    if cost < 500: return 'Low (<$500)'
    if cost < 2000: return 'Medium ($500-$2K)'
    if cost < 10000: return 'High ($2K-$10K)'
    return 'Enterprise (>$10K)'

df['CostTier'] = df['Cost'].apply(categorize_cost)

# Statistical Analysis Functions
def calculate_statistics(series):
    """Calculate comprehensive descriptive statistics"""
    clean = series.dropna()
    if len(clean) == 0:
        return {}
    return {
        'count': len(clean),
        'mean': clean.mean(),
        'median': clean.median(),
        'std': clean.std(),
        'min': clean.min(),
        'max': clean.max(),
        'q25': clean.quantile(0.25),
        'q75': clean.quantile(0.75),
        'iqr': clean.quantile(0.75) - clean.quantile(0.25),
        'skewness': stats.skew(clean) if len(clean) > 2 else 0,
        'kurtosis': stats.kurtosis(clean) if len(clean) > 2 else 0
    }

# Filter widgets
search = pn.widgets.TextInput(
    name='Search Tools', 
    placeholder='Enter tool name...', 
    width=300,
    description='Filter by tool name (case-insensitive)'
)

all_companies = sorted([c for c in df['Company'].unique() if c != 'No Company Data'])
all_tags = sorted(list(set([t for tags in df['TagsList'] for t in tags if t])))

company_filter = pn.widgets.MultiChoice(
    name=f'Company Filter — {len(all_companies)} available', 
    options=all_companies,
    width=300
)

tag_filter = pn.widgets.MultiChoice(
    name=f'Category Filter — {len(all_tags)} available', 
    options=all_tags,
    width=300
)

cost_tier_filter = pn.widgets.MultiChoice(
    name='Price Tier Filter',
    options=['Free', 'Low (<$500)', 'Medium ($500-$2K)', 'High ($2K-$10K)', 'Enterprise (>$10K)'],
    width=300
)

reset_button = pn.widgets.Button(
    name='Reset All Filters', 
    button_type='warning',
    width=300
)

def reset_filters(event):
    search.value = ''
    company_filter.value = []
    tag_filter.value = []
    cost_tier_filter.value = []

reset_button.on_click(reset_filters)

@pn.depends(search, company_filter, tag_filter, cost_tier_filter)
def get_filtered_data(search_val, companies, tags, tiers):
    """Apply all filters to the dataset"""
    filtered = df.copy()
    
    if search_val:
        filtered = filtered[filtered['ToolName'].str.contains(search_val, case=False, na=False)]
    
    if companies:
        filtered = filtered[filtered['Company'].isin(companies)]
    
    if tags:
        filtered = filtered[filtered['TagsList'].apply(lambda x: any(t in x for t in tags))]
    
    if tiers:
        filtered = filtered[filtered['CostTier'].isin(tiers)]
    
    return filtered

@pn.depends(search, company_filter, tag_filter, cost_tier_filter)
def stats_cards(search_val, companies, tags, tiers):
    """Generate statistical overview cards"""
    filtered = get_filtered_data(search_val, companies, tags, tiers)
    total = len(filtered)
    
    if total == 0:
        return pn.pane.HTML('<p>No data available</p>')
    
    company_pct = (filtered['HasCompany'].sum() / total * 100) if total > 0 else 0
    tags_pct = (filtered['HasTags'].sum() / total * 100) if total > 0 else 0
    cost_pct = (filtered['HasCost'].sum() / total * 100) if total > 0 else 0
    
    cost_stats = calculate_statistics(filtered['Cost'])
    median_cost = f"${cost_stats['median']:,.0f}" if cost_stats else 'N/A'
    
    html = f'''<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:20px; margin:20px 0">
    <div style="background:#2c3e50; color:white; padding:25px; border-radius:12px; box-shadow:0 4px 6px rgba(0,0,0,0.1)">
        <h2 style="margin:0; font-size:2.5em; font-family: 'Georgia', serif">{total}</h2>
        <p style="margin:8px 0 0 0; opacity:0.9; font-size:0.95em">Total Sample Size</p>
        <p style="margin:4px 0 0 0; opacity:0.7; font-size:0.8em">n — {total}</p>
    </div>
    <div style="background:#34495e; color:white; padding:25px; border-radius:12px; box-shadow:0 4px 6px rgba(0,0,0,0.1)">
        <h2 style="margin:0; font-size:2.5em; font-family: 'Georgia', serif">{company_pct:.0f}%</h2>
        <p style="margin:8px 0 0 0; opacity:0.9; font-size:0.95em">Company Attribution</p>
        <p style="margin:4px 0 0 0; opacity:0.7; font-size:0.8em">{filtered["HasCompany"].sum()} records</p>
    </div>
    <div style="background:#5d6d7e; color:white; padding:25px; border-radius:12px; box-shadow:0 4px 6px rgba(0,0,0,0.1)">
        <h2 style="margin:0; font-size:2.5em; font-family: 'Georgia', serif">{tags_pct:.0f}%</h2>
        <p style="margin:8px 0 0 0; opacity:0.9; font-size:0.95em">Categorized Tools</p>
        <p style="margin:4px 0 0 0; opacity:0.7; font-size:0.8em">{filtered["HasTags"].sum()} with tags</p>
    </div>
    <div style="background:#7f8c8d; color:white; padding:25px; border-radius:12px; box-shadow:0 4px 6px rgba(0,0,0,0.1)">
        <h2 style="margin:0; font-size:2.5em; font-family: 'Georgia', serif">{median_cost}</h2>
        <p style="margin:8px 0 0 0; opacity:0.9; font-size:0.95em">Median Annual Cost</p>
        <p style="margin:4px 0 0 0; opacity:0.7; font-size:0.8em">{cost_pct:.0f}% with pricing</p>
    </div>
    </div>'''
    return pn.pane.HTML(html)

@pn.depends(search, company_filter, tag_filter, cost_tier_filter)
def cost_boxplot(search_val, companies, tags, tiers):
    """Box plot showing cost distribution statistics"""
    filtered = get_filtered_data(search_val, companies, tags, tiers)
    cost_data = filtered[filtered['HasCost']]
    
    if len(cost_data) == 0:
        return pn.pane.Markdown('### Cost Distribution (Box Plot)\n\n*No cost data available*', 
                               styles={'text-align':'center', 'padding':'40px'})
    
    return cost_data.hvplot.box(
        y='Cost',
        title=f'Cost Distribution Analysis — n={len(cost_data)}',
        ylabel='Annual Cost ($)',
        color='#34495e',
        height=400,
        box_fill_color='#95a5a6',
        whisker_color='#2c3e50'
    )

@pn.depends(search, company_filter, tag_filter, cost_tier_filter)
def cost_histogram(search_val, companies, tags, tiers):
    """Histogram with normal distribution overlay"""
    filtered = get_filtered_data(search_val, companies, tags, tiers)
    cost_data = filtered[filtered['HasCost']]['Cost']
    
    if len(cost_data) == 0:
        return pn.pane.Markdown('*No cost data*')
    
    stats_info = calculate_statistics(cost_data)
    
    return cost_data.hvplot.hist(
        title=f'Cost Distribution Histogram — μ=${stats_info["mean"]:,.0f}, σ=${stats_info["std"]:,.0f}',
        bins=25,
        color='#7f8c8d',
        alpha=0.7,
        height=400,
        xlabel='Annual Cost ($)',
        ylabel='Frequency'
    )

@pn.depends(search, company_filter, tag_filter, cost_tier_filter)
def market_segmentation(search_val, companies, tags, tiers):
    """Market segmentation by price tier"""
    filtered = get_filtered_data(search_val, companies, tags, tiers)
    
    tier_counts = filtered['CostTier'].value_counts()
    tier_order = ['Free', 'Low (<$500)', 'Medium ($500-$2K)', 'High ($2K-$10K)', 'Enterprise (>$10K)', 'Unknown']
    tier_counts = tier_counts.reindex([t for t in tier_order if t in tier_counts.index], fill_value=0)
    
    return tier_counts.hvplot.bar(
        title=f'Market Segmentation by Price Tier — n={len(filtered)}',
        color='#5d6d7e',
        height=400,
        ylabel='Number of Tools',
        xlabel='Price Tier',
        rot=45
    )

@pn.depends(search, company_filter, tag_filter, cost_tier_filter)
def company_chart(search_val, companies, tags, tiers):
    filtered = get_filtered_data(search_val, companies, tags, tiers)
    if filtered['HasCompany'].sum() == 0:
        return pn.pane.Markdown('*No company data*')
    data = filtered[filtered['HasCompany']]['Company'].value_counts().head(15)
    return data.hvplot.barh(
        title=f'Top 15 Companies by Tool Count — n={filtered["HasCompany"].sum()}', 
        color='#34495e', 
        height=450,
        xlabel='Number of Tools'
    )

@pn.depends(search, company_filter, tag_filter, cost_tier_filter)
def tag_chart(search_val, companies, tags, tiers):
    filtered = get_filtered_data(search_val, companies, tags, tiers)
    if filtered['HasTags'].sum() == 0:
        return pn.pane.Markdown('*No tag data*')
    tag_counts = {}
    for tlist in filtered[filtered['HasTags']]['TagsList']:
        for t in tlist:
            tag_counts[t] = tag_counts.get(t, 0) + 1
    data = pd.Series(tag_counts).sort_values(ascending=True).tail(15)
    return data.hvplot.barh(
        title=f'Top 15 Categories by Tool Count — n={filtered["HasTags"].sum()}', 
        color='#5d6d7e', 
        height=450,
        xlabel='Number of Tools'
    )

@pn.depends(search, company_filter, tag_filter, cost_tier_filter)
def data_table(search_val, companies, tags, tiers):
    filtered = get_filtered_data(search_val, companies, tags, tiers)
    display = filtered[['ToolName', 'Company', 'Tags', 'Cost', 'Rating', 'CostTier']].copy()
    display.columns = ['Tool', 'Company', 'Categories', 'Annual Cost ($)', 'Rating', 'Price Tier']
    
    return pn.widgets.Tabulator(
        display, 
        page_size=25,
        sizing_mode='stretch_both',
        height=600,
        show_index=False,
        sortable=True,
        configuration={
            'clipboard': True,
            'clipboardCopyRowRange': 'selected'
        }
    )

# Academic-styled template
template = pn.template.FastListTemplate(
    title='Research Tools Landscape Analysis',
    sidebar=[
        pn.pane.Markdown('## Research Controls'),
        pn.pane.Markdown('### Filters'),
        search, 
        company_filter, 
        tag_filter,
        cost_tier_filter,
        pn.pane.Markdown('---'),
        reset_button,
    ],
    main=[
        pn.pane.Markdown('## Overview Statistics'),
        stats_cards,
        pn.pane.Markdown('## Descriptive Statistics'),
        pn.Row(
            pn.Column(cost_boxplot, sizing_mode='stretch_both'),
            pn.Column(cost_histogram, sizing_mode='stretch_both')
        ),
        pn.pane.Markdown('## Market Analysis'),
        pn.Row(
            pn.Column(market_segmentation, sizing_mode='stretch_both')
        ),
        pn.pane.Markdown('## Market Composition'),
        pn.Row(
            pn.Column(company_chart, sizing_mode='stretch_both'),
            pn.Column(tag_chart, sizing_mode='stretch_both')
        ),
        pn.pane.Markdown('## Complete Dataset'),
        pn.pane.Markdown('*Table shows all tools matching current filter criteria. Click column headers to sort.*'),
        data_table
    ],
    accent_base_color='#2c3e50',
    header_background='#34495e'
)

template.servable()

# Automatic HTML Export
if __name__ == "__main__" or __name__.startswith('bokeh_app'):
    import os
    from datetime import datetime
    
    # Create exports directory if it doesn't exist
    export_dir = Path('exports')
    export_dir.mkdir(exist_ok=True)
    
    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = export_dir / f"{timestamp}_tools_dashboard.html"
    
    # Save the template as a static HTML file
    # Note: embed=True is not supported for templates, so this creates 
    # a file that loads resources from CDN.
    template.save(str(filename), title=template.title)
    print(f"Dashboard exported to {filename}")
