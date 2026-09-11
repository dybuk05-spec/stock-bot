import yfinance as yf
import pandas as pd
import requests

# --- TELEGRAM CONFIG ---
BOT_TOKEN = "8618302558:AAHvSxznFBHJcZ0vFHgTdS3t3-lQRIrKQUw"
CHAT_ID = "7108286252"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Telegram dispatch failed: {e}")

def calculate_technicals(df):
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['Vol_SMA_20'] = df['Volume'].rolling(window=20).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema_12 - ema_26
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    return df

def scan_and_alert(watchlist):
    alerts = []
    for ticker in watchlist:
        try:
            df = yf.Ticker(ticker).history(period="6mo")
            if len(df) < 50:
                continue
                
            df = calculate_technicals(df)
            curr = df.iloc[-1]
            prev = df.iloc[-2]
            
            uptrend = curr['Close'] > curr['EMA_20'] > curr['SMA_50']
            rsi_ok = 55 <= curr['RSI'] <= 70
            macd_cross = (curr['MACD'] > curr['Signal']) and (prev['MACD'] <= prev['Signal'] or curr['MACD'] > 0)
            vol_spike = curr['Volume'] >= (1.5 * curr['Vol_SMA_20'])
            
            if uptrend and rsi_ok and macd_cross and vol_spike:
                price = round(curr['Close'], 2)
                target = round(price * 1.06, 2)
                stop = round(price * 0.97, 2)
                
                alerts.append(
                    f"🚀 *Buy Signal: {ticker}*\n"
                    f"• Entry: ₹{price}\n"
                    f"• Target (+6%): ₹{target}\n"
                    f"• Stop Loss (-3%): ₹{stop}\n"
                    f"• RSI: {round(curr['RSI'], 1)}"
                )
        except Exception:
            continue
            
    if alerts:
        send_telegram_alert(f"📊 *Short-Term Swing Picks*\n\n" + "\n\n".join(alerts))
    else:
        send_telegram_alert("Scan complete: No stocks met the technical criteria today.")

if __name__ == "__main__":
        stocks = [
        # Defence & Aerospace (High-Beta Momentum)
        "HAL.NS", "BEL.NS", "MAZDOCK.NS", "COCHINSHIP.NS", "BDL.NS", 
        "GRSE.NS", "DATAPATTNS.NS", "SOLARINDS.NS", "PARAS.NS",

        # Large Cap IT & Tech
        "RELIANCE.NS", "TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS", 
        "LTIM.NS", "PERSISTENT.NS", "COFORGE.NS",
        
        # Banking & Financial Services
        "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS", 
        "INDUSINDBK.NS", "FEDERALBNK.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", 
        "CHOLAFIN.NS", "MUTHOOTFIN.NS", "SHRIRAMFIN.NS",
        
        # Auto, EV & Ancillaries
        "TATAMOTORS.NS", "M&M.NS", "MARUTI.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS", 
        "EICHERMOT.NS", "TVSMOTOR.NS", "BHARATFORG.NS",
        
        # Metals, Mining & Energy
        "TATASTEEL.NS", "HINDALCO.NS", "JSWSTEEL.NS", "VEDL.NS", "JINDALSTEL.NS", 
        "COALINDIA.NS", "NTPC.NS", "POWERGRID.NS", "ONGC.NS", "BPCL.NS", "IOC.NS",
        
        # Capital Goods & Infrastructure
        "LT.NS", "SIEMENS.NS", "ABB.NS", "BHEL.NS", "DLF.NS",
        
        # Pharma, Healthcare & Chemicals
        "SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS", "DIVISLAB.NS", "APOLLOHOSP.NS", 
        "TRENT.NS", "PIDILITIND.NS",
        
        # FMCG, Consumer & Telecom
        "ITC.NS", "HINDUNILVR.NS", "TITAN.NS", "BHARTIARTL.NS", "ASIANPAINT.NS"
    ]

    scan_and_alert(stocks)
