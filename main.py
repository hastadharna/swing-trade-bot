import yfinance as yf
import pandas_ta as ta
import pandas as pd
import plotly.graph_objects as go
import requests
import os
from datetime import datetime

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TICKERS = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "SBIN.NS"]

def send_telegram(text):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}"
    requests.get(url)

def create_chart(df, ticker, stop_loss, signal):
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], line=dict(color='orange', width=1.5), name='SMA 200'))
    color = "green" if "Buy" in signal else "red"
    fig.add_annotation(x=df.index[-1], y=df['Close'].iloc[-1], text=signal, showarrow=True, bgcolor=color, font=dict(color="white"))
    fig.add_hline(y=stop_loss, line_dash="dash", line_color="red", annotation_text=f"SL: {round(stop_loss, 2)}")
    fig.update_layout(title=f"{ticker} Analysis", template="plotly_dark", xaxis_rangeslider_visible=False)
    fig.write_html(f"{ticker}_analysis.html")

def analyze():
    signals = []
    for t in TICKERS:
        try:
            df = yf.download(t, period="1y", interval="1d", progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0) # FIX: Flatten headers

            df['SMA_200'] = ta.sma(df['Close'], length=200)
            df.ta.macd(append=True); df.ta.adx(append=True)
            last = df.iloc[-1]

            score = 0
            if last['Close'] > last['SMA_200']: score += 1
            if last['ADX_14'] > 20: score += 1
            if last['MACD_12_26_9'] > last['MACDs_12_26_9']: score += 1

            if score >= 2:
                sl = df['Low'].tail(5).min()
                signals.append(f"✅ {t}: Score {score}/3 @ ₹{round(last['Close'], 2)}")
                create_chart(df, t, sl, "STRONG BUY")
        except Exception as e: print(f"Error {t}: {e}")

    report = "🚀 Market Scan:\n\n" + "\n".join(signals) if signals else "😴 No setups."
    send_telegram(report)

if __name__ == "__main__":
    analyze()
