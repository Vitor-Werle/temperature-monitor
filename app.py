import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Temperature Dashboard",
    page_icon="🌡️",
    layout="wide"
)


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv("data.csv")
    df.columns = df.columns.str.strip()  # remove spaces from column names
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


df = load_data()

# Calculate date limits
min_date = df["timestamp"].min().date()
max_date = df["timestamp"].max().date()

# ========== SIDEBAR ==========
with st.sidebar:
    st.header("Filters")

    start_date, end_date = st.date_input(
        "Select date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    show_moving_average = st.checkbox("Show Moving Average", value=True)
    window = st.slider("Moving Average Window", min_value=3, max_value=50, value=10)

    threshold = st.number_input("Alert threshold (°C)", value=30.0)

# ========== APPLY FILTER ==========
mask = (df["timestamp"].dt.date >= start_date) & (df["timestamp"].dt.date <= end_date)
filtered_df = df.loc[mask].copy()

# ========== TITLE ==========
st.title("Temperature Dashboard - IoT")

# ========== METRICS ==========
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Current", f"{filtered_df['temperature'].iloc[-1]:.1f} °C")
with col2:
    st.metric("Average", f"{filtered_df['temperature'].mean():.1f} °C")
with col3:
    st.metric("Max", f"{filtered_df['temperature'].max():.1f} °C")
with col4:
    st.metric("Min", f"{filtered_df['temperature'].min():.1f} °C")

st.caption(f"Last reading: {filtered_df['timestamp'].iloc[-1]}")

# ========== ALERT ==========
current_temp = filtered_df["temperature"].iloc[-1]
if current_temp > threshold:
    st.error(f"⚠️ Temperature is above the limit! ({current_temp:.1f} °C)")
else:
    st.success("Temperature is within normal range")

# ========== MAIN CHART ==========
fig = px.line(
    filtered_df,
    x="timestamp",
    y="temperature",
    title="Temperature over time",
    labels={"temperature": "Temperature (°C)", "timestamp": "Time"}
)

if show_moving_average:
    filtered_df["moving_avg"] = filtered_df["temperature"].rolling(window=window).mean()
    fig.add_scatter(
        x=filtered_df["timestamp"],
        y=filtered_df["moving_avg"],
        mode="lines",
        name=f"Moving Average ({window})",
        line=dict(color="orange", width=2)
    )

fig.update_layout(hovermode="x unified", template="plotly_white", height=500)
st.plotly_chart(fig, use_container_width=True)

# ========== EXTRA CHARTS ==========
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Temperature Distribution")
    fig_hist = px.histogram(filtered_df, x="temperature", nbins=30)
    st.plotly_chart(fig_hist, use_container_width=True)

with col_b:
    st.subheader("Daily Average")
    daily = filtered_df.set_index("timestamp").resample("D")["temperature"].mean().reset_index()
    fig_daily = px.bar(daily, x="timestamp", y="temperature")
    st.plotly_chart(fig_daily, use_container_width=True)

# ========== DOWNLOAD ==========
csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download filtered data as CSV",
    data=csv,
    file_name="filtered_temperature.csv",
    mime="text/csv"
)