"""Interactive Plotly chart utilities for Streamlit dashboard."""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

def plot_sector_donut(df: pd.DataFrame):
    """Plot market capitalization distribution across sectors."""
    sec_df = df.groupby('broad_sector')['market_cap_crore'].sum().reset_index()
    fig = px.pie(
        sec_df,
        names='broad_sector',
        values='market_cap_crore',
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Prism,
        title="Nifty 100 Sector Market Cap Weighting"
    )
    fig.update_layout(
        showlegend=True,
        margin=dict(t=40, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
    )
    return fig

def plot_health_score_distribution(df: pd.DataFrame):
    """Histogram of Composite Health Scores with institutional color banding."""
    scores = df['composite_score'].dropna()
    fig = go.Figure()
    
    # 5 Institutional color bands
    bands = [
        (0, 35, 'Poor (0-34)', '#EF4444'),
        (35, 50, 'Weak (35-49)', '#F97316'),
        (50, 65, 'Average (50-64)', '#EAB308'),
        (65, 80, 'Good (65-79)', '#0EA5E9'),
        (80, 100, 'Excellent (80-100)', '#10B981')
    ]
    
    for low, high, label, col in bands:
        sub = scores[(scores >= low) & (scores < high if high < 100 else scores <= high)]
        fig.add_trace(go.Bar(
            x=[label],
            y=[len(sub)],
            name=label,
            marker_color=col,
            text=[f"{len(sub)} cos"],
            textposition='auto'
        ))

    fig.update_layout(
        title="Composite Financial Health Score Distribution (0–100)",
        xaxis_title="Health Score Tier",
        yaxis_title="Number of Companies",
        margin=dict(t=40, b=20, l=20, r=20),
        showlegend=False
    )
    return fig

def plot_company_financials(pl_df: pd.DataFrame):
    """Interactive bar chart of Revenue vs Net Profit over historical years."""
    recent = pl_df.tail(10)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=recent['year'],
        y=recent['sales'],
        name='Sales / Revenue (₹ Cr)',
        marker_color='#3B82F6'
    ))
    fig.add_trace(go.Bar(
        x=recent['year'],
        y=recent['net_profit'],
        name='Net Profit (PAT) (₹ Cr)',
        marker_color='#10B981'
    ))
    fig.update_layout(
        title="Historical Revenue & Net Profit Trend",
        barmode='group',
        margin=dict(t=40, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def plot_radar_comparison(company_metrics: dict, peer_metrics: dict, ticker: str, group_name: str):
    """Plotly interactive radar chart comparing company against peer group average."""
    categories = list(company_metrics.keys())
    c_vals = list(company_metrics.values())
    p_vals = [peer_metrics.get(k, 0.0) for k in categories]

    # Close the loop
    categories_closed = categories + [categories[0]]
    c_vals_closed = c_vals + [c_vals[0]]
    p_vals_closed = p_vals + [p_vals[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=c_vals_closed,
        theta=categories_closed,
        fill='toself',
        name=ticker,
        line=dict(color='#2563EB', width=2),
        fillcolor='rgba(37, 99, 235, 0.25)'
    ))
    fig.add_trace(go.Scatterpolar(
        r=p_vals_closed,
        theta=categories_closed,
        fill='toself',
        name=f'{group_name} Median',
        line=dict(color='#F59E0B', width=1.5, dash='dash'),
        fillcolor='rgba(245, 158, 11, 0.15)'
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, max(max(c_vals + [10]), max(p_vals + [10])) * 1.15])),
        title=f"Peer Benchmark Radar: {ticker} vs {group_name}",
        margin=dict(t=40, b=20, l=40, r=40)
    )
    return fig
