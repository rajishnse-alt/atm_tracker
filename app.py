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
st.markdown("""
<style>
    .block-container{padding-top:1rem;padding-bottom:1rem;}
    .stApp{background:#0e1117;}
    table{width:100%;border-collapse:collapse;font-size:14px;}
    th{background:#1a237e;color:white;padding:8px 12px;text-align:left;font-weight:500;}
    td{padding:7px 12px;border-bottom:1px solid #2a2a3a;}
    .ce-lbl{background:#0d47a1;color:white;}
    .pe-lbl{background:#4a148c;color:white;}
    .sum-row{background:#004d40;color:white;font-weight:500;}
    .sqrt-row{background:#bf360c;color:white;font-weight:500;}
    .bias-bear{background:#ffcccc;color:#cc0000;font-weight:600;}
    .bias-bull{background:#ccffcc;color:#006600;font-weight:600;}
    .strike-ce{background:white;color:#1565c0;font-weight:500;}
    .strike-pe{background:white;color:#6a1b9a;font-weight:500;}
    .price-ce{background:white;color:#0d47a1;}
    .price-pe{background:white;color:#4a148c;}
    .spot-val{font-size:22px;font-weight:600;color:white;}
    .spot-lbl{font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;}
    .atm-val{font-size:14px;color:#ffd54f;margin-top:2px;}
    .card{background:#1a1a2e;border-radius:10px;padding:.85rem 1.25rem;
          border:1px solid #2a2a4a;margin-bottom:.6rem;}
    .err-box{background:#2a1a1a;border:1px solid #7f1d1d;border-radius:8px;
             padding:.75rem 1rem;color:#fc8181;font-size:13px;margin-bottom:.6rem;}
    .login-box{background:#1a2030;border:1px solid #2a4080;border-radius:12px;
               padding:2rem;text-align:center;max-width:480px;margin:3rem auto;}
    .setup-box{background:#1a2a1a;border:1px solid #1f5f1f;border-radius:8px;
               padding:1rem 1.25rem;color:#a5d6a7;font-size:13px;line-height:2;}
    .refresh-note{font-size:11px;color:#555;text-align:right;margin-top:6px;}
    code{background:#2a2a3a;padding:2px 6px;border-radius:4px;font-size:12px;color:#90caf9;}
</style>
""", unsafe_allow_html=True)

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
# HELPERS
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

def fetch_expiry_dates(token, symbol):
    try:
        r = requests.get(
            UPSTOX_CONTRACT_URL,
            params={"instrument_key": INSTRUMENT_KEY[symbol]},
            headers=upstox_headers(token),
            timeout=15,
        )
        d = r.json()
        if r.status_code == 401:
            return None, "token_expired"
        if d.get("status") == "success" and d.get("data"):
            raw = d["data"]
            if raw and isinstance(raw[0], dict):
                dates = []
                for item in raw:
                    exp = (item.get("expiry")
                           or item.get("expiry_date")
                           or item.get("date")
                           or item.get("expiryDate")
                           or "")
                    if exp:
                        dates.append(str(exp))
            else:
                dates = [str(x) for x in raw]
            dates = sorted(set(dates))
            return dates if dates else None, None if dates else "Empty expiry list"
        return None, f"Expiry fetch failed: {d}"
    except Exception as e:
        return None, str(e)

