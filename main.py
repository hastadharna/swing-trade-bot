import os
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
import glob
from datetime import datetime

# Import pandas_ta carefully due to maintenance issues
try:
    import pandas_ta as ta
except ImportError:
    import pandas_ta_classic as ta

# --- 1. CREDENTIALS ---
# Access via environment variables (GitHub) or st.secrets (Streamlit)
TOKEN = os.getenv('TELEGRAM_TOKEN') or st.secrets.get("TELEGRAM_TOKEN")
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID') or st.secrets.get("TELEGRAM_CHAT_ID")

st.set_page_config(page_title="2026 Swing Scanner", layout="wide")
st.title("📈 Multi-Confluence Swing Dashboard")

# --- 2. LOGIC ---
def send_telegram(text):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}"
        requests.get(url)

def analyze():
    for f in glob.glob("*.html"): os.remove(f) # Cleanup
    tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "SBIN.NS"]
    signals = []

    for t in tickers:
        try:
            df = yf.download(t, period="1y", interval="1d", progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            df['SMA_200'] = ta.sma(df['Close'], length=200)
            df.ta.macd(append=True)
            last = df.iloc[-1]

            if last['Close'] > last['SMA_200']:
                sl = df['Low'].tail(5).min()
                signals.append(f"✅ {t}: BUY @ ₹{round(last['Close'], 2)}")
                
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
                st.plotly_chart(fig, use_container_width=True)
                fig.write_html(f"{t}_analysis.html")
        except Exception as e: st.error(f"Error {t}: {e}")

    if signals: send_telegram("🚀 Market Scan:\n\n" + "\n".join(signals))

if st.sidebar.button('🔄 Refresh'): analyze()
elif __name__ == "__main__": analyze()
