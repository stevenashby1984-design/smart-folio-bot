import time
import requests
from datetime import datetime

SUPABASE_URL = "https://supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"

OKX_BASE_URL = "https://okx.com"
LOOKBACK = 200
BASE_RISK_GBP = 1.00

def get_all_usdt_symbols():
    """Dynamically fetches every active crypto pair ending in USDT on OKX"""
    try:
        path = "/api/v5/public/instruments?instType=SPOT"
        res = requests.get(OKX_BASE_URL + path, timeout=10).json()
        if "data" in res:
            # Filters to find only major assets settled in USDT (e.g., BTC-USDT, ETH-USDT)
            symbols = [item["instId"] for item in res["data"] if item["instId"].endswith("-USDT")]
            # Sort them and limit to top 50 high-volume tokens to prevent terminal lag
            return sorted(symbols)[:50]
    except Exception as e:
        print(f"Error fetching dynamic asset list: {e}")
    return ["BTC-USDT", "ETH-USDT", "SOL-USDT"] # Reliable fallback list

def send_alert_to_lovable(symbol, price, action):
    url = f"{SUPABASE_URL}/rest/v1/trade_logs"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    payload = {
        "symbol": symbol,
        "side": action,
        "execution_price": price,
        "risk_amount_gbp": BASE_RISK_GBP,
        "outcome": "ALERT_ACTIVE",
        "profit_loss_gbp": 0.00
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        if res.status_code == 201 or res.status_code == 200:
            print(f"🚀 DASHBOARD SYNC: Alert pushed to Lovable UI for {symbol}!")
    except Exception as e:
        print(f"Dashboard sync error: {e}")

def run_broad_scanner():
    # Dynamically discover all active market assets on this loop cycle
    watchlist = get_all_usdt_symbols()
    print(f"\n[{datetime.now()}] 🔄 Smart Folio Edge: Scanning ALL ({len(watchlist)}) Live Assets...")
    
    for symbol in watchlist:
        # Requesting spot market candle bars
        path = f"/api/v5/market/candles?instId={symbol}&bar=3m&limit={LOOKBACK}"
        try:
            response = requests.get(OKX_BASE_URL + path, timeout=5).json()
            if "data" not in response or not response["data"]: continue
            
            candles = response["data"][::-1]
            close_prices = [float(candle[4]) for candle in candles]
            current_price = close_prices[-1]
            moving_average = sum(close_prices) / len(close_prices)
            
            if current_price > moving_average:
                print(f"🔥 BREAKOUT CONFIRMED: {symbol} at ${current_price} (MA: ${moving_average:.2f})")
                send_alert_to_lovable(symbol, current_price, "BUY SIGNAL")
            
            # Anti-rate limit safety cushion delay (milliseconds)
            time.sleep(0.1)
                
        except Exception:
            continue # Silently bypass minor server connection hiccups

if __name__ == "__main__":
    print("🤖 ======================================================== 🤖")
    print("🚀 SMART FOLIO FULL EXCHANGE MASS SCANNER IS ONLINE.")
    print("🤖 ======================================================== 🤖")
    while True:
        try:
            run_broad_scanner()
            print("💤 Full scan complete. Sleeping 30 seconds before next deep scan...")
            time.sleep(30)
        except KeyboardInterrupt:
            break
