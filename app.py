import streamlit as st
import requests
import math
import time
from datetime import datetime
import pytz

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(page_title="ATM Options Tracker", page_icon="📊", layout="wide")

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
IST = pytz.timezone("Asia/Kolkata")

STRIKE_STEP = {"NIFTY": 50, "BANKNIFTY": 100}

INSTRUMENT_KEY = {
    "NIFTY": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
}

UPSTOX_OC_URLS = [
    "https://api.upstox.com/v2/option/chain",
    "https://api.upstox.com/v3/option/chain",
]

UPSTOX_CONTRACT_URL = "https://api.upstox.com/v2/option/contract"

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def upstox_headers(token):
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}

def fetch_expiry_dates(token, symbol):
    try:
        r = requests.get(
            UPSTOX_CONTRACT_URL,
            params={"instrument_key": INSTRUMENT_KEY[symbol]},
            headers=upstox_headers(token),
            timeout=15,
        )
        d = r.json()

        if d.get("status") == "success":
            raw = d.get("data", [])
            if raw and isinstance(raw[0], dict):
                dates = [x.get("expiry") or x.get("expiry_date") for x in raw if x]
            else:
                dates = raw

            dates = sorted(set([str(x) for x in dates if x]))
            return dates, None

        return None, str(d)

    except Exception as e:
        return None, str(e)

def fetch_chain(token, symbol, expiry):
    for url in UPSTOX_OC_URLS:
        try:
            r = requests.get(
                url,
                params={
                    "instrument_key": INSTRUMENT_KEY[symbol],
                    "expiry_date": expiry
                },
                headers=upstox_headers(token),
                timeout=15,
            )
            d = r.json()

            if d.get("status") == "success" and d.get("data"):
                return d["data"], None, url

        except Exception as e:
            last_err = str(e)

    return None, last_err, url

def snap(price, step):
    return int(round(price / step) * step)

def parse(data, symbol):
    step = STRIKE_STEP[symbol]
    ce_map, pe_map = {}, {}
    spot = None

    for row in data:
        strike = float(row.get("strike_price", 0))

        if spot is None:
            sp = row.get("underlying_spot_price")
            if sp:
                spot = float(sp)

        ce = row.get("call_options", {}).get("market_data", {})
        pe = row.get("put_options", {}).get("market_data", {})

        ce_map[strike] = float(ce.get("ltp") or 0)
        pe_map[strike] = float(pe.get("ltp") or 0)

    if spot is None:
        common = set(ce_map) & set(pe_map)
        spot = min(common, key=lambda s: abs(ce_map[s] - pe_map[s]))

    atm = snap(spot, step)

    ce_prices = [
        ce_map.get(atm, 0),
        ce_map.get(atm + step, 0),
        ce_map.get(atm + 2 * step, 0),
    ]

    pe_prices = [
        pe_map.get(atm, 0),
        pe_map.get(atm - step, 0),
        pe_map.get(atm - 2 * step, 0),
    ]

    ce_sum = sum(ce_prices)
    pe_sum = sum(pe_prices)

    return {
        "spot": spot,
        "atm": atm,
        "ce_sum": ce_sum,
        "pe_sum": pe_sum,
        "ce_sqrt": math.sqrt(ce_sum),
        "pe_sqrt": math.sqrt(pe_sum),
    }

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
st.title("📊 ATM Options Tracker")

access_token = st.text_input("Enter Upstox Access Token")

if not access_token:
    st.stop()

col1, col2 = st.columns(2)

for col, sym in [(col1, "NIFTY"), (col2, "BANKNIFTY")]:
    with col:

        expiry_dates, err = fetch_expiry_dates(access_token, sym)

        if err or not expiry_dates:
            st.error(f"{sym} expiry error: {err}")
            continue

        # ── LOCKED EXPIRY DROPDOWN ─────────────────────
        key = f"{sym}_expiry"

        if key not in st.session_state:
            st.session_state[key] = expiry_dates[0]

        if st.session_state[key] not in expiry_dates:
            st.session_state[key] = expiry_dates[0]

        selected_expiry = st.selectbox(
            f"{sym} Expiry",
            expiry_dates,
            key=key
        )

        # ── FETCH DATA ─────────────────────────────
        data, err, _ = fetch_chain(access_token, sym, selected_expiry)

        if err or not data:
            st.error(f"{sym} chain error: {err}")
            continue

        result = parse(data, sym)

        # ── DISPLAY ─────────────────────────────
        st.metric(f"{sym} Spot", f"{result['spot']:.2f}")
        st.write(f"ATM: {result['atm']}")
        st.write(f"Expiry: {selected_expiry}")

        st.write("CE √:", round(result["ce_sqrt"], 2))
        st.write("PE √:", round(result["pe_sqrt"], 2))

        bias = "BEARISH" if result["ce_sqrt"] > result["pe_sqrt"] else "BULLISH"
        st.subheader(f"Bias: {bias}")

# ── AUTO REFRESH ─────────────────────────────
time.sleep(180)
st.rerun()
