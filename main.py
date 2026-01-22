import os
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
import glob
from datetime import datetime

# --- 1. SAFE IMPORTS ---
try:
    import pandas_ta as ta
except ImportError:
    try:
        import pandas_ta_classic as ta
    except ImportError:
        st.error("Technical analysis library (pandas-ta) not found.")

# --- 2. CREDENTIALS ---
TOKEN = os.getenv('TELEGRAM_TOKEN') or st.secrets.get("TELEGRAM_TOKEN")
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID') or st.secrets.get("TELEGRAM_CHAT_ID")
TICKERS = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "SBIN.NS", "TATASTEEL.NS"]

st.set_page_config(page_title="2026 Swing Scanner", layout="wide")
st.title("📈 Multi-Confluence Swing Dashboard")

# --- 3. LOGIC ---
def send_telegram(text):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}"
        requests.get(url)

def analyze():
    for f in glob.glob("*.html"): 
        try: os.remove(f)
        except: pass
    
    signals = []
    st.info(f"Scanning {len(TICKERS)} symbols...")

    for t in TICKERS:
        try:
            df = yf.download(t, period="1y", interval="1d", progress=False)
            
            # FIX: Flatten Multi-Index columns (Mandatory for 2026)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Technical Indicators
            df['SMA_200'] = ta.sma(df['Close'], length=200)
            df.ta.macd(append=True)
            df.ta.adx(append=True)
            last = df.iloc[-1]

            # Confluence Logic
            score = 0
            if last['Close'] > last['SMA_200']: score += 1
            if last['ADX_14'] > 20: score += 1
            if last['MACD_12_26_9'] > last['MACDs_12_26_9']: score += 1

            if score >= 2:
                sl = df['Low'].tail(5).min()
                signals.append(f"✅ {t}: Score {score}/3 @ ₹{round(last['Close'], 2)}")
                
                # Visual Dashboard Chart
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
                fig.add_hline(y=sl, line_dash="dash", line_color="red", annotation_text=f"SL: {round(sl, 2)}")
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
