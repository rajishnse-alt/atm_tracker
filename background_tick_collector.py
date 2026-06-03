#!/usr/bin/env python3
"""
Automated Background Tick Collector for ATM Tracker
Runs independently and collects Upstox ticks 24/7, starting collection at 9:15 AM IST on trading days.

Features:
- Auto-starts collection at 9:15 AM IST every trading day (Mon-Fri)
- Runs continuously until 15:30 IST (market close)
- Logs all ticks to data/ticks/SYMBOL.csv
- Auto-purges data older than 30 days
- Restarts on token refresh
- Thread-safe operations
- Comprehensive logging

Setup:
1. Create a .env file with your Upstox token:
   UPSTOX_ACCESS_TOKEN=your_token_here
2. Run: python background_tick_collector.py
3. Leave it running (use screen, nohup, or systemd)
"""

import os
import sys
import json
import time
import logging
import threading
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List
import pytz
import websocket
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
IST = pytz.timezone('Asia/Kolkata')
DATA_DIR = Path(__file__).parent / "data" / "ticks"
DATA_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = Path(__file__).parent / "background_collector.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Upstox API configuration
UPSTOX_AUTH_ENDPOINT = "https://api.upstox.com/v3/feed/market-data-feed/authorize"
INSTRUMENTS = {
    "NIFTY": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
}

# Thread-safe counters
TICK_COUNTERS_LOCK = threading.Lock()
TICK_COUNTERS = {}  # {symbol: {'all_messages': 0, 'price_ticks': 0}}
COLLECTION_ACTIVE = False

# ─────────────────────────────────────────────
# TICK DATA MANAGEMENT
# ─────────────────────────────────────────────
def get_tick_file(symbol: str) -> Path:
    """Get the CSV file path for a symbol."""
    return DATA_DIR / f"{symbol}.csv"

def log_tick(symbol: str, tick_data: dict, timestamp_ist: datetime) -> None:
    """Log a single tick to CSV file."""
    try:
        file_path = get_tick_file(symbol)
        file_exists = file_path.exists()

        ltp = tick_data.get('ltp') or tick_data.get('lastPrice', 0)
        volume = tick_data.get('volume', 0)
        oi = tick_data.get('oi', 0)
        bid = tick_data.get('bid', ltp)
        ask = tick_data.get('ask', ltp)
        bid_qty = tick_data.get('bidQty', 0)
        ask_qty = tick_data.get('askQty', 0)

        with open(file_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi',
                'bid', 'ask', 'bid_qty', 'ask_qty', 'type'
            ])

            if not file_exists:
                writer.writeheader()

            writer.writerow({
                'timestamp': timestamp_ist.isoformat(),
                'open': f"{float(ltp):.2f}",
                'high': f"{float(ltp):.2f}",
                'low': f"{float(ltp):.2f}",
                'close': f"{float(ltp):.2f}",
                'volume': int(volume) if volume else 0,
                'oi': int(oi) if oi else 0,
                'bid': f"{float(bid):.2f}" if bid else "",
                'ask': f"{float(ask):.2f}" if ask else "",
                'bid_qty': int(bid_qty) if bid_qty else 0,
                'ask_qty': int(ask_qty) if ask_qty else 0,
                'type': 'tick'
            })

    except Exception as e:
        logger.error(f"Error logging tick for {symbol}: {e}", exc_info=True)

def purge_old_ticks(symbol: str, days: int = 30) -> None:
    """Remove tick data older than N days."""
    try:
        file_path = get_tick_file(symbol)
        if not file_path.exists():
            return

        cutoff_datetime = datetime.now(IST) - timedelta(days=days)
        rows_kept = []
        rows_deleted = 0

        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames

            for row in reader:
                try:
                    row_datetime = datetime.fromisoformat(row['timestamp'])
                    if row_datetime > cutoff_datetime:
                        rows_kept.append(row)
                    else:
                        rows_deleted += 1
                except (ValueError, KeyError):
                    rows_kept.append(row)

        with open(file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows_kept)

        if rows_deleted > 0:
            logger.info(f"🗑️ Purged {rows_deleted} old ticks from {symbol}.csv (kept {len(rows_kept)})")

    except Exception as e:
        logger.error(f"Error purging old ticks for {symbol}: {e}")

def get_tick_count(symbol: str) -> tuple:
    """Get total and price tick counts for a symbol."""
    with TICK_COUNTERS_LOCK:
        if symbol not in TICK_COUNTERS:
            return 0, 0
        data = TICK_COUNTERS[symbol]
        return data['all_messages'], data['price_ticks']

