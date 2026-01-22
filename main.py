import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import plotly.graph_objects as go
import requests
import os
import glob
from datetime import datetime

# --- 1. CONFIGURATION & SECRETS ---
# Streamlit uses st.secrets; GitHub Actions uses os.getenv
TOKEN = st.secrets.get("TELEGRAM_TOKEN") or os.getenv('TELEGRAM_TOKEN')
CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID") or os.getenv('TELEGRAM_CHAT_ID')

TICKERS = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "SBIN.NS", "TATASTEEL.NS", "BHARTIARTL.NS"]

st.set_page_config(page_title="2026 Swing Scanner", layout="wide")
st.title("📈 Multi-Confluence Swing Dashboard")

# --- 2. UTILITY FUNCTIONS ---
def cleanup_old_files():
    """Deletes all .html files in the root folder to prevent clutter."""
    for file in glob.glob("*.html"):
        try:
            os.remove(file)
        except Exception:
            pass

def send_telegram(text):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}"
        requests.get(url)

def create_visual_report(df, ticker, stop_loss, signal):
    """Creates an interactive Plotly chart with markers."""
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], 
        low=df['Low'], close=df['Close'], name="Price"
    )])
    
    # Add SMA indicators
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], line=dict(color='orange', width=1.5), name="SMA 200"))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='cyan', width=1), name="SMA 50"))

    # Visual Signal Marker
    color = "green" if "BUY" in signal else "red"
    fig.add_annotation(x=df.index[-1], y=df['Close'].iloc[-1], text=signal, showarrow=True, bgcolor=color, font=dict(color="white"))
    
    # Red Dashed Stop-Loss Line
    fig.add_hline(y=stop_loss, line_dash="dash", line_color="red", annotation_text=f"SL: {round(stop_loss, 2)}")
    
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=600)
    
    # Show in Streamlit
    st.plotly_chart(fig, use_container_width=True)
    
    # Save for GitHub Artifacts
    fig.write_html(f"{ticker}_analysis.html")

# --- 3. CORE ANALYSIS ENGINE ---
def run_scan():
    cleanup_old_files()
    signals_found = []
    
    st.info(f"Scanning {len(TICKERS)} Nifty symbols...")
    
    for t in TICKERS:
        try:
            # yfinance now returns Multi-Index data by default in 2026
            df = yf.download(t, period="1y", interval="1d", progress=False)
            
            # CRITICAL FIX: Flatten columns for indicator compatibility
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Technical Indicators using pandas-ta-classic
            df['SMA_200'] = ta.sma(df['Close'], length=200)
            df['SMA_50'] = ta.sma(df['Close'], length=50)
            df.ta.macd(append=True)
            df.ta.adx(append=True)
            
            last = df.iloc[-1]
            
            # The Confluence Score (Out of 4)
            score = 0
            if last['Close'] > last['SMA_200']: score += 1
            if last['SMA_50'] > last['SMA_200']: score += 1
            if last['ADX_14'] > 25: score += 1
            if last['MACD_12_26_9'] > last['MACDs_12_26_9']: score += 1

            if score >= 3:
                sl = df['Low'].tail(5).min()
                msg = f"✅ {t}: STRONG BUY (Score {score}/4) @ ₹{round(last['Close'], 2)}"
                signals_found.append(msg)
                
                st.subheader(f"Dashboard View: {t}")
                create_visual_report(df, t, sl, f"BUY SCORE: {score}")
                
        except Exception as e:
            st.error(f"Error analyzing {t}: {e}")

    # Final Notifications
    if signals_found:
        report = "🚀 **TRADE ALERT** 🚀\n\n" + "\n".join(signals_found)
        send_telegram(report)
        st.success("Scan Complete: Signals sent to Telegram.")
    else:
        st.warning("Scan Complete: No high-confluence setups found.")

# --- 4. EXECUTION LOGIC ---
if st.sidebar.button('🔄 Start New Market Scan'):
    run_scan()
elif __name__ == "__main__":
    # This ensures the scan runs when GitHub Actions triggers it
    run_scan()
