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

# (your full CSS — unchanged)
st.markdown("""<style>
.block-container{padding-top:1rem;padding-bottom:1rem;}
.stApp{background:#0e1117;}
</style>""", unsafe_allow_html=True)

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
            timeout=10,
        )
        d = r.json()
        raw = d.get("data", [])

        if raw and isinstance(raw[0], dict):
            dates = [str(x.get("expiry") or x.get("expiry_date")) for x in raw if x]
        else:
            dates = raw

        return sorted(set(dates)), None
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
                timeout=10,
            )
            d = r.json()
            if d.get("status") == "success" and d.get("data"):
                return d["data"], None
        except:
            pass
    return None, "API failed"

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

        ce_map[strike] = float(row.get("call_options", {}).get("market_data", {}).get("ltp") or 0)
        pe_map[strike] = float(row.get("put_options", {}).get("market_data", {}).get("ltp") or 0)

    if spot is None:
        raise ValueError("Spot not found")

    atm = snap(spot, step)

    ce_sum = sum([ce_map.get(atm + i*step, 0) for i in range(3)])
    pe_sum = sum([pe_map.get(atm - i*step, 0) for i in range(3)])

    return spot, atm, ce_sum, pe_sum

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
st.title("📊 ATM Options Tracker")

token = st.text_input("Access Token")

if not token:
    st.stop()

col1, col2 = st.columns(2)

for col, sym in [(col1, "NIFTY"), (col2, "BANKNIFTY")]:
    with col:

        expiry_dates, err = fetch_expiry_dates(token, sym)

        if err or not expiry_dates:
            st.error(f"{sym} expiry error")
            continue

        # ✅ LOCKED EXPIRY
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

        data, err = fetch_chain(token, sym, selected_expiry)

        if err or not data:
            st.error(f"{sym} data error")
            continue

        try:
            spot, atm, ce_sum, pe_sum = parse(data, sym)
        except Exception as e:
            st.error(str(e))
            continue

        st.write(f"Spot: {spot}")
        st.write(f"ATM: {atm}")
        st.write(f"Expiry: {selected_expiry}")

        st.write("CE:", ce_sum)
        st.write("PE:", pe_sum)

# auto refresh
time.sleep(180)
st.rerun()