# ─────────────────────────────────────────────
# WEBSOCKET MANAGEMENT
# ─────────────────────────────────────────────
def start_websocket_collector(symbol: str, access_token: str) -> Optional[threading.Thread]:
    """Start WebSocket collector for a symbol in a background thread."""
    logger.info(f"Starting WebSocket collector for {symbol}...")

    instrument_key = INSTRUMENTS.get(symbol)
    if not instrument_key:
        logger.error(f"Unknown symbol: {symbol}")
        return None

    ws_state = {"active": False, "ws": None}

    def on_message(ws, message):
        try:
            data = json.loads(message)

            with TICK_COUNTERS_LOCK:
                if symbol not in TICK_COUNTERS:
                    TICK_COUNTERS[symbol] = {'all_messages': 0, 'price_ticks': 0}
                TICK_COUNTERS[symbol]['all_messages'] += 1

            msg_type = data.get('type')

            # Handle market_info (first message)
            if msg_type == 'market_info':
                logger.debug(f"[{symbol}] Received market_info")
                return

            # Handle live_feed (actual ticks)
            if msg_type == 'live_feed':
                feeds = data.get('feeds', {})
                tick_data = feeds.get(instrument_key)

                if tick_data is None:
                    return

                ltp = tick_data.get('ltp')
                if ltp is not None:
                    try:
                        ltp = float(ltp)
                        timestamp_ist = datetime.now(IST)

                        # Log tick to CSV
                        log_tick(symbol, tick_data, timestamp_ist)

                        # Update counter
                        with TICK_COUNTERS_LOCK:
                            TICK_COUNTERS[symbol]['price_ticks'] += 1
                            tick_num = TICK_COUNTERS[symbol]['price_ticks']

                        if tick_num % 100 == 0:  # Log every 100 ticks
                            logger.info(f"✅ [{symbol}] Tick #{tick_num}: LTP={ltp:.2f} | Vol={tick_data.get('volume', 0)}")

                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error parsing tick for {symbol}: {e}")

        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error for {symbol}: {e}")
        except Exception as e:
            logger.error(f"WebSocket message error for {symbol}: {e}", exc_info=True)

    def on_error(ws, error):
        logger.error(f"WebSocket error for {symbol}: {error}")
        ws_state["active"] = False

    def on_close(ws, close_status_code, close_msg):
        logger.info(f"WebSocket closed for {symbol} | Code: {close_status_code}")
        ws_state["active"] = False

    def on_open(ws):
        try:
            payload = {
                "guid": f"atm-auto-{symbol}-{int(time.time())}",
                "method": "sub",
                "data": {
                    "instrument_keys": [instrument_key],
                    "mode": "full"
                }
            }
            ws.send(json.dumps(payload))
            logger.info(f"📡 [{symbol}] Subscribed to {instrument_key}")
            ws_state["active"] = True
        except Exception as e:
            logger.error(f"Subscription error for {symbol}: {e}")

    def run_websocket():
        try:
            # Get WebSocket URL
            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
            auth_response = requests.get(UPSTOX_AUTH_ENDPOINT, headers=headers, timeout=10)

            if auth_response.status_code != 200:
                logger.error(f"Authorize failed for {symbol}: {auth_response.status_code}")
                return

            response_data = auth_response.json()
            if response_data.get('status') != 'success':
                logger.error(f"Authorize error for {symbol}: {response_data.get('errors')}")
                return

            ws_url = response_data.get('data', {}).get('authorizedRedirectUri')
            if not ws_url:
                logger.error(f"No WebSocket URL for {symbol}")
                return

            logger.info(f"Got WebSocket URL for {symbol}")

            # Connect and run
            ws = websocket.WebSocketApp(
                ws_url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                ping_interval=30,
                ping_timeout=10
            )
            ws_state["ws"] = ws
            ws.run_forever()

        except Exception as e:
            logger.error(f"WebSocket thread error for {symbol}: {e}", exc_info=True)

    # Start in daemon thread
    thread = threading.Thread(target=run_websocket, daemon=True, name=f"ws-{symbol}")
    thread.start()
    logger.info(f"🔌 WebSocket thread started for {symbol}")

    return thread

# ─────────────────────────────────────────────
# SCHEDULING & MARKET HOURS
# ─────────────────────────────────────────────
def is_trading_day() -> bool:
    """Check if today is a trading day (Mon-Fri)."""
    now = datetime.now(IST)
    return now.weekday() < 5  # 0-4 = Mon-Fri

def is_market_hours() -> bool:
    """Check if current time is during market hours (9:15-15:30 IST)."""
    now = datetime.now(IST)
    start = now.replace(hour=9, minute=15, second=0, microsecond=0)
    end = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return start <= now <= end

