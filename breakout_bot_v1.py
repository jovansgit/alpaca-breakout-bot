"""Experimental Alpaca breakout bot. Paper trading by default.
Sanitized copy of the July 2025 production logic; no credentials included.
"""
import alpaca_trade_api as tradeapi
import pandas as pd
import time
from datetime import datetime
import csv
import os
import pytz

# === CONFIG === #
LIVE_MODE = False
API_KEY = os.environ['ALPACA_API_KEY' if LIVE_MODE else 'ALPACA_API_KEY_PAPER']
API_SECRET = os.environ['ALPACA_API_SECRET' if LIVE_MODE else 'ALPACA_API_SECRET_PAPER']
BASE_URL = 'https://api.alpaca.markets' if LIVE_MODE else 'https://paper-api.alpaca.markets'
TIMEFRAME = '15Min'
TRADE_LOG_PATH = 'live_trade_log.csv' if LIVE_MODE else 'paper_trade_log.csv'

# === STRATEGY CONFIG PER SYMBOL === #
STRATEGIES = {
    'TSLA': {'bw': 15, 'vm': 3.0, 'tp': .03, 'sl': .01},
    'NVDA': {'bw': 10, 'vm': 3.0, 'tp': .05, 'sl': .02},
    'AMD': {'bw': 10, 'vm': 2.0, 'tp': .03, 'sl': .02},
    'MSFT': {'bw': 15, 'vm': 1.5, 'tp': .05, 'sl': .02},
    'GOOGL': {'bw': 5, 'vm': 2.0, 'tp': .03, 'sl': .02},
    'NFLX': {'bw': 5, 'vm': 2.0, 'tp': .03, 'sl': .02},
    'INTC': {'bw': 15, 'vm': 1.5, 'tp': .05, 'sl': .02},
    'AMZN': {'bw': 10, 'vm': 2.0, 'tp': .03, 'sl': .02},
    'WFC': {'bw': 10, 'vm': 1.5, 'tp': .05, 'sl': .02},
    'XOM': {'bw': 15, 'vm': 3.0, 'tp': .05, 'sl': .01},
    'SLB': {'bw': 10, 'vm': 1.5, 'tp': .05, 'sl': .01},
    'PFE': {'bw': 5, 'vm': 2.0, 'tp': .03, 'sl': .01},
    'UNH': {'bw': 5, 'vm': 2.0, 'tp': .03, 'sl': .02},
    'LLY': {'bw': 15, 'vm': 3.0, 'tp': .05, 'sl': .02},
    'HD': {'bw': 10, 'vm': 2.0, 'tp': .03, 'sl': .01},
    'TGT': {'bw': 5, 'vm': 1.5, 'tp': .03, 'sl': .02},
    'KO': {'bw': 15, 'vm': 2.0, 'tp': .03, 'sl': .01},
    'DIA': {'bw': 10, 'vm': 1.5, 'tp': .03, 'sl': .02},
    'AMAT': {'bw': 15, 'vm': 3.0, 'tp': .03, 'sl': .01},
    'APH': {'bw': 5, 'vm': 2.0, 'tp': .03, 'sl': .02},
    'ASML': {'bw': 10, 'vm': 3.0, 'tp': .03, 'sl': .02},
    'AZO': {'bw': 15, 'vm': 1.5, 'tp': .03, 'sl': .01},
    'EMR': {'bw': 10, 'vm': 1.5, 'tp': .05, 'sl': .01},
    'ENPH': {'bw': 15, 'vm': 2.0, 'tp': .03, 'sl': .02},
    'FAST': {'bw': 10, 'vm': 1.5, 'tp': .03, 'sl': .01},
    'LH': {'bw': 5, 'vm': 1.5, 'tp': .05, 'sl': .01},
    'LRCX': {'bw': 15, 'vm': 2.0, 'tp': .05, 'sl': .02},
    'ODP': {'bw': 5, 'vm': 1.5, 'tp': .05, 'sl': .02},
    'FL': {'bw': 5, 'vm': 1.5, 'tp': .03, 'sl': .02},
    'STX': {'bw': 5, 'vm': 1.5, 'tp': .05, 'sl': .02},
    'KEY': {'bw': 15, 'vm': 1.5, 'tp': .05, 'sl': .02},
    'REGN': {'bw': 15, 'vm': 1.5, 'tp': .03, 'sl': .02},
    'IBM': {'bw': 15, 'vm': 2.0, 'tp': .05, 'sl': .02},
    'CL': {'bw': 15, 'vm': 1.5, 'tp': .03, 'sl': .01},
    'MSI': {'bw': 15, 'vm': 1.5, 'tp': .03, 'sl': .02},
    'AAL': {'bw': 5, 'vm': 1.5, 'tp': .03, 'sl': .02},
    'FITB': {'bw': 10, 'vm': 1.5, 'tp': .03, 'sl': .02},
    'HES': {'bw': 15, 'vm': 1.5, 'tp': .03, 'sl': .02},
    'RCL': {'bw': 10, 'vm': 3.0, 'tp': .03, 'sl': .01},
    'JBHT': {'bw': 15, 'vm': 1.5, 'tp': .03, 'sl': .02},
    'LUV': {'bw': 15, 'vm': 1.5, 'tp': .03, 'sl': .02},
    'TMUS': {'bw': 5, 'vm': 1.5, 'tp': .05, 'sl': .01},
}

