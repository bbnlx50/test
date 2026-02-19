import ccxt
import pandas as pd
import numpy as np
import requests
import time
import os

# ========================
# Environment Variables
# ========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

print("Testing Telegram...")

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
r = requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": "🚀 Fly bot test message"
})

print("Response:", r.text)
# ========================
# Exchange Setup
# ========================
exchange = ccxt.gateio({'enableRateLimit': True})

# ========================
# Token List
# ========================
tokens = [
    "ADA/USDT","AERO/USDT","ELIZAOS/USDT","AIOZ/USDT","AKT/USDT",
    "APT/USDT","AR/USDT","ASTER/USDT","ATH/USDT","AVAX/USDT",
    "BCH/USDT","BEAM/USDT","BTC/USDT",
    "CETUS/USDT","CGPT/USDT","CHZ/USDT","CPOOL/USDT",
    "DOGE/USDT","DOT/USDT","ETH/USDT","FET/USDT","FLOKI/USDT",
    "FLR/USDT","FLUX/USDT","HBAR/USDT","HIVE/USDT",
    "HONEY/USDT","HYPE/USDT","ICP/USDT","IMX/USDT","INJ/USDT",
    "JUP/USDT","KAITO/USDT","KAS/USDT","KTA/USDT","LINK/USDT",
    "METIS/USDT","MINA/USDT","MORPHO/USDT","NEAR/USDT","OKB/USDT",
    "ONDO/USDT","OP/USDT","PEAQ/USDT","PEPE/USDT","POL/USDT",
    "POPCAT/USDT","PYTH/USDT","RAY/USDT","RENDER/USDT","RIO/USDT",
    "SEI/USDT","SHIB/USDT","SOL/USDT","SUI/USDT","SUPRA/USDT",
    "TAO/USDT","TAI/USDT","TIA/USDT","TON/USDT","UNI/USDT",
    "VIRTUAL/USDT","W/USDT","WELL/USDT","WLD/USDT","XLM/USDT",
    "XPL/USDT","XRP/USDT"
]

# ========================
# Timeframes
# ========================
timeframes = ['1h','4h','1d']

# ========================
# Zero Lag EMA Function
# ========================
def zero_lag_ema(close_series, length=70):
    lag = (length - 1) // 2
    zlema = pd.Series(close_series) + (pd.Series(close_series) - pd.Series(close_series).shift(lag))
    return zlema.ewm(span=length, adjust=False).mean()

# ========================
# Trend and Entry Calculation
# ========================
def calculate_signals(df, length=70, mult=1.2):
    src = df['close']
    zlema = zero_lag_ema(src, length)
    atr = df['high'].rolling(length).max() - df['low'].rolling(length).min()
    volatility = atr.rolling(length*3).max() * mult

    trend = [0]*len(df)

    for i in range(1,len(df)):
        if df['close'][i] > zlema[i] + volatility[i]:
            trend[i] = 1
        elif df['close'][i] < zlema[i] - volatility[i]:
            trend[i] = -1
        else:
            trend[i] = trend[i-1]

    df['trend'] = trend
    df['bullish_entry'] = ((df['close'] > zlema) & (df['trend'] == 1) & (pd.Series(trend).shift(1) == 1))
    df['bearish_entry'] = ((df['close'] < zlema) & (df['trend'] == -1) & (pd.Series(trend).shift(1) == -1))

    return df

# ========================
# Telegram Notification
# ========================
def send_telegram(message):
    if BOT_TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    else:
        print("⚠️ BOT_TOKEN or CHAT_ID not set!")

# ========================
# Scanner Loop
# ========================
while True:
    for symbol in tokens:
        for tf in timeframes:
            try:
                print(f"Scanning {symbol} {tf}")
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=100)
                df = pd.DataFrame(
                    ohlcv,
                    columns=["timestamp", "open", "high", "low", "close", "volume"]
                )
                df = calculate_signals(df)
                last_row = df.iloc[-1]
                send_telegram(f"{symbol} {tf} close={last_row['close']} zlema={last_row['zlema']} trend={last_row['trend']}")

            except Exception as e:
                print(f"Error with {symbol} {tf}: {e}")

                # Send Telegram messages only for signals
                if last_row['bullish_entry']:
                    send_telegram(f"🚀 {symbol} {tf} Bullish Entry Signal")
                if last_row['bearish_entry']:
                    send_telegram(f"🔻 {symbol} {tf} Bearish Entry Signal")
                if last_row['trend'] == 1 and last_row['trend'] != df['trend'].iloc[-2]:
                    send_telegram(f"📈 {symbol} {tf} Trend turned Bullish")
                if last_row['trend'] == -1 and last_row['trend'] != df['trend'].iloc[-2]:
                    send_telegram(f"📉 {symbol} {tf} Trend turned Bearish")

                time.sleep(exchange.rateLimit / 1000)  # respect rate limits

            except ccxt.ExchangeError:
                print(f"⚠️ {symbol} not available on YOUR EXCHANGE")
            except Exception as e:
                print(f"❌ Error fetching {symbol} {tf}: {e}")

    # Wait before next full cycle (e.g., 5 minutes)
    time.sleep(300)







