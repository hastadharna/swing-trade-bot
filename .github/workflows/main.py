import yfinance as yf
import pandas_ta as ta
import pandas as pd
import requests
import os

# --- AUTHENTICATION ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# --- LIST OF STOCKS (Nifty 50 Heavyweights) ---
TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", 
    "TATASTEEL.NS", "SBIN.NS", "BHARTIARTL.NS", "LTIM.NS", "MARUTI.NS"
]

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}"
    requests.get(url)

def analyze_stocks():
    final_signals = []
    
    for ticker in TICKERS:
        try:
            # Download daily data (1 year for better SMA calculation)
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
            if df.empty: continue

            # 1. ADD INDICATORS
            df['SMA_200'] = ta.sma(df['Close'], length=200)
            df['SMA_50'] = ta.sma(df['Close'], length=50)
            df.ta.macd(append=True)
            df.ta.adx(append=True)
            df['VOL_SMA'] = ta.sma(df['Volume'], length=20) # 20-day Avg Volume

            last = df.iloc[-1]
            prev = df.iloc[-2]

            # 2. THE "CONFLUENCE" CHECKLIST
            score = 0
            
            # Rule 1: Long term trend is Up
            if last['Close'] > last['SMA_200']: score += 1
            
            # Rule 2: Strong Trend Strength (ADX > 20)
            if last['ADX_14'] > 20: score += 1
            
            # Rule 3: Bullish Momentum (MACD Crossover or Positive)
            if last['MACD_12_26_9'] > last['MACDs_12_26_9']: score += 1
            
            # Rule 4: Volume Confirmation (Today's Vol > Avg Vol)
            if last['Volume'] > last['VOL_SMA']: score += 1

            # 3. OUTPUT LOGIC
            if score >= 3:
                # Calculate Stop Loss (Recent 5-day Low)
                stop_loss = df['Low'].tail(5).min()
                msg = (f"✅ {ticker}\n"
                       f"Price: ₹{round(last['Close'], 2)}\n"
                       f"Confidence: {score}/4\n"
                       f"SL: ₹{round(stop_loss, 2)}")
                final_signals.append(msg)
                
        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")

    # Final Report
    if final_signals:
        report = "🚀 **HIGH PROBABILITY SWING SETUPS** 🚀\n\n" + "\n\n".join(final_signals)
    else:
        report = "😴 No high-confluence setups today. Staying in cash."
    
    send_telegram(report)

if __name__ == "__main__":
    analyze_stocks()