SYMBOLS = list(STRATEGIES.keys())

# === INIT API === #
api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')

# === UTILITY FUNCTIONS === #
def get_recent_data(symbol, timeframe, limit=100):
    bars = api.get_bars(symbol, timeframe, limit=limit).df
    bars.index = pd.to_datetime(bars.index)
    return bars

def find_breakout(df, strategy):
    bw = strategy['bw']
    vm = strategy['vm']
    recent_high = df['high'].rolling(window=bw).max().iloc[-2]
    avg_volume = df['volume'].rolling(window=bw).mean().iloc[-1]
    breakout = df['close'].iloc[-1] > recent_high
    volume_ok = df['volume'].iloc[-1] > vm * avg_volume
    return breakout and volume_ok

def already_has_position(symbol):
    positions = api.list_positions()
    return any(pos.symbol == symbol for pos in positions)

def log_trade(symbol, price, qty, action):
    fieldnames = ['timestamp', 'symbol', 'price', 'qty', 'action']
    file_exists = os.path.isfile(TRADE_LOG_PATH)
    with open(TRADE_LOG_PATH, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'price': price,
            'qty': qty,
            'action': action
        })

def check_closed_orders():
    closed_orders = api.list_orders(status='closed', limit=50)
    for order in closed_orders:
        if order.side == 'sell' and order.filled_qty != '0':
            log_trade(order.symbol, float(order.filled_avg_price), float(order.filled_qty), 'sell')

def submit_buy_order(symbol, strategy):
    tp = strategy['tp']
    sl = strategy['sl']
    quote = api.get_latest_quote(symbol)
    price = quote.ask_price

    # Capital allocation heuristic from production (not a loss-risk cap).
    capital = min(500, max(75, price))
    qty = int(capital / price)  # Whole shares only

    if qty < 1:
        print(f"[SKIP] {symbol} price too high (${price}) for capital limit.")
        return

    try:
        api.submit_order(
            symbol=symbol,
            qty=qty,
            side='buy',
            type='market',
            time_in_force='gtc',
            order_class='bracket',
            take_profit={'limit_price': round(price * (1 + tp), 2)},
            stop_loss={
                'stop_price': round(price * (1 - sl), 2),
                'limit_price': round(price * (1 - sl * 1.02), 2)
            }
        )
        print(f"[BUY] {symbol} @ ${price} x {qty}")
        log_trade(symbol, price, qty, 'buy')
    except Exception as e:
        print(f"[ERROR] Order failed for {symbol}: {e}")

def is_new_candle_time():
    now = datetime.now(pytz.timezone("America/New_York"))
    return now.minute % 15 == 0 and now.second < 30

# === MAIN LOOP === #
if __name__ == '__main__':
    while True:
        try:
            now = datetime.now()
            if is_new_candle_time():
                if not api.get_clock().is_open:
                    print(f"{now}: Market is closed. Skipping this cycle.")
                    time.sleep(60)
                    continue
                print(f"{now}: Checking candles at new interval")
                for symbol in SYMBOLS:
                    strategy = STRATEGIES[symbol]
                    try:
                        df = get_recent_data(symbol, TIMEFRAME, limit=strategy['bw'] + 10)
                        if find_breakout(df, strategy) and not already_has_position(symbol):
                            submit_buy_order(symbol, strategy)
                        else:
                            print(f"{now}: No breakout or already in position for {symbol}")
                    except Exception as e:
                        print(f"Error with {symbol}: {e}")
                check_closed_orders()
                time.sleep(60)
            else:
                time.sleep(30)
        except Exception as e:
            print(f"Global Error: {e}")
            time.sleep(60)