def fetch_chain(token, symbol, expiry_date):
    cache_key = f"oc_{symbol}_{expiry_date}"
    time_key  = f"oc_time_{symbol}"
    now       = time.time()

    if (cache_key in st.session_state
            and time_key in st.session_state
            and now - st.session_state[time_key] < 180):
        return st.session_state[cache_key], None, st.session_state.get(f"oc_url_{symbol}", "cached")

    last_err  = "No response"
    last_raw  = {}

    for url in UPSTOX_OC_URLS:
        try:
            r = requests.get(
                url,
                params={"instrument_key": INSTRUMENT_KEY[symbol],
                        "expiry_date":    expiry_date},
                headers=upstox_headers(token),
                timeout=15,
            )
            last_raw = r.json()

            if r.status_code == 401:
                return None, "token_expired", url

            if last_raw.get("status") == "success":
                data = last_raw.get("data") or []
                if data:
                    st.session_state[cache_key]          = data
                    st.session_state[time_key]           = now
                    st.session_state[f"oc_url_{symbol}"] = url
                    return data, None, url
                else:
                    last_err = f"Empty data array from {url}"
            else:
                last_err = str(last_raw)

        except Exception as e:
            last_err = str(e)

    st.session_state[f"raw_{symbol}"] = last_raw
    return None, last_err, UPSTOX_OC_URLS[-1]

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

        ce_map[strike] = float((row.get("call_options") or {}).get("market_data", {}).get("ltp") or 0)
        pe_map[strike] = float((row.get("put_options") or {}).get("market_data", {}).get("ltp") or 0)

    if spot is None:
        raise ValueError("Could not determine underlying spot price")

    atm = snap(spot, step)

    ce_rows = [
        {"label": "ATM CE",   "strike": atm, "price": ce_map.get(float(atm), 0)},
        {"label": "ATM+1 CE", "strike": atm + step, "price": ce_map.get(float(atm+step), 0)},
        {"label": "ATM+2 CE", "strike": atm + 2*step, "price": ce_map.get(float(atm+2*step), 0)},
    ]

    pe_rows = [
        {"label": "ATM PE",   "strike": atm, "price": pe_map.get(float(atm), 0)},
        {"label": "ATM-1 PE", "strike": atm - step, "price": pe_map.get(float(atm-step), 0)},
        {"label": "ATM-2 PE", "strike": atm - 2*step, "price": pe_map.get(float(atm-2*step), 0)},
    ]

    ce_sum = sum(x["price"] for x in ce_rows)
    pe_sum = sum(x["price"] for x in pe_rows)

    return dict(
        spot=spot,
        atm=atm,
        ce_rows=ce_rows,
        pe_rows=pe_rows,
        ce_sum=ce_sum,
        pe_sum=pe_sum,
        ce_sqrt=math.sqrt(ce_sum),
        pe_sqrt=math.sqrt(pe_sum),
        bearish=math.sqrt(ce_sum) > math.sqrt(pe_sum)
    )

def render_table(r, symbol, expiry):
    st.markdown(f"<h4 style='color:white'>{symbol} | Exp: {expiry}</h4>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if not secrets_ok():
    st.stop()

api_key      = st.secrets["upstox"]["api_key"]
api_secret   = st.secrets["upstox"]["api_secret"]
redirect_uri = st.secrets["upstox"]["redirect_uri"]

qp = st.query_params
auth_code = qp.get("code")

if auth_code and "access_token" not in st.session_state:
    token, _ = exchange_code(api_key, api_secret, redirect_uri, auth_code)
    st.session_state["access_token"] = token
    st.session_state["token_acquired"] = time.time()
    st.query_params.clear()
    st.rerun()

if "access_token" not in st.session_state:
    st.markdown(f"[Login with Upstox]({build_auth_url(api_key, redirect_uri)})")
    st.stop()

access_token = st.session_state["access_token"]

col1, col2 = st.columns(2)

for col, sym in [(col1, "NIFTY"), (col2, "BANKNIFTY")]:
    with col:

        expiry_dates, _ = fetch_expiry_dates(access_token, sym)

        key = f"{sym}_expiry"

        if key not in st.session_state:
            st.session_state[key] = expiry_dates[0]

        if st.session_state[key] not in expiry_dates:
            st.session_state[key] = expiry_dates[0]

        selected_expiry = st.selectbox(sym + " Expiry", expiry_dates, key=key)

        data, _, _ = fetch_chain(access_token, sym, selected_expiry)

        result = parse(data, sym)

        render_table(result, sym, selected_expiry)

time.sleep(180)
st.rerun()
