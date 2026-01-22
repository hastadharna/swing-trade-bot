import os
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
import glob
from datetime import datetime

# --- 1. SAFE IMPORTS & COMPATIBILITY ---
try:
    import pandas_ta as ta
except ImportError:
    import pandas_ta_classic as ta

# --- 2. ROBUST CREDENTIAL HANDLER ---
def get_secret(key):
    # Try GitHub Actions environment variable first
    val = os.getenv(key)
    if val:
        return val
    # Fallback to Streamlit secrets
    try:
        return st.secrets.get(key)
    except Exception:
        return None

TOKEN = get_secret("TELEGRAM_TOKEN")
CHAT_ID = get_secret("TELEGRAM_CHAT_ID")

# Basic Streamlit UI Setup
st.set_page_config(page_title="2026 Swing Scanner", layout="wide")
st.title("📈 Multi-Confluence Swing Dashboard")

if not TOKEN or not CHAT_ID:
    st.error("Missing Credentials! Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID in Secrets.")
    st.stop()

# --- 3. CORE LOGIC ---
def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}"
    requests.get(url)

def analyze():
    # Cleanup old reports
    for f in glob.glob("*.html"):
        try: os.remove(f)
        except: pass
    
    tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "SBIN.NS", "TATASTEEL.NS"]
    signals = []
    
    for t in tickers:
        try:
            df = yf.download(t, period="1y", interval="1d", progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df['SMA_200'] = ta.sma(df['Close'], length=200)
            df.ta.macd(append=True)
            df.ta.adx(append=True)
            last = df.iloc[-1]

            # 3-Point Confluence
            score = 0
            if last['Close'] > last['SMA_200']: score += 1
            if last['ADX_14'] > 20: score += 1
            if last['MACD_12_26_9'] > last['MACDs_12_26_9']: score += 1

            if score >= 2:
                sl = df['Low'].tail(5).min()
                signals.append(f"✅ {t}: Score {score}/3 @ ₹{round(last['Close'], 2)}")
                
                # Visual Chart
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
                fig.add_hline(y=sl, line_dash="dash", line_color="red", annotation_text="SL")
                fig.update_layout(template="plotly_dark", title=f"{t} Analysis", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
                fig.write_html(f"{t}_analysis.html")
        except Exception as e:
            st.error(f"Error {t}: {e}")

    if signals:
        send_telegram("🚀 Market Scan Results:\n\n" + "\n".join(signals))

if st.sidebar.button('🔄 Refresh Scan'):
    analyze()
elif __name__ == "__main__":
    analyze()
