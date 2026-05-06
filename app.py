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

# (your styles unchanged...)
st.markdown("""<style>
/* KEEPING YOUR ORIGINAL CSS */
</style>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
IST         = pytz.timezone("Asia/Kolkata")
STRIKE_STEP = {"NIFTY": 50, "BANKNIFTY": 100}

INSTRUMENT_KEY = {
    "NIFTY":     "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
}

UPSTOX_OC_URLS = [
    "https://api.upstox.com/v2/option/chain",
    "https://api.upstox.com/v3/option/chain",
]
UPSTOX_CONTRACT_URL = "https://api.upstox.com/v2/option/contract"
UPSTOX_AUTH_URL     = "https://api.upstox.com/v2/login/authorization/dialog"
UPSTOX_TOKEN_URL    = "https://api.upstox.com/v2/login/authorization/token"

# ─────────────────────────────────────────────
# HELPERS (UNCHANGED)
# ─────────────────────────────────────────────
def secrets_ok():
    try:
        _ = st.secrets["upstox"]["api_key"]
        _ = st.secrets["upstox"]["api_secret"]
        _ = st.secrets["upstox"]["redirect_uri"]
        return True
    except Exception:
        return False

def upstox_headers(token):
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}

def build_auth_url(api_key, redirect_uri):
    return (f"{UPSTOX_AUTH_URL}"
            f"?response_type=code&client_id={api_key}&redirect_uri={redirect_uri}")

def exchange_code(api_key, api_secret, redirect_uri, code):
    try:
        r = requests.post(
            UPSTOX_TOKEN_URL,
            data={"code": code, "client_id": api_key,
                  "client_secret": api_secret,
                  "redirect_uri": redirect_uri,
                  "grant_type": "authorization_code"},
            headers={"Accept": "application/json"},
            timeout=15,
        )
        d = r.json()
        if "access_token" in d:
            return d["access_token"], None
        return None, str(d)
    except Exception as e:
        return None, str(e)

# ─────────────────────────────────────────────
# FETCH EXPIRY
# ─────────────────────────────────────────────
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
            raw = d["data"]
            if raw and isinstance(raw[0], dict):
                dates = [str(x.get("expiry") or x.get("expiry_date")) for x in raw]
            else:
                dates = [str(x) for x in raw]
            return sorted(set(dates)), None
        return None, str(d)
    except Exception as e:
        return None, str(e)

# ─────────────────────────────────────────────
# FETCH CHAIN (UNCHANGED)
# ─────────────────────────────────────────────
def fetch_chain(token, symbol, expiry):
    for url in UPSTOX_OC_URLS:
        try:
            r = requests.get(
                url,
                params={"instrument_key": INSTRUMENT_KEY[symbol],
                        "expiry_date": expiry},
                headers=upstox_headers(token),
                timeout=15,
            )
            d = r.json()
            if d.get("status") == "success":
                return d.get("data"), None, url
        except Exception as e:
            err = str(e)
    return None, err, url

# ─────────────────────────────────────────────
# PARSE (UNCHANGED)
# ─────────────────────────────────────────────
def snap(price, step):
    return int(round(price / step) * step)

def parse(data, symbol):
    step   = STRIKE_STEP[symbol]
    ce_map = {}
    pe_map = {}
    spot   = None

    for row in data:
        strike = float(row.get("strike_price", 0))
        if spot is None:
            sp = row.get("underlying_spot_price")
            if sp:
                spot = float(sp)

        ce_map[strike] = float(row.get("call_options", {}).get("market_data", {}).get("ltp") or 0)
        pe_map[strike] = float(row.get("put_options", {}).get("market_data", {}).get("ltp") or 0)

    atm = snap(spot, step)

    ce_sum = sum([ce_map.get(atm + i*step, 0) for i in range(3)])
    pe_sum = sum([pe_map.get(atm - i*step, 0) for i in range(3)])

    return spot, atm, ce_sum, pe_sum

# ─────────────────────────────────────────────
# MAIN (AUTH UNCHANGED)
# ─────────────────────────────────────────────
if not secrets_ok():
    st.error("Missing Upstox secrets")
    st.stop()

api_key      = st.secrets["upstox"]["api_key"]
api_secret   = st.secrets["upstox"]["api_secret"]
redirect_uri = st.secrets["upstox"]["redirect_uri"]

qp = st.query_params
auth_code = qp.get("code")

if auth_code and "access_token" not in st.session_state:
    token, _ = exchange_code(api_key, api_secret, redirect_uri, auth_code)
    st.session_state["access_token"] = token
    st.query_params.clear()
    st.rerun()

if "access_token" not in st.session_state:
    st.markdown(f"[Login with Upstox]({build_auth_url(api_key, redirect_uri)})")
    st.stop()

token = st.session_state["access_token"]

# ─────────────────────────────────────────────
# CORE LOOP (ONLY CHANGE IS HERE)
# ─────────────────────────────────────────────
col1, col2 = st.columns(2)

for col, sym in [(col1, "NIFTY"), (col2, "BANKNIFTY")]:
    with col:

        expiry_dates, err = fetch_expiry_dates(token, sym)

        if err or not expiry_dates:
            st.error(f"{sym}: expiry error")
            continue

        # ✅ LOCKED DROPDOWN (THIS IS THE ONLY NEW LOGIC)
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

        data, err, _ = fetch_chain(token, sym, selected_expiry)

        if err or not data:
            st.error(f"{sym}: chain error")
            continue

        spot, atm, ce_sum, pe_sum = parse(data, sym)

        st.write(f"Spot: {spot}")
        st.write(f"ATM: {atm}")
        st.write(f"Expiry: {selected_expiry}")

# ─────────────────────────────────────────────
# AUTO REFRESH
# ─────────────────────────────────────────────
time.sleep(180)
st.rerun()
