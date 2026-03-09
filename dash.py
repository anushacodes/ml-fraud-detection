import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Fraud Model Monitor", layout="wide")
st.title("🛡️ Fraud Detection Pipeline Monitor")

# --- DATA MOCKING (Replace with actual DB query later) ---
@st.cache_data
def get_data():
    """Generates 30 days of simulated tracking data and system events."""
    dates = [datetime.today() - timedelta(days=i) for i in range(30, 0, -1)]
    
    # Simulate degrading performance, then recovery
    accuracy = np.concatenate([np.linspace(0.98, 0.90, 15), np.linspace(0.98, 0.99, 15)])
    precision = np.concatenate([np.linspace(0.95, 0.85, 15), np.linspace(0.96, 0.97, 15)])
    recall = np.concatenate([np.linspace(0.85, 0.70, 15), np.linspace(0.88, 0.90, 15)])
    
    df = pd.DataFrame({
        "Date": dates,
        "Accuracy": accuracy + np.random.normal(0, 0.01, 30),
        "Precision": precision + np.random.normal(0, 0.01, 30),
        "Recall": recall + np.random.normal(0, 0.01, 30),
        "Daily_Txns": np.random.randint(1000, 5000, 30)
    })
    
    # Define significant events to overlay on the graph
    events = [
        {"date": dates[14], "label": "⚠️ Drift Detected", "color": "red"},
        {"date": dates[16], "label": "🔄 Model Retrained", "color": "green"}
    ]
    
    return df, events

df, events = get_data()

# --- TOP KPI METRICS ---
# Get the most recent values for the top row
latest = df.iloc[-1]
total_txns = df["Daily_Txns"].sum()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Total Transactions Processed", value=f"{total_txns:,}")
with col2:
    st.metric(label="Current Accuracy", value=f"{latest['Accuracy']:.2%}")
with col3:
    st.metric(label="Current Precision", value=f"{latest['Precision']:.2%}")
with col4:
    st.metric(label="Current Recall", value=f"{latest['Recall']:.2%}")

st.markdown("---")

# --- PLOTLY GRAPH WITH EVENT MARKERS ---
st.subheader("Model Performance Over Time")

fig = go.Figure()

# Add lines for each metric
fig.add_trace(go.Scatter(x=df["Date"], y=df["Accuracy"], mode='lines', name='Accuracy', line=dict(color='blue')))
fig.add_trace(go.Scatter(x=df["Date"], y=df["Precision"], mode='lines', name='Precision', line=dict(color='orange')))
fig.add_trace(go.Scatter(x=df["Date"], y=df["Recall"], mode='lines', name='Recall', line=dict(color='purple')))

# Add Vertical Lines for Events
for event in events:
    fig.add_vline(
        x=event["date"].timestamp() * 1000, # Plotly requires timestamps in ms for vlines on datetime x-axes
        line_dash="dash",
        line_color=event["color"],
        annotation_text=event["label"],
        annotation_position="top right"
    )

# Format the chart layout
fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Metric Score",
    yaxis=dict(range=[0.5, 1.05]), # Keep y-axis scaled reasonably
    hovermode="x unified",
    margin=dict(l=0, r=0, t=30, b=0)
)

st.plotly_chart(fig, use_container_width=True)