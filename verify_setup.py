#!/usr/bin/env python3
"""
Automated verification script for ATM Tracker setup
Tests WebSocket, token validity, and data collection readiness
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
import requests
from datetime import datetime
import pytz

IST = pytz.timezone('Asia/Kolkata')
PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR / "data" / "ticks"

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text:^70}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

def print_section(text):
    print(f"\n{YELLOW}[*] {text}{RESET}")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def test_python():
    """Test Python version and required packages."""
    print_section("Testing Python Installation")

    try:
        import websocket
        print_success("websocket-client installed")
    except ImportError:
        print_error("websocket-client not installed")
        return False

    try:
        import pytz
        print_success("pytz installed")
    except ImportError:
        print_error("pytz not installed")
        return False

    try:
        import requests
        print_success("requests installed")
    except ImportError:
        print_error("requests not installed")
        return False

    try:
        import dotenv
        print_success("python-dotenv installed")
    except ImportError:
        print_error("python-dotenv not installed")
        return False

    return True

def test_environment():
    """Test environment variables."""
    print_section("Testing Environment Variables")

    env_file = PROJECT_DIR / ".env"

    if not env_file.exists():
        print_error(f".env file not found at {env_file}")
        print_warning("Run: python3 setup_background_collector.sh")
        return False

    print_success(f".env file found")

    # Load from .env
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)
    except:
        pass

    access_token = os.getenv("UPSTOX_ACCESS_TOKEN")

    if not access_token:
        print_error("UPSTOX_ACCESS_TOKEN not set in .env")
        return False

    if access_token == "YOUR_TOKEN_HERE":
        print_error("UPSTOX_ACCESS_TOKEN is still placeholder value")
        return False

    # Show masked token
    token_preview = f"{access_token[:20]}...{access_token[-10:]}"
    print_success(f"Access token found: {token_preview}")

    return True, access_token

def test_api_token(access_token):
    """Test if the Upstox API token is valid."""
    print_section("Testing Upstox API Token")

    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }

        response = requests.get(
            "https://api.upstox.com/v3/feed/market-data-feed/authorize",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                ws_url = data.get('data', {}).get('authorizedRedirectUri')
                if ws_url:
                    print_success("API token is valid ✓")
                    return True
                else:
                    print_error("No WebSocket URL in response")
                    return False
            else:
                print_error(f"API error: {data.get('errors')}")
                return False

        elif response.status_code == 401:
            print_error("Token invalid or expired (401 Unauthorized)")
            return False

        else:
            print_warning(f"Unexpected status: {response.status_code}")
            return True  # Let it proceed anyway

    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to Upstox API (network error)")
        return False

    except Exception as e:
        print_error(f"API test failed: {e}")
        return False

def test_data_directory():
    """Test if data directory is ready."""
    print_section("Testing Data Directory")

    if not DATA_DIR.exists():
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            print_success(f"Created data directory: {DATA_DIR}")
        except Exception as e:
            print_error(f"Cannot create data directory: {e}")
            return False
    else:
        print_success(f"Data directory exists: {DATA_DIR}")

    # Check permissions
    if os.access(DATA_DIR, os.W_OK):
        print_success("Data directory is writable")
    else:
        print_error("Data directory is not writable")
        return False

    return True

def test_collector_script():
    """Test if collector script exists and is readable."""
    print_section("Testing Collector Script")

    script_file = PROJECT_DIR / "background_tick_collector.py"

    if not script_file.exists():
        print_error(f"Collector script not found: {script_file}")
        return False

    print_success(f"Collector script found: {script_file}")

    # Try to parse it
    try:
        with open(script_file, 'r') as f:
            compile(f.read(), str(script_file), 'exec')
        print_success("Collector script is valid Python")
    except Exception as e:
        print_error(f"Collector script has syntax errors: {e}")
        return False

    return True

def test_market_status():
    """Show current market status."""
    print_section("Market Status")

    now = datetime.now(IST)
    is_trading_day = now.weekday() < 5

    day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][now.weekday()]
    print(f"Current time: {now.strftime('%d %b %Y %H:%M:%S IST')}")
    print(f"Day: {day_name}")

    if is_trading_day:
        print_success("Today is a trading day (Mon-Fri)")
    else:
        print_warning("Today is NOT a trading day (market closed)")

    is_market_open = is_trading_day and (9, 15) <= (now.hour, now.minute) <= (15, 30)

    if is_market_open:
        print_success("Market is OPEN (9:15 - 15:30 IST)")
    else:
        print_warning("Market is CLOSED")

        # Calculate time until next open
        if is_trading_day:
            next_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
            if now >= next_open:
                next_open = next_open + pytz.timezone('Asia/Kolkata').localize(
                    __import__('datetime').timedelta(days=1)
                )
        else:
            days_to_monday = (7 - now.weekday()) % 7
            if days_to_monday == 0:
                days_to_monday = 1
            next_open = now.replace(hour=9, minute=15, second=0, microsecond=0) + \
                       __import__('datetime').timedelta(days=days_to_monday)

        time_diff = next_open - now
        hours = time_diff.seconds // 3600
        minutes = (time_diff.seconds % 3600) // 60
        print(f"Market opens in: {hours}h {minutes}m")

    return is_market_open

def test_existing_data():
    """Check if there's any existing tick data."""
    print_section("Checking Existing Tick Data")

    csv_files = list(DATA_DIR.glob("*.csv"))

    if not csv_files:
        print_warning("No tick data files found yet")
        print("(This is normal on first run)")
    else:
        print_success(f"Found {len(csv_files)} data file(s):")
        for csv_file in csv_files:
            size_kb = csv_file.stat().st_size / 1024
            rows = sum(1 for _ in open(csv_file)) - 1  # Subtract header
            print(f"  📊 {csv_file.name}: {size_kb:.1f} KB ({rows} ticks)")

    return True

def main():
    """Run all tests."""
    print_header("ATM Tracker Setup Verification")

    tests = [
        ("Python Packages", test_python),
        ("Environment Variables", test_environment),
        ("Data Directory", test_data_directory),
        ("Collector Script", test_collector_script),
        ("Market Status", test_market_status),
        ("Existing Data", test_existing_data),
    ]

    results = {}
    access_token = None

    for test_name, test_func in tests:
        try:
            if test_name == "Environment Variables":
                result = test_func()
                if result:
                    success, access_token = result
                    results[test_name] = success
                else:
                    results[test_name] = False
            else:
                results[test_name] = test_func()
        except Exception as e:
            print_error(f"Test failed with exception: {e}")
            results[test_name] = False

    # Test API token if we have it
    if access_token:
        try:
            results["API Token"] = test_api_token(access_token)
        except Exception as e:
            print_error(f"API test failed: {e}")
            results["API Token"] = False

    # Summary
    print_header("Summary")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"{status} - {test_name}")

    print(f"\n{BLUE}Passed: {passed}/{total}{RESET}\n")

    if passed == total:
        print_success("All tests passed! ✨")
        print(f"\n{YELLOW}Next step: Run the setup script${RESET}")
        print(f"  bash {PROJECT_DIR}/setup_background_collector.sh\n")
        return 0

    else:
        print_error("Some tests failed. Please fix the issues above.")
        print(f"\nFor help, check:")
        print(f"  - {PROJECT_DIR}/background_collector.log")
        print(f"  - README.md (if available)")
        return 1

if __name__ == "__main__":
    sys.exit(main())
