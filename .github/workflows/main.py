import yfinance as yf
import pandas_ta as ta
import pandas as pd
import requests
import os

# --- AUTHENTICATION ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

TICKERS = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS"]

def send_telegram(text):
    if not TOKEN or not CHAT_ID:
        print("Error: Telegram credentials missing!")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}"
    requests.get(url)

def analyze_stocks():
    final_signals = []
    
    for ticker in TICKERS:
        try:
            # FIX: yfinance now uses multi-index headers. We flatten them.
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
            if df.empty: continue
            
            # This line removes the extra 'Ticker' level from the columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)

            # Indicators
            df['SMA_200'] = ta.sma(df['Close'], length=200)
            df.ta.macd(append=True)
            df.ta.adx(append=True)

            last = df.iloc[-1]
            
            # Simple 3-point confluence
            score = 0
            if last['Close'] > last['SMA_200']: score += 1
            if last['ADX_14'] > 20: score += 1
            if last['MACD_12_26_9'] > last['MACDs_12_26_9']: score += 1

            if score >= 2:
                final_signals.append(f"✅ {ticker} (Score: {score}/3) @ ₹{round(last['Close'], 2)}")
                
        except Exception as e:
            print(f"Skipping {ticker} due to error: {e}")

    report = "📊 Swing Scan:\n" + "\n".join(final_signals) if final_signals else "😴 No setups."
    send_telegram(report)

if __name__ == "__main__":
    analyze_stocks()
