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
            # Download daily data
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
            if df.empty: continue

            # 1. ADD INDICATORS USING THE TA EXTENSION
            df['SMA_200'] = ta.sma(df['Close'], length=200)
            df.ta.macd(append=True)
            df.ta.adx(append=True)
            df['VOL_SMA'] = ta.sma(df['Volume'], length=20)

            last = df.iloc[-1]

            # 2. THE CONFLUENCE CHECKLIST
            score = 0
            if last['Close'] > last['SMA_200']: score += 1
            if last['ADX_14'] > 20: score += 1
            if last['MACD_12_26_9'] > last['MACDs_12_26_9']: score += 1
            if last['Volume'] > last['VOL_SMA']: score += 1

            # 3. SIGNAL OUTPUT
            if score >= 3:
                stop_loss = df['Low'].tail(5).min()
                msg = (f"✅ {ticker}\n"
                       f"Price: ₹{round(last['Close'], 2)}\n"
                       f"Confidence: {score}/4\n"
                       f"SL: ₹{round(stop_loss, 2)}")
                final_signals.append(msg)
                
        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")

    # Final Report
    report = "🚀 **HIGH PROBABILITY SWING SETUPS** 🚀\n\n" + "\n\n".join(final_signals) if final_signals else "😴 No high-confluence setups today."
    send_telegram(report)

if __name__ == "__main__":
    analyze_stocks()
