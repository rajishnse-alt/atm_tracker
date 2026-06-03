#!/usr/bin/env python3
"""
Standalone Upstox WebSocket Test Script
Tests WebSocket connection independently to verify token and feed access
"""

import websocket
import json
import threading
import time
import requests
import sys

# ─────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN_HERE"  # Replace with your Upstox OAuth token
TEST_SYMBOLS = [
    ("NIFTY", "NSE_INDEX|Nifty 50"),
    ("BANKNIFTY", "NSE_INDEX|Nifty Bank"),
    ("RELIANCE", "NSE_EQ|INE002A01018"),
]

# ─────────────────────────────────────
# TRACKING GLOBALS
# ─────────────────────────────────────
session_data = {}

def upstox_headers(token):
    """Generate Upstox API headers with Bearer token."""
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}

# ─────────────────────────────────────
# WEBSOCKET CALLBACKS
# ─────────────────────────────────────
def on_message(ws, message):
    """Handle incoming WebSocket message (Upstox V3 API format)."""
    try:
        data = json.loads(message)
        symbol = ws.symbol if hasattr(ws, 'symbol') else "UNKNOWN"
        instrument_key = ws.instrument_key if hasattr(ws, 'instrument_key') else "UNKNOWN"
        msg_type = data.get('type')

        # Handle market_info messages (first message on subscription)
        if msg_type == 'market_info':
            print(f"📡 [{symbol}] Received market_info status")
            return

        # Handle live_feed messages (actual tick data)
        if msg_type == 'live_feed':
            feeds = data.get('feeds', {})
            tick_data = feeds.get(instrument_key)

            if tick_data is None:
                print(f"⚠️  [{symbol}] live_feed received but no data for {instrument_key}")
                return

            # Extract LTP from the nested tick data
            ltp = tick_data.get('ltp') or tick_data.get('lastPrice') or tick_data.get('last_price')

            if ltp:
                ltp = float(ltp)

                # Update session high/low
                if symbol not in session_data:
                    session_data[symbol] = {"high": ltp, "low": ltp, "ticks": 0}

                if ltp > session_data[symbol]["high"]:
                    session_data[symbol]["high"] = ltp
                if ltp < session_data[symbol]["low"]:
                    session_data[symbol]["low"] = ltp

                session_data[symbol]["ticks"] += 1

                print(f"✅ [{symbol}] LTP: {ltp:>10.2f} | H: {session_data[symbol]['high']:>10.2f} | L: {session_data[symbol]['low']:>10.2f} | Ticks: {session_data[symbol]['ticks']}")
            else:
                print(f"⚠️  [{symbol}] live_feed with no LTP data")
        else:
            print(f"⚠️  [{symbol}] Unknown message type: {msg_type}")

    except json.JSONDecodeError as e:
        print(f"⚠️  JSON Error: {e}")
    except Exception as e:
        print(f"❌ Message Error: {e}")
        import traceback
        traceback.print_exc()

def on_error(ws, error):
    """Handle WebSocket error."""
    symbol = ws.symbol if hasattr(ws, 'symbol') else "UNKNOWN"
    print(f"❌ [{symbol}] WebSocket Error: {error}")

def on_close(ws, close_status_code, close_msg):
    """Handle WebSocket close."""
    symbol = ws.symbol if hasattr(ws, 'symbol') else "UNKNOWN"
    print(f"⏹️  [{symbol}] WebSocket Closed - Code: {close_status_code}, Msg: {close_msg}")

def on_open(ws):
    """Handle WebSocket open - subscribe to instrument."""
    try:
        symbol_name = ws.symbol if hasattr(ws, 'symbol') else "UNKNOWN"
        instrument_key = ws.instrument_key if hasattr(ws, 'instrument_key') else "UNKNOWN"

        payload = {
            "guid": f"test-{symbol_name}-{int(time.time())}",
            "method": "sub",
            "data": {
                "instrument_keys": [instrument_key],
                "mode": "full"
            }
        }

        ws.send(json.dumps(payload))
        print(f"📡 [{symbol_name}] Subscribed to {instrument_key}")

    except Exception as e:
        print(f"❌ Subscription Error: {e}")

# ─────────────────────────────────────
# MAIN TEST FUNCTION
# ─────────────────────────────────────
def test_websocket(symbol, instrument_key, access_token):
    """Test WebSocket connection for a single symbol."""
    print(f"\n{'='*70}")
    print(f"Testing: {symbol} ({instrument_key})")
    print(f"{'='*70}")

    try:
        # Step 1: Get WebSocket URL from authorize endpoint
        print(f"1️⃣  Calling authorize endpoint...")
        headers = upstox_headers(access_token)
        auth_response = requests.get(
            "https://api.upstox.com/v3/feed/market-data-feed/authorize",
            headers=headers,
            timeout=10
        )

        if auth_response.status_code != 200:
            print(f"❌ Authorize failed: {auth_response.status_code}")
            print(f"   Response: {auth_response.text}")
            return False

        response_data = auth_response.json()
        if response_data.get('status') != 'success':
            print(f"❌ Authorize error: {response_data.get('errors')}")
            return False

        ws_url = response_data.get('data', {}).get('authorizedRedirectUri')
        if not ws_url:
            print(f"❌ No WebSocket URL in response")
            return False

        print(f"✅ Got WebSocket URL: {ws_url[:60]}...")

        # Step 2: Connect to WebSocket
        print(f"2️⃣  Connecting to WebSocket...")
        ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            ping_interval=30,
            ping_timeout=10
        )

        # Attach symbol info to ws object
        ws.symbol = symbol
        ws.instrument_key = instrument_key

        # Run for 15 seconds
        print(f"3️⃣  Running for 15 seconds (listening for ticks)...\n")

        def run_ws():
            ws.run_forever()

        ws_thread = threading.Thread(target=run_ws, daemon=True)
        ws_thread.start()

        # Wait 15 seconds
        time.sleep(15)
        ws.close()

        # Results
        print(f"\n{'─'*70}")
        if symbol in session_data:
            data = session_data[symbol]
            print(f"✅ SUCCESS for {symbol}!")
            print(f"   Session High: {data['high']}")
            print(f"   Session Low: {data['low']}")
            print(f"   Ticks Received: {data['ticks']}")
            return True
        else:
            print(f"⚠️  No ticks received for {symbol}")
            print(f"   This could mean:")
            print(f"   1. Market is closed")
            print(f"   2. No trading activity in the 15 second window")
            print(f"   3. WebSocket connected but message format is different")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

# ─────────────────────────────────────
# RUN TESTS
# ─────────────────────────────────────
if __name__ == "__main__":
    if ACCESS_TOKEN == "YOUR_ACCESS_TOKEN_HERE":
        print("❌ ERROR: Set your Upstox ACCESS_TOKEN in this script!")
        print("   Find it in your app at: st.session_state['access_token']")
        sys.exit(1)

    print(f"\n🧪 Upstox WebSocket Test Script")
    print(f"Testing {len(TEST_SYMBOLS)} instruments...\n")

    results = {}
    for symbol, instrument_key in TEST_SYMBOLS:
        success = test_websocket(symbol, instrument_key, ACCESS_TOKEN)
        results[symbol] = success
        time.sleep(2)  # Slight delay between tests

    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    for symbol, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {symbol}")

    print(f"\n{'='*70}")
    if all(results.values()):
        print(f"✅ All tests passed! WebSocket is working correctly.")
    else:
        print(f"⚠️  Some tests failed. Check token and market hours.")