def seconds_until_market_open() -> int:
    """Get seconds until next market open (9:15 AM IST)."""
    now = datetime.now(IST)

    # If today is not a trading day, find next trading day
    if now.weekday() >= 5:  # Saturday or Sunday
        days_until_monday = (7 - now.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_market_open = now.replace(hour=9, minute=15, second=0, microsecond=0) + timedelta(days=days_until_monday)
    else:
        # Today is a trading day
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        if now >= market_open:
            # Market already opened today, next open is tomorrow
            next_market_open = market_open + timedelta(days=1)
            # If tomorrow is weekend, skip to Monday
            while next_market_open.weekday() >= 5:
                next_market_open += timedelta(days=1)
        else:
            # Market opens later today
            next_market_open = market_open

    delta = next_market_open - now
    return int(delta.total_seconds())

# ─────────────────────────────────────────────
# MAIN COLLECTOR LOOP
# ─────────────────────────────────────────────
def main_collector_loop(access_token: str) -> None:
    """Main loop: Wait for market hours, collect ticks, repeat."""
    global COLLECTION_ACTIVE
    ws_threads = {}

    logger.info("=" * 70)
    logger.info("🚀 ATM Tracker Background Tick Collector Started")
    logger.info(f"📍 Data directory: {DATA_DIR}")
    logger.info(f"📝 Log file: {LOG_FILE}")
    logger.info("=" * 70)

    while True:
        try:
            # Check if it's a trading day and market hours
            if is_trading_day() and is_market_hours():
                if not COLLECTION_ACTIVE:
                    logger.info("🟢 Market is OPEN - Starting tick collection...")
                    COLLECTION_ACTIVE = True

                    # Start WebSocket for each symbol
                    for symbol in INSTRUMENTS.keys():
                        if symbol not in ws_threads:
                            thread = start_websocket_collector(symbol, access_token)
                            if thread:
                                ws_threads[symbol] = thread

                    # Purge old data daily
                    for symbol in INSTRUMENTS.keys():
                        purge_old_ticks(symbol, days=30)

                # Print status every 5 minutes
                nifty_all, nifty_price = get_tick_count("NIFTY")
                bnifty_all, bnifty_price = get_tick_count("BANKNIFTY")

                logger.info(
                    f"📊 Live | NIFTY: {nifty_price} ticks | BANKNIFTY: {bnifty_price} ticks"
                )

                time.sleep(300)  # Check every 5 minutes

            else:
                if COLLECTION_ACTIVE:
                    logger.info("🔴 Market is CLOSED - Stopping tick collection...")
                    COLLECTION_ACTIVE = False
                    ws_threads.clear()

                # Wait until market opens
                seconds_to_wait = seconds_until_market_open()
                hours = seconds_to_wait // 3600
                minutes = (seconds_to_wait % 3600) // 60

                logger.info(f"⏳ Waiting for market open... ({hours}h {minutes}m)")
                time.sleep(min(seconds_to_wait, 3600))  # Check every hour or until market open

        except KeyboardInterrupt:
            logger.info("⚠️ Shutting down gracefully...")
            COLLECTION_ACTIVE = False
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            time.sleep(10)

def verify_setup() -> bool:
    """Verify that everything is set up correctly."""
    logger.info("\n🔍 Verifying setup...")

    # Check access token
    access_token = os.getenv("UPSTOX_ACCESS_TOKEN")
    if not access_token:
        logger.error("❌ UPSTOX_ACCESS_TOKEN not found in environment variables")
        logger.error("   Please create a .env file with: UPSTOX_ACCESS_TOKEN=your_token")
        return False

    if access_token == "YOUR_TOKEN_HERE":
        logger.error("❌ UPSTOX_ACCESS_TOKEN is still set to placeholder value")
        return False

    logger.info(f"✅ Access token found (length: {len(access_token)})")

    # Check data directory
    if not DATA_DIR.exists():
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created data directory: {DATA_DIR}")
        except Exception as e:
            logger.error(f"❌ Cannot create data directory: {e}")
            return False

    # Test token with authorize endpoint
    logger.info("Testing token with Upstox API...")
    try:
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        response = requests.get(UPSTOX_AUTH_ENDPOINT, headers=headers, timeout=10)

        if response.status_code == 200:
            logger.info("✅ Token is valid")
            return True
        elif response.status_code == 401:
            logger.error("❌ Token is invalid or expired")
            return False
        else:
            logger.warning(f"⚠️ Unexpected status code: {response.status_code}")
            logger.warning("   Proceeding anyway (token may still work)...")
            return True

    except Exception as e:
        logger.error(f"❌ Cannot connect to Upstox API: {e}")
        logger.error("   Check your internet connection")
        return False

if __name__ == "__main__":
    # Verify setup
    if not verify_setup():
        logger.error("\n❌ Setup verification failed. Please fix the issues above.")
        sys.exit(1)

    # Get access token
    access_token = os.getenv("UPSTOX_ACCESS_TOKEN")

    logger.info("\n✅ Setup verification passed!")
    logger.info("\n📋 Next steps:")
    logger.info("   1. Keep this script running (use screen, nohup, or systemd)")
    logger.info("   2. Every trading day at 9:15 AM IST, tick collection starts")
    logger.info(f"   3. Ticks are saved to: {DATA_DIR}/SYMBOL.csv")
    logger.info("   4. Data older than 30 days is auto-purged")
    logger.info("\n" + "=" * 70 + "\n")

    # Start main loop
    try:
        main_collector_loop(access_token)
    except KeyboardInterrupt:
        logger.info("\n✋ Collector stopped by user")
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)
