cat << 'EOF' > main_loop.py
import time
import requests
import os
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

SUPABASE_URL = "https://supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"

OKX_BASE_URL = "https://okx.com"
LOOKBACK = 200
BASE_RISK_GBP = 1.00

# ==========================================
# 🌐 FIX: Tiny Web Server for Render Free Tier
# ==========================================
class RenderHealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Smart Folio Engine Is Live And Scanning!")

def run_health_server():
    # Render automatically injects a variable called PORT into free web services
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), RenderHealthServer)
    print(f"🌐 Render Health Check listening on port {port}...")
    server.serve_forever()

# ==========================================
# 🤖 Core Trading Signal Logic
# ==========================================
def get_all_usdt_symbols():
    try:
        path = "/api/v5/public/instruments?instType=SPOT"
        res = requests.get(OKX_BASE_URL + path, timeout=10).json()
        if "data" in res:
            symbols = [item["instId"] for item in res["data"] if item["instId"].endswith("-USDT")]
            return sorted(symbols)[:50]
    except Exception as e:
        print(f"Error fetching asset list: {e}")
    return ["BTC-USDT", "ETH-USDT", "SOL-USDT"]

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
    watchlist = get_all_usdt_symbols()
    print(f"\n[{datetime.now()}] 🔄 Smart Folio Edge: Scanning ALL ({len(watchlist)}) Live Assets...")
    
    for symbol in watchlist:
        path = f"/api/v5/market/candles?instId={symbol}&bar=3m&limit={LOOKBACK}"
        try:
            response = requests.get(OKX_BASE_URL + path, timeout=5).json()
            if "data" not in response or not response["data"]: continue
            
            candles = response["data"][::-1]
            close_prices = [float(candle) for candle in candles]
            current_price = close_prices[-1]
            moving_average = sum(close_prices) / len(close_prices)
            
            if current_price > moving_average:
                print(f"🔥 BREAKOUT CONFIRMED: {symbol} at ${current_price}")
                send_alert_to_lovable(symbol, current_price, "BUY SIGNAL")
            
            time.sleep(0.1)
        except Exception:
            continue

def main_trading_loop():
    print("🤖 SMART FOLIO FULL EXCHANGE MASS SCANNER IS ONLINE.")
    while True:
        try:
            run_broad_scanner()
            print("💤 Full scan complete. Sleeping 30 seconds...")
            time.sleep(30)
        except Exception as e:
            print(f"Loop restart catch: {e}")
            time.sleep(10)

if __name__ == "__main__":
    # Start the web port in a separate thread so it answers Render's check instantly
    web_thread = threading.Thread(target=run_health_server, daemon=True)
    web_thread.start()
    
    # Run our core trading scanner logic on the primary thread
    main_trading_loop()
EOF
