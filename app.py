import streamlit as st
import requests
import math
import time
from datetime import datetime, timedelta
import pytz
from scipy.stats import norm
from scipy.optimize import brentq

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(page_title="ATM Options Tracker", page_icon="📊", layout="wide")
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;600&family=Syne:wght@600;700;800&display=swap');

  :root {
    --bg:        #080c14;
    --surface:   #0d1321;
    --border:    #1c2840;
    --border2:   #253352;
    --text:      #c8d8f0;
    --muted:     #4a6080;
    --ce:        #2979ff;
    --ce-dim:    #0d1e40;
    --pe:        #ab47bc;
    --pe-dim:    #1a0d24;
    --bull:      #00e676;
    --bull-dim:  #003318;
    --bear:      #ff5252;
    --bear-dim:  #2a0808;
    --gold:      #ffc940;
    --gold-dim:  #2a1e00;
    --mono: 'JetBrains Mono', monospace;
    --display: 'Syne', sans-serif;
  }

  html, body, .stApp { background: var(--bg) !important; }
  .block-container { padding: .75rem 1.2rem 1rem !important; }

  .app-header { display: flex; align-items: baseline; gap: 10px; margin-bottom: 4px; }
  .app-title  { font-family: var(--display); font-size: 22px; font-weight: 800; color: white; letter-spacing: -.3px; }
  .app-sub    { font-family: var(--mono); font-size: 11px; color: var(--muted); letter-spacing: .5px; }

  .sec-hdr {
    font-family: var(--display); font-size: 11px; font-weight: 700;
    color: var(--muted); letter-spacing: 2px; text-transform: uppercase;
    margin: 1.1rem 0 .45rem; padding-bottom: 5px;
    border-bottom: 1px solid var(--border);
  }

  .inst-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: .6rem .85rem .55rem;
    margin-bottom: .45rem; position: relative; overflow: hidden;
  }
  .inst-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, var(--ce), var(--pe));
  }
  .inst-name { font-family: var(--display); font-size: 16px; font-weight: 800; color: white; letter-spacing: .4px; line-height: 1; }
  .inst-meta { font-family: var(--mono); font-size: 10px; color: var(--muted); margin-top: 3px; letter-spacing: .3px; }
  .inst-spot { font-family: var(--mono); font-size: 18px; font-weight: 600; color: white; letter-spacing: -.5px; }
  .inst-atm  { font-family: var(--mono); font-size: 11px; color: var(--gold); margin-top: 1px; }

  .pcr-row   { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-top: 5px; }
  .pcr-wrap  { display: inline-flex; align-items: center; gap: 6px; background: var(--surface); border: 1px solid var(--border2); border-radius: 6px; padding: 3px 9px 3px 7px; }
  .pcr-label { font-family: var(--mono); font-size: 10px; color: var(--muted); letter-spacing: 1px; text-transform: uppercase; }
  .pcr-val   { font-family: var(--mono); font-size: 13px; font-weight: 600; }
  .pcr-bull-c { color: var(--bull); }
  .pcr-bear-c { color: var(--bear); }
  .pcr-neut-c { color: var(--gold); }
  .pcr-tag    { font-family: var(--mono); font-size: 9px; font-weight: 600; padding: 1px 5px; border-radius: 3px; letter-spacing: .5px; text-transform: uppercase; }
  .pcr-tag-bull { background: var(--bull-dim); color: var(--bull); }
  .pcr-tag-bear { background: var(--bear-dim); color: var(--bear); }
  .pcr-tag-neut { background: var(--gold-dim); color: var(--gold); }
  .pcr-divider  { color: var(--border2); font-size: 16px; line-height: 1; }

  .opt-table { width: 100%; border-collapse: collapse; font-family: var(--mono); font-size: 11px; margin-bottom: .5rem; }
  .opt-table thead th { background: transparent; color: var(--muted); font-size: 9px; font-weight: 600; letter-spacing: 1.5px; text-transform: uppercase; padding: 4px 6px; border-bottom: 1px solid var(--border); text-align: left; }
  .opt-table thead th:last-child { text-align: right; }
  .opt-table td { padding: 3px 6px; border-bottom: 1px solid var(--border); white-space: nowrap; }
  .opt-table td:last-child { text-align: right; }

  .r-ce    { color: var(--ce); }
  .r-pe    { color: var(--pe); }
  .r-ce-bg { background: var(--ce-dim); }
  .r-pe-bg { background: var(--pe-dim); }
  .r-sum   { background: #0a1a10; }
  .r-sum td  { color: #4caf50 !important; font-weight: 600; font-size: 11px; }
  .r-sqrt  { background: #150b00; }
  .r-sqrt td { color: var(--gold) !important; font-weight: 600; font-size: 11px; }
  .r-bias td { font-weight: 700; font-size: 11px; padding: 4px 6px; }
  .r-bias-bull { background: var(--bull-dim); }
  .r-bias-bull td { color: var(--bull) !important; }
  .r-bias-bear { background: var(--bear-dim); }
  .r-bias-bear td { color: var(--bear) !important; }

  /* ── Trend row ── */
  .r-trend td { font-weight: 800; font-size: 12px; padding: 6px 8px; letter-spacing: .4px; border-radius: 0 0 8px 8px; }
  .r-trend-bull { background: #002a10; border-top: 2px solid var(--bull); }
  .r-trend-bull td { color: var(--bull) !important; }
  .r-trend-bear { background: #1e0404; border-top: 2px solid var(--bear); }
  .r-trend-bear td { color: var(--bear) !important; }
  .r-trend-neut { background: #1a1400; border-top: 2px solid var(--gold); }
  .r-trend-neut td { color: var(--gold) !important; }
  .r-trend-conf { background: #1a1a00; border-top: 2px solid #FFD700; }
  .r-trend-conf td { color: #FFD700 !important; }

  .tag-ce { display: inline-block; background: #102040; color: var(--ce); font-size: 9px; font-weight: 600; padding: 1px 5px; border-radius: 3px; letter-spacing: .5px; border: 1px solid #1a3060; }
  .tag-pe { display: inline-block; background: #1e0a28; color: var(--pe); font-size: 9px; font-weight: 600; padding: 1px 5px; border-radius: 3px; letter-spacing: .5px; border: 1px solid #3a1a50; }
  .strike-num { color: var(--text); font-weight: 600; }
  .price-num  { font-weight: 600; }

  .rrs-table { width: 100%; border-collapse: collapse; font-family: var(--mono); font-size: 11px; margin-bottom: .5rem; }
  .rrs-table td { padding: 4px 7px; border-bottom: 1px solid var(--border); white-space: nowrap; vertical-align: middle; }
  .rrs-table .lbl   { color: var(--muted); font-size: 10px; width: 38%; }
  .rrs-table .v-ce  { color: #00BFFF; font-weight: 600; }
  .rrs-table .v-pe  { color: #FF69B4; font-weight: 600; }
  .rrs-table .v-y   { color: #FFD700; font-weight: 600; }
  .rrs-table .v-g   { color: #00e676; font-weight: 600; }
  .rrs-table .v-r   { color: #ff5252; font-weight: 600; }
  .rrs-table .v-o   { color: #FFA600; font-weight: 600; }
  .rrs-table .v-w   { color: white;   font-weight: 600; }
  .rrs-table .v-gray{ color: #666;    font-weight: 400; }
  .rrs-table .v-aq  { color: #00FFFF; font-weight: 600; }
  .rrs-table .sec-hdr-row td { background: #1a1a1a; color: #666; font-size: 9px; letter-spacing: 1.5px; text-transform: uppercase; padding: 5px 7px; }
  .rrs-table .signal-bull td { background: #003318; color: #00e676 !important; font-weight: 700; }
  .rrs-table .signal-bear td { background: #2a0808; color: #ff5252 !important; font-weight: 700; }
  .rrs-table .signal-neut td { background: #1a1600; color: #FFA600 !important; font-weight: 700; }
  .rrs-table .signal-conf td { background: #1a1a00; color: #FFD700 !important; font-weight: 700; }
  .spcl-val { font-size: 20px !important; font-weight: 800 !important; color: #FFA600 !important; letter-spacing: -1px; }

  .spcl-wrap  { display: inline-flex; align-items: center; gap: 6px; background: var(--surface); border: 1px solid var(--border2); border-radius: 6px; padding: 3px 9px 3px 7px; }
  .spcl-label { font-family: var(--mono); font-size: 10px; color: var(--muted); letter-spacing: 1px; text-transform: uppercase; }
  .spcl-val-display { font-family: var(--mono); font-size: 13px; font-weight: 600; }
  .spcl-bull { color: #00e676; }
  .spcl-bear { color: #CC7722; }

  .trade-setup-wrap { display: inline-block; background: var(--surface); border: 1px solid var(--border2); border-radius: 6px; padding: 5px 8px; font-family: var(--mono); font-size: 10px; }
  .trade-setup-label { color: var(--muted); letter-spacing: 1px; text-transform: uppercase; margin-bottom: 3px; display: block; font-weight: 600; }
  .trade-side { margin: 3px 0; }
  .trade-ce { color: #00BFFF; font-weight: 600; }
  .trade-pe { color: #FF69B4; font-weight: 600; }
  .trade-buy { color: #00e676; }
  .trade-sell { color: #ff5252; }
  .trade-qty { color: #FFD700; font-weight: 600; }
  .trade-strike { font-weight: 600; }
  .trade-strike-valid { background: rgba(0, 230, 118, 0.35); padding: 2px 4px; border-radius: 3px; border: 1px solid #00e676; color: #00e676; font-weight: 700; }
  .strikes-display-wrap { display: inline-flex; align-items: center; gap: 12px; background: var(--surface); border: 1px solid var(--border2); border-radius: 6px; padding: 3px 9px 3px 7px; }
  .strikes-label { font-family: var(--mono); font-size: 10px; color: var(--muted); letter-spacing: 1px; text-transform: uppercase; }
  .strikes-side { font-family: var(--mono); font-size: 11px; }
  .strikes-ce { color: #00BFFF; }
  .strikes-pe { color: #FF69B4; }
  .strike-item { display: inline-block; margin-right: 6px; }
  .strike-val { font-weight: 600; }
  .strike-valid { background: rgba(0, 230, 118, 0.35); padding: 2px 4px; border-radius: 3px; border: 1px solid #00e676; color: #00e676; font-weight: 700; }

  .valid-strikes-wrap { display: inline-flex; flex-direction: column; align-items: flex-start; background: var(--surface); border: 1px solid var(--border2); border-radius: 6px; padding: 4px 8px; font-family: var(--mono); font-size: 10px; margin-left: 4px; gap: 2px; }
  .valid-strikes-label { color: var(--muted); letter-spacing: 1px; text-transform: uppercase; font-weight: 600; font-size: 9px; }
  .valid-strikes-side { font-weight: 600; font-size: 10px; white-space: nowrap; }
  .valid-strikes-ce { color: #2979ff; }
  .valid-strikes-pe { color: #ab47bc; }
  .valid-strike-item { display: inline-block; padding: 2px 4px; background: rgba(0, 230, 118, 0.2); border: 1px solid #00e676; border-radius: 3px; color: #00e676; font-weight: 600; }

  .btst-bull { color: #00e676 !important; font-weight: 700; }
  .btst-bear { color: #ff5252 !important; font-weight: 700; }
  .btst-neut { color: #FFA600 !important; font-weight: 700; }

  .err-box   { background: #1a0808; border: 1px solid #5a1a1a; border-radius: 8px; padding: .6rem .9rem; color: #fc8181; font-family: var(--mono); font-size: 12px; margin-bottom: .5rem; }
  .login-box { background: var(--surface); border: 1px solid var(--border2); border-radius: 14px; padding: 2.5rem 2rem; text-align: center; max-width: 460px; margin: 3rem auto; }
  .setup-box { background: #0d1a10; border: 1px solid #1a4020; border-radius: 10px; padding: 1rem 1.25rem; color: #a5d6a7; font-family: var(--mono); font-size: 12px; line-height: 2; }
  .refresh-note { font-family: var(--mono); font-size: 10px; color: var(--muted); text-align: right; margin-top: 8px; }
  code { background: #1a2030; padding: 2px 6px; border-radius: 4px; font-size: 12px; color: #90caf9; font-family: var(--mono); }

  #MainMenu, footer, header { visibility: hidden; }
  .stSpinner > div { border-top-color: var(--ce) !important; }
  div[data-testid="stSelectbox"] label { font-family: var(--mono) !important; font-size: 11px !important; color: var(--muted) !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS  (mirrors Pine default inputs)
# ─────────────────────────────────────────────
IST = pytz.timezone("Asia/Kolkata")

STRIKE_STEP_FIXED = {"NIFTY": 50, "BANKNIFTY": 100}

# Pine parameter defaults
TREND_EMA_LEN       = 5     # trendEmaLen
TREND_CONF_BARS     = 3     # trendConfBars
REV_CONF_BARS       = 2     # revConfBars
STRONG_MOVE_COEFF   = 1.2   # strongMoveCoeff
DOM_CONF_BARS       = 2     # domConfBars
PRE_GAMMA_MIN_SCORE = 3     # preGammaMinScore
PRE_GAMMA_VOL_BARS  = 2     # preGammaVolBars
DOMINANCE_THRESHOLD = 0.04  # threshold

def infer_strike_step(data):
    from collections import Counter
    strikes = sorted({float(row.get("strike_price", 0)) for row in data if row.get("strike_price")})
    if len(strikes) < 2:
        return 50
    diffs = [strikes[i+1] - strikes[i] for i in range(len(strikes)-1)]
    return int(Counter(diffs).most_common(1)[0][0])

INSTRUMENT_KEY = {
    "NIFTY":     "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "HDFCBANK":  "NSE_EQ|INE040A01034",
    "ICICIBANK": "NSE_EQ|INE090A01021",
    "SBIN":      "NSE_EQ|INE062A01020",
    "RELIANCE":  "NSE_EQ|INE002A01018",
}

DISPLAY_NAME = {
    "NIFTY": "NIFTY", "BANKNIFTY": "BANKNIFTY",
    "HDFCBANK": "HDFC Bank", "ICICIBANK": "ICICI Bank",
    "SBIN": "SBI", "RELIANCE": "Reliance",
}

SYMBOL_GROUPS = [
    ("📈 Index Options",    ["NIFTY",    "BANKNIFTY"]),
    ("🏦 Bank Stocks",      ["HDFCBANK", "ICICIBANK"]),
    ("🏢 Large Cap Stocks", ["SBIN",     "RELIANCE"]),
]

UPSTOX_OC_URLS           = ["https://api.upstox.com/v2/option/chain", "https://api.upstox.com/v3/option/chain"]
UPSTOX_CONTRACT_URL      = "https://api.upstox.com/v2/option/contract"
UPSTOX_AUTH_URL          = "https://api.upstox.com/v2/login/authorization/dialog"
UPSTOX_TOKEN_URL         = "https://api.upstox.com/v2/login/authorization/token"
UPSTOX_MARKET_QUOTE      = "https://api.upstox.com/v2/market-quote/quotes"
UPSTOX_HISTORICAL_CANDLE = "https://api.upstox.com/v3/historical-candle"

# ─────────────────────────────────────────────
# EMA HELPER
# ─────────────────────────────────────────────
def ema_update(prev_ema, new_val, period):
    if prev_ema is None:
        return float(new_val)
    alpha = 2.0 / (period + 1)
    return alpha * float(new_val) + (1.0 - alpha) * float(prev_ema)

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
    return f"{UPSTOX_AUTH_URL}?response_type=code&client_id={api_key}&redirect_uri={redirect_uri}"

def exchange_code(api_key, api_secret, redirect_uri, code):
    try:
        r = requests.post(
            UPSTOX_TOKEN_URL,
            data={"code": code, "client_id": api_key, "client_secret": api_secret,
                  "redirect_uri": redirect_uri, "grant_type": "authorization_code"},
            headers={"Accept": "application/json"}, timeout=15)
        d = r.json()
        return (d["access_token"], None) if "access_token" in d else (None, str(d))
    except Exception as e:
        return None, str(e)

# ─────────────────────────────────────────────
# FETCH VIX
# ─────────────────────────────────────────────
def fetch_vix(token):
    cache_key = "vix_data"; time_key = "vix_time"
    now = time.time()
    if (cache_key in st.session_state and time_key in st.session_state
            and now - st.session_state[time_key] < 60):
        return st.session_state[cache_key]
    try:
        r = requests.get(UPSTOX_MARKET_QUOTE,
                         params={"symbol": "NSE_INDEX|India VIX"},
                         headers=upstox_headers(token), timeout=10)
        d = r.json()
        if d.get("status") == "success":
            for key in d.get("data", {}):
                q    = d["data"][key]
                ltp  = q.get("last_price") or q.get("ltp") or 0
                dopen = (q.get("ohlc") or {}).get("open") or ltp
                if ltp:
                    res = {"ltp": float(ltp), "day_open": float(dopen)}
                    st.session_state[cache_key] = res
                    st.session_state[time_key]  = now
                    return res
    except Exception:
        pass
    return st.session_state.get(cache_key)

# ─────────────────────────────────────────────
# BLACK-SCHOLES PRICING
# ─────────────────────────────────────────────
def bs_call(S, K, T, r, sigma):
    """Black-Scholes call option price."""
    if T <= 0 or sigma <= 0:
        return max(S - K, 0)
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)

def bs_put(S, K, T, r, sigma):
    """Black-Scholes put option price."""
    if T <= 0 or sigma <= 0:
        return max(K - S, 0)
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

def calculate_implied_volatility(option_price, S, K, T, r, is_call=True):
    """Calculate implied volatility using Brent's method."""
    if option_price <= 0 or T <= 0:
        return 0.15  # Default to 15% if cannot calculate

    def objective(sigma):
        if is_call:
            return bs_call(S, K, T, r, sigma) - option_price
        else:
            return bs_put(S, K, T, r, sigma) - option_price

    try:
        # IV typically ranges from 0.01 to 3.0 (1% to 300%)
        iv = brentq(objective, 0.001, 3.0, xtol=1e-4)
        return iv
    except (ValueError, RuntimeError):
        # If brentq fails, return estimated IV
        return 0.15

def extract_atm_volatility(atm, ce_map, pe_map, atm_strike, days_to_expiry=1, risk_free_rate=0.06):
    """
    Extract implied volatility from ATM options.
    Uses average of call and put IV for robustness.
    """
    # Convert days to years
    T = max(days_to_expiry / 365.0, 0.001)

    # Get ATM option prices
    ce_atm_price = float(ce_map.get(atm_strike, 0)) or 0
    pe_atm_price = float(pe_map.get(atm_strike, 0)) or 0

    if ce_atm_price <= 0 and pe_atm_price <= 0:
        return 0.20  # Default to 20% if no ATM data

    atm_iv = 0
    count = 0

    # Calculate IV from ATM call
    if ce_atm_price > 0:
        ce_iv = calculate_implied_volatility(ce_atm_price, atm_strike, atm_strike, T, risk_free_rate, is_call=True)
        atm_iv += ce_iv
        count += 1

    # Calculate IV from ATM put
    if pe_atm_price > 0:
        pe_iv = calculate_implied_volatility(pe_atm_price, atm_strike, atm_strike, T, risk_free_rate, is_call=False)
        atm_iv += pe_iv
        count += 1

    return atm_iv / count if count > 0 else 0.20

def predict_extreme_prices(atm, extreme_strike, ce_map, pe_map, atm_strike, days_to_expiry=1, risk_free_rate=0.06):
    """
    Use Black-Scholes to predict CE and PE prices at extreme strikes based on current IV.

    Returns: (predicted_ce_price, predicted_pe_price)
    """
    # Extract current IV from ATM
    sigma = extract_atm_volatility(atm, ce_map, pe_map, atm_strike, days_to_expiry, risk_free_rate)

    # Convert days to years
    T = max(days_to_expiry / 365.0, 0.001)

    # Predict call and put prices at extreme strike
    ce_price = bs_call(atm, extreme_strike, T, risk_free_rate, sigma)
    pe_price = bs_put(atm, extreme_strike, T, risk_free_rate, sigma)

    return ce_price, pe_price, sigma

# FETCH OTM LTPs
# ─────────────────────────────────────────────
def fetch_otm_ltps(token, symbol, expiry, atm, step, chain_data):
    ce_map = {}; pe_map = {}
    for row in chain_data:
        strike  = float(row.get("strike_price", 0))
        call_md = (row.get("call_options") or {}).get("market_data") or {}
        pe_md   = (row.get("put_options")  or {}).get("market_data") or {}
        ce_map[strike] = float(call_md.get("ltp") or 0)
        pe_map[strike] = float(pe_md.get("ltp")   or 0)
    res = {"ce_atm": ce_map.get(float(atm), 0.0), "pe_atm": pe_map.get(float(atm), 0.0)}
    for i in range(1, 5):
        res[f"ce_{i}"] = ce_map.get(float(atm + i * step), 0.0)
        res[f"pe_{i}"] = pe_map.get(float(atm - i * step), 0.0)
    return res

# ─────────────────────────────────────────────
# FETCH chain / expiries
# ─────────────────────────────────────────────
def fetch_expiry_dates(token, symbol):
    try:
        r = requests.get(UPSTOX_CONTRACT_URL,
                         params={"instrument_key": INSTRUMENT_KEY[symbol]},
                         headers=upstox_headers(token), timeout=15)
        d = r.json()
        if r.status_code == 401:
            return None, "token_expired"
        if d.get("status") == "success" and d.get("data"):
            raw = d["data"]
            if raw and isinstance(raw[0], dict):
                dates = [str(item.get("expiry") or item.get("expiry_date") or
                             item.get("date") or item.get("expiryDate") or "") for item in raw]
                dates = [x for x in dates if x]
            else:
                dates = [str(x) for x in raw]
            dates = sorted(set(dates))
            return (dates, None) if dates else (None, "Empty expiry list")
        return None, f"Expiry fetch failed: {d}"
    except Exception as e:
        return None, str(e)

def fetch_chain(token, symbol, expiry_date):
    cache_key = f"oc_{symbol}_{expiry_date}"; time_key = f"oc_time_{symbol}_{expiry_date}"
    now = time.time()
    if (cache_key in st.session_state and time_key in st.session_state
            and now - st.session_state[time_key] < 180):
        return st.session_state[cache_key], None, "cached"
    last_err = "No response"; last_raw = {}
    for url in UPSTOX_OC_URLS:
        try:
            r = requests.get(url,
                             params={"instrument_key": INSTRUMENT_KEY[symbol], "expiry_date": expiry_date},
                             headers=upstox_headers(token), timeout=15)
            last_raw = r.json()
            if r.status_code == 401:
                return None, "token_expired", url
            if last_raw.get("status") == "success":
                data = last_raw.get("data") or []
                if data:
                    st.session_state[cache_key] = data
                    st.session_state[time_key]  = now
                    return data, None, url
                last_err = f"Empty data from {url}"
            else:
                last_err = str(last_raw)
        except Exception as e:
            last_err = str(e)
    st.session_state[f"raw_{symbol}"] = last_raw
    return None, last_err, UPSTOX_OC_URLS[-1]

# ─────────────────────────────────────────────
# PARSE
# ─────────────────────────────────────────────
def snap(price, step):
    return int(round(price / step) * step)

def _get_oi_chg(md):
    """Try every known Upstox field name for intraday OI change."""
    for key in ("oi_day_change", "change_oi", "day_change_oi", "oi_change", "oiChange", "changeOi"):
        v = md.get(key)
        if v is not None:
            try:
                return float(v)
            except Exception:
                pass
    return 0.0

def parse(data, symbol):
    step = STRIKE_STEP_FIXED.get(symbol) or infer_strike_step(data)
    ce_map = {}; pe_map = {}; ce_oi = {}; pe_oi = {}
    ce_oi_chg = {}; pe_oi_chg = {}
    spot = None

    for row in data:
        strike = float(row.get("strike_price", 0))
        if spot is None:
            sp = row.get("underlying_spot_price")
            if sp: spot = float(sp)

        call_md = (row.get("call_options") or {}).get("market_data") or {}
        ce_map[strike]    = float(call_md.get("ltp") or 0)
        ce_oi[strike]     = float(call_md.get("oi")  or 0)
        ce_oi_chg[strike] = _get_oi_chg(call_md)

        put_md  = (row.get("put_options") or {}).get("market_data") or {}
        pe_map[strike]    = float(put_md.get("ltp") or 0)
        pe_oi[strike]     = float(put_md.get("oi")  or 0)
        pe_oi_chg[strike] = _get_oi_chg(put_md)

    if spot is None:
        common = set(ce_map) & set(pe_map)
        if common:
            spot = float(min(common, key=lambda s: abs(ce_map[s] - pe_map[s])))
    if spot is None:
        raise ValueError("Could not determine underlying spot price")

    atm = snap(spot, step)

    ce_rows = [
        {"label": "ATM",   "strike": atm,            "price": ce_map.get(float(atm),            0.0)},
        {"label": "ATM+1", "strike": atm + step,     "price": ce_map.get(float(atm + step),     0.0)},
        {"label": "ATM+2", "strike": atm + 2 * step, "price": ce_map.get(float(atm + 2 * step), 0.0)},
    ]
    pe_rows = [
        {"label": "ATM",   "strike": atm,            "price": pe_map.get(float(atm),            0.0)},
        {"label": "ATM-1", "strike": atm - step,     "price": pe_map.get(float(atm - step),     0.0)},
        {"label": "ATM-2", "strike": atm - 2 * step, "price": pe_map.get(float(atm - 2 * step), 0.0)},
    ]
    ce_sum  = sum(r["price"] for r in ce_rows)
    pe_sum  = sum(r["price"] for r in pe_rows)
    ce_sqrt = math.sqrt(ce_sum) if ce_sum > 0 else 0.0
    pe_sqrt = math.sqrt(pe_sum) if pe_sum > 0 else 0.0

    # ── PCR based on total OI  (ATM ±10 strikes) ──────────────────────────
    pcr_strikes = [atm + (i * step) for i in range(-10, 11)]
    total_ce_oi = sum(ce_oi.get(float(s), 0.0) for s in pcr_strikes)
    total_pe_oi = sum(pe_oi.get(float(s), 0.0) for s in pcr_strikes)
    pcr = (total_pe_oi / total_ce_oi) if total_ce_oi > 0 else 0.0

    # ── PCR based on OI Change (only positive additions; ATM ±10 strikes) ─
    # Positive OI change = fresh writing / new open interest added today
    total_ce_oi_chg = sum(max(ce_oi_chg.get(float(s), 0.0), 0.0) for s in pcr_strikes)
    total_pe_oi_chg = sum(max(pe_oi_chg.get(float(s), 0.0), 0.0) for s in pcr_strikes)
    pcr_oi_chg = (total_pe_oi_chg / total_ce_oi_chg) if total_ce_oi_chg > 0 else 0.0

    # ── SPCL VAL Calculation (from PineScript) ─────────────────────────────
    # base_spcl = (sqrt(CE_LTP + PE_LTP) * π) / 2
    # spcl_val = (base_spcl + (base_spcl - vix_sqrt)) / 2
    spcl_val = None
    ce_atm = ce_map.get(float(atm), 0.0)
    pe_atm = pe_map.get(float(atm), 0.0)
    if ce_atm > 0 and pe_atm > 0:
        base_spcl = (math.sqrt(ce_atm + pe_atm) * math.pi) / 2
        # SPCL VAL calculation will be completed in compute_rrs_analysis with VIX data
        # For now store base_spcl for later use
        spcl_val = base_spcl  # Will be recalculated with VIX in next function

    # ── ATM OI Changes (for display) ────────────────────────────────────────
    atm_ce_oi_chg_pct = ce_oi_chg.get(float(atm), 0.0)
    atm_pe_oi_chg_pct = pe_oi_chg.get(float(atm), 0.0)

    return dict(
        spot=spot, atm=atm, step=step,
        ce_map=ce_map, pe_map=pe_map,
        ce_oi=ce_oi, pe_oi=pe_oi,
        ce_oi_chg=ce_oi_chg, pe_oi_chg=pe_oi_chg,
        ce_rows=ce_rows, pe_rows=pe_rows,
        ce_sum=ce_sum, pe_sum=pe_sum,
        ce_sqrt=ce_sqrt, pe_sqrt=pe_sqrt,
        bearish=ce_sqrt > pe_sqrt,
        pcr=pcr,
        total_pe_oi=total_pe_oi, total_ce_oi=total_ce_oi,
        pcr_oi_chg=pcr_oi_chg,
        total_pe_oi_chg=total_pe_oi_chg, total_ce_oi_chg=total_ce_oi_chg,
        atm_ce_oi_chg_pct=atm_ce_oi_chg_pct,
        atm_pe_oi_chg_pct=atm_pe_oi_chg_pct,
        spcl_val=spcl_val, ce_atm=ce_atm, pe_atm=pe_atm,
    )

# ─────────────────────────────────────────────
# TRADING DAYS
# ─────────────────────────────────────────────
def calc_trading_days_to_expiry(expiry_str):
    try:
        now_ist = datetime.now(IST).date()
        p = expiry_str.split("-")
        if len(p) == 3:
            exp_date = datetime(int(p[0]), int(p[1]), int(p[2])).date()
        else:
            return 1
        diff_days    = max((exp_date - now_ist).days, 0)
        trading_days = max(round(diff_days * 5 / 7) + 1, 1)
        return trading_days
    except Exception:
        return 1

# ─────────────────────────────────────────────
# COMPUTE RRS
# ─────────────────────────────────────────────
def compute_rrs_analysis(result, otm_ltps, expiry, vix_info, now_ist, prev_state, symbol):
    spot   = result["spot"]
    atm    = result["atm"]
    step   = result["step"]
    ce_atm = otm_ltps["ce_atm"]
    pe_atm = otm_ltps["pe_atm"]

    ce1 = otm_ltps["ce_1"]; ce2 = otm_ltps["ce_2"]
    ce3 = otm_ltps["ce_3"]; ce4 = otm_ltps["ce_4"]
    pe1 = otm_ltps["pe_1"]; pe2 = otm_ltps["pe_2"]
    pe3 = otm_ltps["pe_3"]; pe4 = otm_ltps["pe_4"]

    ce1_open = prev_state.get("ce1_open") or ce1 or 0.001
    ce2_open = prev_state.get("ce2_open") or ce2 or 0.001
    ce3_open = prev_state.get("ce3_open") or ce3 or 0.001
    ce4_open = prev_state.get("ce4_open") or ce4 or 0.001
    pe1_open = prev_state.get("pe1_open") or pe1 or 0.001
    pe2_open = prev_state.get("pe2_open") or pe2 or 0.001
    pe3_open = prev_state.get("pe3_open") or pe3 or 0.001
    pe4_open = prev_state.get("pe4_open") or pe4 or 0.001

    def ero(now_val, open_val):
        return (open_val - now_val) / open_val if open_val else 0.0

    ce1e = ero(ce1, ce1_open); ce2e = ero(ce2, ce2_open)
    ce3e = ero(ce3, ce3_open); ce4e = ero(ce4, ce4_open)
    pe1e = ero(pe1, pe1_open); pe2e = ero(pe2, pe2_open)
    pe3e = ero(pe3, pe3_open); pe4e = ero(pe4, pe4_open)

    call_erosion = (ce1e + ce2e + ce3e + ce4e) / 4
    put_erosion  = (pe1e + pe2e + pe3e + pe4e) / 4
    dominance    = put_erosion - call_erosion

    call_ema = ema_update(prev_state.get("call_ema"), call_erosion, TREND_EMA_LEN)
    put_ema  = ema_update(prev_state.get("put_ema"),  put_erosion,  TREND_EMA_LEN)
    ema_momentum = put_ema - call_ema

    warmup_bars  = prev_state.get("warmup_bars", 0) + 1
    raw_momentum = put_erosion - call_erosion
    if warmup_bars < 6:
        raw_weight    = max(0.0, (6 - warmup_bars) / 6.0) * 0.8
        momentum_diff = raw_weight * raw_momentum + (1.0 - raw_weight) * ema_momentum
    else:
        momentum_diff = ema_momentum

    call_ema_fast = ema_update(prev_state.get("call_ema_fast"), call_erosion, 3)
    put_ema_fast  = ema_update(prev_state.get("put_ema_fast"),  put_erosion,  3)
    call_ema_slow = ema_update(prev_state.get("call_ema_slow"), call_erosion, 8)
    put_ema_slow  = ema_update(prev_state.get("put_ema_slow"),  put_erosion,  8)
    fast_mom = put_ema_fast - call_ema_fast
    slow_mom = put_ema_slow - call_ema_slow

    dom_history = list(prev_state.get("dom_history", []))
    dom_history.append(dominance)
    if len(dom_history) > 20:
        dom_history = dom_history[-20:]
    dom_mean = sum(dom_history) / len(dom_history)
    dom_var  = (sum((v - dom_mean) ** 2 for v in dom_history) / len(dom_history)
                if len(dom_history) > 1 else 0.0)
    volatility = max(math.sqrt(dom_var) if dom_var > 0 else DOMINANCE_THRESHOLD,
                     DOMINANCE_THRESHOLD)

    dom_abs = abs(dominance)
    dom_avg = ema_update(prev_state.get("dom_avg"), dom_abs, 20)
    dom_avg = max(dom_avg, DOMINANCE_THRESHOLD) if dom_avg else DOMINANCE_THRESHOLD

    strong_move = abs(momentum_diff) > volatility * STRONG_MOVE_COEFF

    prev_dom1 = prev_state.get("prev_dom1", dominance)
    prev_dom2 = prev_state.get("prev_dom2", dominance)
    prev_vol1 = prev_state.get("prev_vol1", volatility)
    prev_vol2 = prev_state.get("prev_vol2", volatility)

    dominance_accel = dominance - prev_dom1
    dom_velocity2   = prev_dom1 - prev_dom2

    bull_count = prev_state.get("bull_count", 0)
    bear_count = prev_state.get("bear_count", 0)
    if   momentum_diff > 0: bull_count += 1; bear_count  = 0
    elif momentum_diff < 0: bear_count += 1; bull_count  = 0
    else:                   bull_count  = 0; bear_count  = 0

    dom_rising_count  = prev_state.get("dom_rising_count",  0)
    dom_falling_count = prev_state.get("dom_falling_count", 0)
    if   dominance > prev_dom1: dom_rising_count  += 1; dom_falling_count  = 0
    elif dominance < prev_dom1: dom_falling_count += 1; dom_rising_count   = 0
    else:                       dom_rising_count   = 0; dom_falling_count  = 0

    dom_conf_up   = dom_rising_count  >= DOM_CONF_BARS
    dom_conf_down = dom_falling_count >= DOM_CONF_BARS

    dom_pending_bull = bull_count >= TREND_CONF_BARS and not dom_conf_up
    dom_pending_bear = bear_count >= TREND_CONF_BARS and not dom_conf_down

    confirmed_trend = prev_state.get("confirmed_trend", "neutral")
    prev_trend_sign = prev_state.get("prev_trend_sign", 0.0)
    if   bull_count >= TREND_CONF_BARS and dom_conf_up:
        confirmed_trend = "bull"; prev_trend_sign = 1.0
    elif bear_count >= TREND_CONF_BARS and dom_conf_down:
        confirmed_trend = "bear"; prev_trend_sign = -1.0

    rev_count = prev_state.get("rev_count", 0)
    cur_sign  = 1.0 if momentum_diff > 0 else (-1.0 if momentum_diff < 0 else 0.0)
    if prev_trend_sign != 0 and cur_sign != 0 and cur_sign != prev_trend_sign:
        rev_count += 1
    elif cur_sign == prev_trend_sign:
        rev_count = 0
    early_reversal = rev_count >= REV_CONF_BARS

    sideways = (abs(momentum_diff) < volatility * 0.3 and
                dom_abs < dom_avg * 0.4 and
                bull_count < TREND_CONF_BARS and
                bear_count < TREND_CONF_BARS)

    prev_sideways     = prev_state.get("prev_sideways", False)
    compression_break = prev_sideways and abs(dominance_accel) > dom_avg * 0.3 and strong_move

    if dom_pending_bull:
        core_trend = "⬆⏳ PENDING BULL"
    elif dom_pending_bear:
        core_trend = "⬇⏳ PENDING BEAR"
    elif sideways:
        core_trend = "💥 BREAK OUT" if compression_break else "➖⚖️ SIDEWAYS"
    elif confirmed_trend == "bull":
        if strong_move:
            core_trend = "⬆⬆ OTM BULL+🔥⚡" if early_reversal else "⬆⬆ OTM BULL🔥"
        else:
            core_trend = "⬆ OTM BULL⚡" if early_reversal else "⬆ OTM BULL"
    elif confirmed_trend == "bear":
        if strong_move:
            core_trend = "⬇⬇ OTM BEAR+🔥⚡" if early_reversal else "⬇⬇ OTM BEAR🔥"
        else:
            core_trend = "⬇ OTM BEAR⚡" if early_reversal else "⬇ OTM BEAR"
    else:
        core_trend = "➖ NEUTRAL"

    gamma_build = (volatility > prev_vol1 and
                   momentum_diff * dominance > 0 and
                   dominance_accel * dominance > 0 and
                   abs(dominance_accel) > abs(dom_velocity2) * 0.5)
    gamma_explode = gamma_build and strong_move and volatility > prev_vol2
    if (gamma_explode and
            ((dominance > 0 and confirmed_trend == "bull") or
             (dominance < 0 and confirmed_trend == "bear"))):
        gamma_signal = "🟢 GAMMA↑" if dominance > 0 else "🔴 GAMMA↓"
    else:
        gamma_signal = ""

    raw_writer_cap = (abs(dominance_accel) > dom_avg * 0.8 and
                      dominance_accel * dominance < 0 and
                      abs(raw_momentum) > DOMINANCE_THRESHOLD * 1.5)

    writer_cap = (raw_writer_cap or
                  (strong_move and
                   dominance_accel * dominance < 0 and
                   abs(dominance_accel) > dom_avg * 0.5))
    if writer_cap:
        writer_signal = "💣 PUT WRITER" if dominance > 0 else "💣 CALL WRITER"
    else:
        writer_signal = ""

    prev_iv_peak   = prev_state.get("prev_iv_peak", False)
    iv_peak        = volatility > prev_vol1 and prev_vol1 > prev_vol2
    iv_compression = volatility < prev_vol1 and abs(momentum_diff) < dom_avg * 0.3
    iv_crush       = prev_iv_peak and iv_compression
    iv_signal      = "📉 IV CRUSH" if iv_crush else ""

    exp_parts = expiry.split("-"); is_expiry_day = False
    try:
        now_date = datetime.now(IST).date()
        exp_date = datetime(int(exp_parts[0]), int(exp_parts[1]), int(exp_parts[2])).date()
        is_expiry_day = now_date == exp_date
    except Exception:
        pass
    expiry_vol_spike = is_expiry_day and volatility > prev_vol1
    expiry_trap      = is_expiry_day and dom_abs > dom_avg * 0.6 and momentum_diff * dominance < 0
    expiry_signal    = ("🧨 EXP TRAP" if expiry_trap else
                        "⚡ EXP VOL"  if expiry_vol_spike else "")

    score = sum([
        1.0 if gamma_build       else 0.0,
        1.0 if writer_cap        else 0.0,
        1.0 if iv_crush          else 0.0,
        1.0 if strong_move       else 0.0,
        1.0 if early_reversal    else 0.0,
        1.0 if compression_break else 0.0,
    ])
    smart_prob = round((score / 6.0) * 100)
    if smart_prob > 70 and confirmed_trend != "neutral":
        smart_bias = "🧠 SMART BULL" if confirmed_trend == "bull" else "🧠 SMART BEAR"
    elif smart_prob > 40:
        smart_bias = "🧠 BUILDING"
    else:
        smart_bias = ""

    vol_rising_count = prev_state.get("vol_rising_count", 0)
    vol_rising_count = vol_rising_count + 1 if volatility > prev_vol1 else 0
    vol_rising       = vol_rising_count >= PRE_GAMMA_VOL_BARS

    dom_velocity_pg      = dominance - prev_dom1
    prev_dom_velocity_pg = prev_state.get("prev_dom_velocity_pg", dom_velocity_pg)
    dom_accel_pg         = dom_velocity_pg - prev_dom_velocity_pg
    dom_build_up = (dom_velocity_pg != 0 and
                    math.copysign(1, dom_velocity_pg) == math.copysign(1, dom_accel_pg) and
                    abs(dom_velocity_pg) > abs(prev_dom_velocity_pg))

    ce_expand_count = sum(1 for e in [ce1e, ce2e, ce3e, ce4e] if e < 0)
    pe_expand_count = sum(1 for e in [pe1e, pe2e, pe3e, pe4e] if e < 0)
    premium_expansion = (
        (ce_expand_count >= 2 and pe_expand_count >= 2) or
        (momentum_diff > 0 and pe_expand_count >= 2 and ce_expand_count < 2) or
        (momentum_diff < 0 and ce_expand_count >= 2 and pe_expand_count < 2)
    )

    approaching_threshold = dom_abs > dom_avg * 0.5 and dom_abs < dom_avg * 0.9

    ema_divergence = (fast_mom != 0 and
                      abs(fast_mom) > abs(slow_mom) and
                      math.copysign(1, fast_mom) == math.copysign(1, slow_mom))

    pre_gamma_score = sum([
        1 if vol_rising            else 0,
        1 if dom_build_up          else 0,
        1 if premium_expansion     else 0,
        1 if approaching_threshold else 0,
        1 if ema_divergence        else 0,
    ])
    pre_gamma_dir    = "bull" if fast_mom > 0 else "bear"
    pre_gamma_signal = ""
    if pre_gamma_score >= PRE_GAMMA_MIN_SCORE and not gamma_explode and not sideways:
        pre_gamma_signal = "⚡ PRE-GAMMA ↑" if pre_gamma_dir == "bull" else "⚡ PRE-GAMMA ↓"

    trend_arrow = (expiry_signal    or
                   gamma_signal     or
                   pre_gamma_signal or
                   writer_signal    or
                   iv_signal        or
                   smart_bias       or
                   core_trend)

    thr       = DOMINANCE_THRESHOLD
    rss_bull  = dominance >  thr
    rss_bear  = dominance < -thr
    inst_bull = any(x in trend_arrow for x in ["⬆", "BULL", "PUT WRITER", "GAMMA↑", "PRE-GAMMA ↑"])
    inst_bear = any(x in trend_arrow for x in ["⬇", "BEAR", "CALL WRITER", "IV CRUSH", "GAMMA↓", "PRE-GAMMA ↓", "EXP TRAP"])
    otm_bull  = momentum_diff > 0
    otm_bear  = momentum_diff < 0

    strong_bull = rss_bull and otm_bull and inst_bull
    strong_bear = rss_bear and otm_bear and inst_bear

    if   strong_bull:           spike_signal = "⬆⬆ CE STRONG 🔥" if otm_bull else "⬆ BULL CONFIRM 🔥"; sig_color = "bull"
    elif strong_bear:           spike_signal = "⬇⬇ PE STRONG 🔥" if otm_bear else "⬇ BEAR CONFIRM 🔥"; sig_color = "bear"
    elif rss_bull and otm_bull: spike_signal = "⬆⬆ RSS+OTM BULL" if strong_move else "⬆ RSS+OTM BULL"; sig_color = "bull"
    elif rss_bear and otm_bear: spike_signal = "⬇⬇ RSS+OTM BEAR" if strong_move else "⬇ RSS+OTM BEAR"; sig_color = "bear"
    elif rss_bull and otm_bear: spike_signal = "⚡ CONFLICT ↑RSS↓OTM"; sig_color = "conf"
    elif rss_bear and otm_bull: spike_signal = "⚡ CONFLICT ↓RSS↑OTM"; sig_color = "conf"
    elif rss_bull:              spike_signal = "⬆ RSS BULL"; sig_color = "bull"
    elif rss_bear:              spike_signal = "⬇ RSS BEAR"; sig_color = "bear"
    elif otm_bull:              spike_signal = "⬆⬆ OTM BULL🔥" if strong_move else "⬆ OTM BULL"; sig_color = "bull"
    elif otm_bear:              spike_signal = "⬇⬇ OTM BEAR🔥" if strong_move else "⬇ OTM BEAR"; sig_color = "bear"
    elif sideways:              spike_signal = "💥 BREAK OUT" if compression_break else "➖ SIDEWAYS / WAIT"; sig_color = "neut"
    else:                       spike_signal = "◆ NEUTRAL / WAIT"; sig_color = "neut"

    vix_current  = (vix_info or {}).get("ltp")      or 15.0
    vix_day_open = (vix_info or {}).get("day_open") or vix_current
    vix_sqrt     = math.sqrt(vix_day_open) if vix_day_open else None
    spcl_val     = None
    if ce_atm and pe_atm and vix_sqrt:
        base_spcl = (math.sqrt(ce_atm + pe_atm) * 3.14) / 2
        spcl_val  = (base_spcl + (base_spcl - vix_sqrt)) / 2

    trading_days_left = calc_trading_days_to_expiry(expiry)
    per_day_vix  = (vix_current / math.sqrt(365)) * math.sqrt(trading_days_left) if vix_current else None
    vix_per_day  = vix_current / trading_days_left if (vix_current and trading_days_left) else None
    exp_move_pts = (spot * per_day_vix / 100.0) if per_day_vix else None
    em_steps     = max(round(exp_move_pts / step), 1) if exp_move_pts else None
    em_upper_strike = atm + em_steps * step if em_steps else None
    em_lower_strike = atm - em_steps * step if em_steps else None
    upper_level  = spot + exp_move_pts if exp_move_pts else None
    lower_level  = spot - exp_move_pts if exp_move_pts else None

    ce_intrinsic      = max(spot - atm, 0)
    pe_intrinsic      = max(float(atm) - spot, 0)
    ce_tv             = max(ce_atm - ce_intrinsic, 0) if ce_atm else None
    pe_tv             = max(pe_atm - pe_intrinsic, 0) if pe_atm else None
    ce_iv_pct_display = (ce_intrinsic / ce_atm * 100) if ce_atm else 0.0
    pe_iv_pct_display = (pe_intrinsic / pe_atm * 100) if pe_atm else 0.0

    dist_from_atm = abs(spot - atm)
    gamma_score   = 100.0 / (1.0 + (dist_from_atm / step))
    vix_boost     = vix_current / 15.0
    buffer        = step * 0.25
    ce_bias = 1.2 if spot > atm + buffer else (0.8 if spot < atm - buffer else 1.0)
    pe_bias = 1.2 if spot < atm - buffer else (0.8 if spot > atm + buffer else 1.0)
    ce_iv_g = max((ce_atm - max(spot - atm, 0)) / ce_atm * 100, 0) if ce_atm > 0 else 0.0
    pe_iv_g = max((pe_atm - max(float(atm) - spot, 0)) / pe_atm * 100, 0) if pe_atm > 0 else 0.0
    ce_spike_score = gamma_score * (1.0 + ce_iv_g / 100.0) * vix_boost * ce_bias
    pe_spike_score = gamma_score * (1.0 + pe_iv_g / 100.0) * vix_boost * pe_bias
    score_diff     = ce_spike_score - pe_spike_score

    prev_avg_ce    = prev_state.get("avg_ce_erosion", call_erosion)
    prev_avg_pe    = prev_state.get("avg_pe_erosion", put_erosion)
    avg_ce_erosion = (call_erosion + prev_avg_ce) / 2
    avg_pe_erosion = (put_erosion  + prev_avg_pe) / 2
    total_ero      = avg_ce_erosion + avg_pe_erosion
    ce_edge_pct    = (avg_ce_erosion / total_ero * 100) if total_ero > 0 else 50.0
    pe_edge_pct    = (avg_pe_erosion / total_ero * 100) if total_ero > 0 else 50.0
    decay_velocity  = dominance_accel
    btst_conviction = abs(ce_edge_pct - pe_edge_pct)

    max_ce_ero = max(ce1e, ce2e, ce3e, ce4e)
    max_pe_ero = max(pe1e, pe2e, pe3e, pe4e)
    max_ce_str = atm + ([ce1e, ce2e, ce3e, ce4e].index(max_ce_ero) + 1) * step
    max_pe_str = atm - ([pe1e, pe2e, pe3e, pe4e].index(max_pe_ero) + 1) * step

    btst_bear = dominance < -thr and max_ce_ero > max_pe_ero and decay_velocity < 0
    btst_bull = dominance >  thr and max_pe_ero > max_ce_ero and decay_velocity > 0

    h = now_ist.hour; mn = now_ist.minute
    after_1515 = h > 15 or (h == 15 and mn >= 15)

    if not after_1515:
        btst_signal = "⏳ Wait for 15:15"; btst_color = "gray"; btst_target = "—"
    elif btst_bear and btst_conviction > 15:
        btst_signal = "⬇ BTST SHORT"; btst_color = "bear"
        btst_target = f"Max decay: CE {max_ce_str} ({max_ce_ero*100:.1f}%)"
    elif btst_bull and btst_conviction > 15:
        btst_signal = "⬆ BTST LONG"; btst_color = "bull"
        btst_target = f"Max decay: PE {max_pe_str} ({max_pe_ero*100:.1f}%)"
    elif dominance < -thr:
        btst_signal = "⬇ WEAK SHORT"; btst_color = "bear"
        btst_target = f"CE {max_ce_str} eroding {max_ce_ero*100:.1f}%"
    elif dominance > thr:
        btst_signal = "⬆ WEAK LONG"; btst_color = "bull"
        btst_target = f"PE {max_pe_str} eroding {max_pe_ero*100:.1f}%"
    else:
        btst_signal = "◆ NO EDGE"; btst_color = "neut"; btst_target = "Decay balanced — skip BTST"

    if   expiry_signal:    signal_source = "Expiry"
    elif gamma_signal:     signal_source = "Gamma"
    elif pre_gamma_signal: signal_source = "PreGamma"
    elif writer_signal:    signal_source = "Writer Cap"
    elif iv_signal:        signal_source = "IV Crush"
    elif smart_bias:       signal_source = "Smart"
    else:                  signal_source = "Core"

    new_state = dict(
        ce1_open=ce1_open, ce2_open=ce2_open, ce3_open=ce3_open, ce4_open=ce4_open,
        pe1_open=pe1_open, pe2_open=pe2_open, pe3_open=pe3_open, pe4_open=pe4_open,
        warmup_bars=warmup_bars,
        call_ema=call_ema, put_ema=put_ema,
        call_ema_fast=call_ema_fast, put_ema_fast=put_ema_fast,
        call_ema_slow=call_ema_slow, put_ema_slow=put_ema_slow,
        dom_avg=dom_avg, dom_history=dom_history,
        bull_count=bull_count, bear_count=bear_count,
        dom_rising_count=dom_rising_count, dom_falling_count=dom_falling_count,
        vol_rising_count=vol_rising_count,
        confirmed_trend=confirmed_trend, prev_trend_sign=prev_trend_sign,
        rev_count=rev_count,
        prev_dom1=dominance, prev_dom2=prev_dom1,
        prev_vol1=volatility, prev_vol2=prev_vol1,
        prev_sideways=sideways, prev_iv_peak=iv_peak,
        prev_dom_velocity_pg=dom_velocity_pg,
        avg_ce_erosion=avg_ce_erosion, avg_pe_erosion=avg_pe_erosion,
    )

    return dict(
        spot=spot, atm=atm, step=step,
        ce_atm=ce_atm, pe_atm=pe_atm,
        vix_current=vix_current, vix_day_open=vix_day_open,
        trading_days_left=trading_days_left,
        per_day_vix=per_day_vix, vix_per_day=vix_per_day,
        exp_move_pts=exp_move_pts, exp_move_pct=per_day_vix,
        upper_level=upper_level, lower_level=lower_level,
        em_upper_strike=em_upper_strike, em_lower_strike=em_lower_strike,
        ce_intrinsic=ce_intrinsic, pe_intrinsic=pe_intrinsic,
        ce_tv=ce_tv, pe_tv=pe_tv,
        ce_iv_pct=ce_iv_pct_display, pe_iv_pct=pe_iv_pct_display,
        spcl_val=spcl_val,
        dist_from_atm=dist_from_atm, gamma_score=gamma_score,
        vix_boost=vix_boost, ce_spike_score=ce_spike_score, pe_spike_score=pe_spike_score,
        score_diff=score_diff,
        spike_signal=spike_signal, sig_color=sig_color,
        trend_arrow=trend_arrow, signal_source=signal_source,
        warmup_bars=warmup_bars,
        core_trend=core_trend,
        writer_signal=writer_signal, pre_gamma_signal=pre_gamma_signal, gamma_signal=gamma_signal,
        confirmed_trend=confirmed_trend,
        dom_pending_bull=dom_pending_bull, dom_pending_bear=dom_pending_bear,
        smart_prob=smart_prob, smart_bias=smart_bias,
        dominance=dominance, momentum_diff=momentum_diff,
        strong_move=strong_move, sideways=sideways, dom_avg=dom_avg,
        btst_signal=btst_signal, btst_color=btst_color, btst_target=btst_target,
        ce_edge_pct=ce_edge_pct, pe_edge_pct=pe_edge_pct, decay_velocity=decay_velocity,
        is_expiry_day=is_expiry_day,
        new_state=new_state,
    )

# ─────────────────────────────────────────────
# RENDER HELPERS
# ─────────────────────────────────────────────
def _na(v, fmt="{:.2f}", fallback="N/A"):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return fallback
    return fmt.format(v)

def _pcr_badge(val, label, show_range_note=False, history=None):
    """
    Render a single PCR badge with trend history.
    Thresholds: > 1.0 = BULLISH, < 1.0 = BEARISH, == 1.0 = NEUTRAL
    """
    if val > 1.0:
        cls, tag, text = "pcr-bull-c", "pcr-tag-bull", "BULLISH"
    elif val < 1.0:
        cls, tag, text = "pcr-bear-c", "pcr-tag-bear", "BEARISH"
    else:
        cls, tag, text = "pcr-neut-c", "pcr-tag-neut", "NEUTRAL"

    note = ("<span class='pcr-label' style='margin-left:4px;font-size:9px;'>"
            "CE:ATM→+10 | PE:ATM→-10</span>") if show_range_note else ""

    # Add trend history tooltip if available
    trend_html = ""
    if history and len(history) > 0:
        trend_text = " → ".join(str(v) for v in history)
        # Determine trend direction (↑ if rising, ↓ if falling)
        trend_arrow = "↑" if history[-1] > history[0] else "↓" if history[-1] < history[0] else "→"
        trend_color = "#00e676" if history[-1] > history[0] else "#ff5252" if history[-1] < history[0] else "#999"

        trend_html = (f"<span class='pcr-trend' style='margin-left:6px;font-size:9px;color:{trend_color};' "
                     f"title='Last 6 PCR values: {trend_text}'>"
                     f"{trend_arrow} {trend_text}"
                     f"</span>")

    return (f"<div class='pcr-wrap'>"
            f"<span class='pcr-label'>{label}</span>"
            f"<span class='pcr-val {cls}'>{val:.2f}</span>"
            f"<span class='pcr-tag {tag}'>{text}</span>"
            f"{trend_html}"
            f"{note}"
            f"</div>")

def _spcl_badge(val, label, bullish=None):
    """
    Render SPCL VAL badge (Special Value from PineScript).
    SPCL VAL = (sqrt(CE_LTP + PE_LTP) * π / 2) adjusted for VIX
    Color: Green if bullish (Bu), Dark Orange if bearish (Be)
    """
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return f"<div class='spcl-wrap'><span class='spcl-label'>{label}</span><span class='spcl-val-display'>N/A</span></div>"

    # Determine color based on bias
    color_class = "spcl-bull" if bullish else "spcl-bear"

    return (f"<div class='spcl-wrap'>"
            f"<span class='spcl-label'>{label}</span>"
            f"<span class='spcl-val-display {color_class}'>{val:.2f}</span>"
            f"</div>")

def _valid_strikes_summary(atm, spcl_val=None, ce_map=None, pe_map=None, step=None):
    """
    Display the BEST OTM CE and PE strikes where LTP (premium) <= SPCL VAL.
    CE: Next 20 OTM strikes above ATM - show strike with highest LTP <= SPCL VAL
    PE: 20 OTM strikes below ATM - show strike with highest LTP <= SPCL VAL
    Shows the single best strike with most premium within affordable range.
    """
    if atm is None or spcl_val is None or math.isnan(spcl_val):
        return ""

    # If we don't have the complete chain data, return empty
    if (not ce_map or len(ce_map) == 0) and (not pe_map or len(pe_map) == 0):
        return ""

    # Find BEST CE strike in OTM range with LTP <= SPCL VAL (highest LTP)
    # CE: next 20 strikes ABOVE ATM
    best_ce = None
    best_ce_ltp = -1
    if ce_map:
        ce_candidates = []
        for strike, ltp in ce_map.items():
            strike_float = float(strike)
            ltp_float = float(ltp) if ltp else 0
            # Get all CE strikes above ATM with valid LTP
            if strike_float > atm and ltp_float > 0 and ltp_float <= spcl_val:
                ce_candidates.append((strike_float, ltp_float))
        # Sort by strike price ascending, take first 20, then find one with highest LTP
        ce_candidates.sort(key=lambda x: x[0])
        for strike, ltp in ce_candidates[:20]:
            if ltp > best_ce_ltp:
                best_ce = strike
                best_ce_ltp = ltp

    # Find BEST PE strike in OTM range with LTP <= SPCL VAL (highest LTP)
    # PE: last 20 strikes BELOW ATM (closest to ATM going down)
    best_pe = None
    best_pe_ltp = -1
    if pe_map:
        pe_candidates = []
        for strike, ltp in pe_map.items():
            strike_float = float(strike)
            ltp_float = float(ltp) if ltp else 0
            # Get all PE strikes below ATM with valid LTP
            if strike_float < atm and ltp_float > 0 and ltp_float <= spcl_val:
                pe_candidates.append((strike_float, ltp_float))
        # Sort by strike price descending (closest to ATM first), take first 20, then find one with highest LTP
        pe_candidates.sort(key=lambda x: x[0], reverse=True)
        for strike, ltp in pe_candidates[:20]:
            if ltp > best_pe_ltp:
                best_pe = strike
                best_pe_ltp = ltp

    # Create display for best strikes
    html = f"<div class='valid-strikes-wrap'>"
    html += f"<span class='valid-strikes-label'>Best OTM Strike (LTP ≤ SPCL VAL: {spcl_val:.2f})</span>"

    if best_ce is not None and best_ce_ltp > 0:
        html += f"<div class='valid-strikes-side valid-strikes-ce'>CE: <span class='valid-strike-item'>{int(best_ce)}({best_ce_ltp:.2f})</span></div>"
    else:
        html += f"<div class='valid-strikes-side valid-strikes-ce' style='color:#999;'>CE: None with LTP ≤ {spcl_val:.2f}</div>"

    if best_pe is not None and best_pe_ltp > 0:
        html += f"<div class='valid-strikes-side valid-strikes-pe'>PE: <span class='valid-strike-item'>{int(best_pe)}({best_pe_ltp:.2f})</span></div>"
    else:
        html += f"<div class='valid-strikes-side valid-strikes-pe' style='color:#999;'>PE: None with LTP ≤ {spcl_val:.2f}</div>"

    html += f"</div>"

    return html

def _strikes_display(atm, spcl_val=None):
    """
    Display CE and PE side strikes next to SPCL VAL.
    Highlights strikes that are <= SPCL VAL.

    CE Strikes: ATM+400, ATM+600, ATM+1400
    PE Strikes: ATM-400, ATM-600, ATM-1400
    """
    # CE side positions
    ce_400 = atm + 400
    ce_600 = atm + 600
    ce_1400 = atm + 1400

    # PE side positions
    pe_400 = atm - 400
    pe_600 = atm - 600
    pe_1400 = atm - 1400

    # Helper function to format strike with highlighting
    def format_strike_item(strike, spcl_val):
        if spcl_val is not None and not math.isnan(spcl_val) and strike <= spcl_val:
            return f"<span class='strike-item strike-valid'><span class='strike-val'>{strike}</span></span>"
        return f"<span class='strike-item'><span class='strike-val'>{strike}</span></span>"

    ce_400_fmt = format_strike_item(ce_400, spcl_val)
    ce_600_fmt = format_strike_item(ce_600, spcl_val)
    ce_1400_fmt = format_strike_item(ce_1400, spcl_val)
    pe_400_fmt = format_strike_item(pe_400, spcl_val)
    pe_600_fmt = format_strike_item(pe_600, spcl_val)
    pe_1400_fmt = format_strike_item(pe_1400, spcl_val)

    strikes_html = (f"<div class='strikes-display-wrap'>"
                    f"<span class='strikes-label'>Strikes</span>"
                    f"<span class='strikes-side strikes-ce'>CE: {ce_400_fmt} {ce_600_fmt} {ce_1400_fmt}</span>"
                    f"<span style='color:var(--border2);'>│</span>"
                    f"<span class='strikes-side strikes-pe'>PE: {pe_400_fmt} {pe_600_fmt} {pe_1400_fmt}</span>"
                    f"</div>")
    return strikes_html

def _calculate_qty_adjustment(atm, ce_map, pe_map, opening_ce_prices=None, opening_pe_prices=None):
    """
    Calculate which side (CE/PE) has more loss potential and adjust far leg (1400) quantities.
    Ensures max intraday loss stays < 1.8% of capital deployed.

    Position Structure (Iron Condor):
    - CE: ATM+400(B)[1] | ATM+600(S)[3] | ATM+1400(B)[2]  → Max loss at 24200 (short strike)
    - PE: ATM-400(B)[1] | ATM-600(S)[3] | ATM-1400(B)[2]  → Max loss at 23000 (short strike)

    Returns dict with adjusted quantities:
    {'ce_1400_qty': adjusted_qty, 'pe_1400_qty': adjusted_qty, 'loss_pct': loss_percentage}
    """
    # Base quantities for each leg
    base_qties = {'400': 1, '600': 3, '1400': 2}

    # Get LTPs for all legs (use opening prices if provided, else use current LTPs)
    ce_ltps = {}
    pe_ltps = {}

    for offset in ['400', '600', '1400']:
        ce_strike = atm + int(offset)
        pe_strike = atm - int(offset)

        # CE: Use provided bought price if available, else Wednesday opening from ce_map
        if opening_ce_prices and ce_strike in opening_ce_prices:
            ce_ltps[offset] = float(opening_ce_prices[ce_strike]) if opening_ce_prices[ce_strike] else 0
        else:
            # Default to Wednesday opening prices from ce_map
            ce_ltps[offset] = float(ce_map.get(ce_strike, ce_map.get(str(ce_strike), 0)) or 0) if ce_map else 0

        # PE: Use provided bought price if available, else Wednesday opening from pe_map
        if opening_pe_prices and pe_strike in opening_pe_prices:
            pe_ltps[offset] = float(opening_pe_prices[pe_strike]) if opening_pe_prices[pe_strike] else 0
        else:
            # Default to Wednesday opening prices from pe_map
            pe_ltps[offset] = float(pe_map.get(pe_strike, pe_map.get(str(pe_strike), 0)) or 0) if pe_map else 0

    # Calculate loss potential for imbalance detection
    ce_loss = sum((atm + int(offset) - atm) * qty * 0.5 for offset, qty in base_qties.items())
    pe_loss = sum((atm - (atm - int(offset))) * qty * 0.5 for offset, qty in base_qties.items())

    # Calculate max loss at SHORT strikes (where max loss occurs in iron condor)
    # CE: Long 400 & 1400, Short 600 → Max loss = (600 - 400) × 100 per lot
    # PE: Long 400 & 1400, Short 600 → Max loss = (600 - 400) × 100 per lot
    ce_short_strike = atm + 600
    pe_short_strike = atm - 600

    max_loss_per_ce_lot = (600 - 400) * 100  # 20,000 per lot at short strike
    max_loss_per_pe_lot = (600 - 400) * 100  # 20,000 per lot at short strike

    # Calculate capital deployed (net premium: long premiums - short premiums)
    ce_capital = (ce_ltps['400'] * base_qties['400'] + ce_ltps['1400'] * base_qties['1400']) - (ce_ltps['600'] * base_qties['600'])
    pe_capital = (pe_ltps['400'] * base_qties['400'] + pe_ltps['1400'] * base_qties['1400']) - (pe_ltps['600'] * base_qties['600'])
    total_capital = ce_capital + pe_capital

    # Calculate current max loss and loss percentage
    current_max_loss_ce = max_loss_per_ce_lot * base_qties['600']
    current_max_loss_pe = max_loss_per_pe_lot * base_qties['600']
    current_total_max_loss = current_max_loss_ce + current_max_loss_pe
    current_loss_pct = (current_total_max_loss / total_capital * 100) if total_capital > 0 else 0

    # Determine which side has more loss and adjust far leg (1400) quantity
    adjusted_qties = {'ce_1400_qty': 2, 'pe_1400_qty': 2, 'loss_pct': current_loss_pct}

    # Only increase quantities if loss stays < 1.8%
    if current_loss_pct < 1.8:
        if ce_loss > pe_loss and pe_loss > 0:
            # CE side has MORE loss potential, increase ce_1400 quantity
            imbalance_ratio = ce_loss / pe_loss
            adjustment = max(1.0, min(2.5, imbalance_ratio * 0.3))
            new_ce_qty = max(2, int(2 + adjustment * 2))

            # Check if new quantity still keeps loss < 1.8%
            new_max_loss = current_max_loss_ce + (max_loss_per_ce_lot * (new_ce_qty - base_qties['1400'])) + current_max_loss_pe
            new_loss_pct = (new_max_loss / total_capital * 100) if total_capital > 0 else 0

            if new_loss_pct < 1.8:
                adjusted_qties['ce_1400_qty'] = new_ce_qty
                adjusted_qties['loss_pct'] = new_loss_pct

        elif pe_loss > ce_loss and ce_loss > 0:
            # PE side has MORE loss potential, increase pe_1400 quantity
            imbalance_ratio = pe_loss / ce_loss
            adjustment = max(1.0, min(2.5, imbalance_ratio * 0.3))
            new_pe_qty = max(2, int(2 + adjustment * 2))

            # Check if new quantity still keeps loss < 1.8%
            new_max_loss = current_max_loss_ce + current_max_loss_pe + (max_loss_per_pe_lot * (new_pe_qty - base_qties['1400']))
            new_loss_pct = (new_max_loss / total_capital * 100) if total_capital > 0 else 0

            if new_loss_pct < 1.8:
                adjusted_qties['pe_1400_qty'] = new_pe_qty
                adjusted_qties['loss_pct'] = new_loss_pct

    return adjusted_qties

def _payoff_chart(atm, ce_map, pe_map, ce_1400_qty=2, pe_1400_qty=2, opening_ce_prices=None, opening_pe_prices=None, days_to_expiry=1, symbol='NIFTY'):
    """
    Generate SVG payoff/P&L chart showing profit/loss across strike range.

    Shows iron condor payoff curve from ATM-1400 to ATM+1400 with:
    - Red area for losses
    - Green area for profits
    - Proper scaling and axis labels
    - Loss amounts at sold strikes (ATM±600)

    Uses trade setup quantities (1, 3, adjusted_qty) directly.

    Parameters:
    -----------
    opening_ce_prices : dict, optional
        CE strike actual bought/entry prices. If provided, uses these for P&L calcs instead of Wednesday opens.
        Format: {24000: {'price': 67.5, 'is_short': False}}

    opening_pe_prices : dict, optional
        PE strike actual bought/entry prices. If provided, uses these for P&L calcs instead of Wednesday opens.
        Format: {23600: {'price': 85.0, 'is_short': False}}

    If bought prices not provided, uses Wednesday opening prices from ce_map/pe_map (default).
    """
    # Get LTPs for all legs (use opening prices if provided, else use current LTPs)
    ce_ltps = {}
    pe_ltps = {}
    base_qties = {'400': 1, '600': 3, '1400': 2}

    for offset in ['400', '600', '1400']:
        ce_strike = atm + int(offset)
        pe_strike = atm - int(offset)

        # CE: Use provided bought price if available, else Wednesday opening from ce_map
        if opening_ce_prices and ce_strike in opening_ce_prices:
            ce_ltps[offset] = float(opening_ce_prices[ce_strike]) if opening_ce_prices[ce_strike] else 0
        else:
            # Default to Wednesday opening prices from ce_map
            ce_ltps[offset] = float(ce_map.get(ce_strike, ce_map.get(str(ce_strike), 0)) or 0) if ce_map else 0

        # PE: Use provided bought price if available, else Wednesday opening from pe_map
        if opening_pe_prices and pe_strike in opening_pe_prices:
            pe_ltps[offset] = float(opening_pe_prices[pe_strike]) if opening_pe_prices[pe_strike] else 0
        else:
            # Default to Wednesday opening prices from pe_map
            pe_ltps[offset] = float(pe_map.get(pe_strike, pe_map.get(str(pe_strike), 0)) or 0) if pe_map else 0

    # Calculate net premium (debit if positive, credit if negative)
    ce_debit = ce_ltps['400'] * base_qties['400'] + ce_ltps['1400'] * base_qties['1400']
    ce_credit = ce_ltps['600'] * base_qties['600']
    ce_net = ce_debit - ce_credit

    pe_debit = pe_ltps['400'] * base_qties['400'] + pe_ltps['1400'] * base_qties['1400']
    pe_credit = pe_ltps['600'] * base_qties['600']
    pe_net = pe_debit - pe_credit

    total_net_premium = ce_net + pe_net

    # Calculate payoff at different strikes using Black-Scholes for more realistic pricing
    payoff_points = []
    strike_range = range(atm - 1400, atm + 1401, 100)

    # Extract IV for BS calculations
    atm_iv = extract_atm_volatility(atm, ce_map, pe_map, atm, days_to_expiry) if days_to_expiry > 0 else 0.20
    T = max(days_to_expiry / 365.0, 0.001)
    r = 0.06

    for s in strike_range:
        # For points far from ATM, use BS predictions; near ATM use intrinsic value
        # This gives a more realistic payoff curve accounting for time value decay

        ce_400_strike = atm + 400
        ce_600_strike = atm + 600
        ce_1400_strike = atm + 1400

        pe_400_strike = atm - 400
        pe_600_strike = atm - 600
        pe_1400_strike = atm - 1400

        # CE side P&L (use BS for more realistic pricing)
        ce_400_payoff = 0
        ce_600_payoff = 0
        ce_1400_payoff = 0

        try:
            # Predict CE prices at strike s using BS
            ce_price_at_s, _, _ = predict_extreme_prices(atm, s, ce_map, pe_map, atm, days_to_expiry)

            # CE 400 leg (LONG) - use trade setup qty
            ce_400_entry = opening_ce_prices.get(ce_400_strike, {}).get('price', ce_ltps.get('400', 0)) if opening_ce_prices else ce_ltps.get('400', 0)
            ce_400_qty = base_qties['400']
            if ce_price_at_s > 0 and ce_400_entry > 0:
                ce_400_payoff = (ce_price_at_s - ce_400_entry) * ce_400_qty
            else:
                ce_400_payoff = max(0, s - ce_400_strike) * ce_400_qty if s > ce_400_strike else 0

            # CE 600 leg (SHORT) - use trade setup qty
            ce_600_entry = opening_ce_prices.get(ce_600_strike, {}).get('price', ce_ltps.get('600', 0)) if opening_ce_prices else ce_ltps.get('600', 0)
            ce_600_qty = base_qties['600']
            if ce_price_at_s > 0 and ce_600_entry > 0:
                ce_600_payoff = -(ce_600_entry - ce_price_at_s) * ce_600_qty
            else:
                ce_600_payoff = -max(0, s - ce_600_strike) * ce_600_qty if s > ce_600_strike else 0

            # CE 1400 leg (LONG) - use trade setup qty
            ce_1400_entry = opening_ce_prices.get(ce_1400_strike, {}).get('price', 0) if opening_ce_prices else 0
            ce_1400_qty_actual = ce_1400_qty
            if ce_price_at_s > 0 and ce_1400_entry > 0:
                ce_1400_payoff = (ce_price_at_s - ce_1400_entry) * ce_1400_qty_actual
            else:
                ce_1400_payoff = max(0, s - ce_1400_strike) * ce_1400_qty_actual if s > ce_1400_strike else 0
        except:
            # Fallback to intrinsic value calculation
            ce_400_payoff = max(0, s - ce_400_strike) * base_qties['400'] * 100 if s > ce_400_strike else 0
            ce_600_payoff = -max(0, s - ce_600_strike) * base_qties['600'] * 100 if s > ce_600_strike else 0
            ce_1400_payoff = max(0, s - ce_1400_strike) * ce_1400_qty * 100 if s > ce_1400_strike else 0

        # PE side P&L (use BS for more realistic pricing)
        pe_400_payoff = 0
        pe_600_payoff = 0
        pe_1400_payoff = 0

        try:
            # Predict PE prices at strike s using BS
            _, pe_price_at_s, _ = predict_extreme_prices(atm, s, ce_map, pe_map, atm, days_to_expiry)

            # PE 400 leg (LONG) - use trade setup qty
            pe_400_entry = opening_pe_prices.get(pe_400_strike, {}).get('price', pe_ltps.get('400', 0)) if opening_pe_prices else pe_ltps.get('400', 0)
            pe_400_qty = base_qties['400']
            if pe_price_at_s > 0 and pe_400_entry > 0:
                pe_400_payoff = (pe_price_at_s - pe_400_entry) * pe_400_qty
            else:
                pe_400_payoff = max(0, pe_400_strike - s) * pe_400_qty if s < pe_400_strike else 0

            # PE 600 leg (SHORT) - use trade setup qty
            pe_600_entry = opening_pe_prices.get(pe_600_strike, {}).get('price', pe_ltps.get('600', 0)) if opening_pe_prices else pe_ltps.get('600', 0)
            pe_600_qty = base_qties['600']
            if pe_price_at_s > 0 and pe_600_entry > 0:
                pe_600_payoff = -(pe_600_entry - pe_price_at_s) * pe_600_qty
            else:
                pe_600_payoff = -max(0, pe_600_strike - s) * pe_600_qty if s < pe_600_strike else 0

            # PE 1400 leg (LONG) - use trade setup qty
            pe_1400_entry = opening_pe_prices.get(pe_1400_strike, {}).get('price', 0) if opening_pe_prices else 0
            pe_1400_qty_actual = pe_1400_qty
            if pe_price_at_s > 0 and pe_1400_entry > 0:
                pe_1400_payoff = (pe_price_at_s - pe_1400_entry) * pe_1400_qty_actual
            else:
                pe_1400_payoff = max(0, pe_1400_strike - s) * pe_1400_qty_actual if s < pe_1400_strike else 0
        except:
            # Fallback to intrinsic value calculation
            pe_400_payoff = max(0, pe_400_strike - s) * base_qties['400'] * 100 if s < pe_400_strike else 0
            pe_600_payoff = -max(0, pe_600_strike - s) * base_qties['600'] * 100 if s < pe_600_strike else 0
            pe_1400_payoff = max(0, pe_1400_strike - s) * pe_1400_qty * 100 if s < pe_1400_strike else 0

        total_payoff = (ce_400_payoff + ce_600_payoff + ce_1400_payoff +
                       pe_400_payoff + pe_600_payoff + pe_1400_payoff -
                       total_net_premium)

        payoff_points.append((s, total_payoff))

    # Find max profit and max loss for scaling
    pnls = [p[1] for p in payoff_points]
    max_profit = max(pnls) if pnls else 0
    min_loss = min(pnls) if pnls else 0
    y_max = max(abs(max_profit), abs(min_loss))
    y_max = max(y_max, 100000)  # Min scale

    # SVG dimensions
    width, height = 280, 100
    margin = 25
    plot_width = width - 2 * margin
    plot_height = height - 2 * margin

    # Scale factors
    x_scale = plot_width / (max(strike_range) - min(strike_range))
    y_scale = plot_height / (2 * y_max)

    # Start SVG
    svg = f'<svg width="{width}" height="{height}" style="background:#0a0a0a; border:1px solid #333; border-radius:3px;">'

    # Draw zero line (break-even)
    zero_y = margin + plot_height / 2
    svg += f'<line x1="{margin}" y1="{zero_y}" x2="{width-margin}" y2="{zero_y}" stroke="#444" stroke-width="1" stroke-dasharray="2,2"/>'

    # Mark key strike levels
    # Short strikes (ATM±600) - where max loss occurs
    ce_short = atm + 600
    pe_short = atm - 600

    # Long extreme legs (ATM±1400)
    ce_extreme = atm + 1400
    pe_extreme = atm - 1400

    # Calculate losses at sold strikes based on current LTP
    def calc_payoff_at_strike(strike, ce_ltps, pe_ltps, base_qties, ce_1400_qty, pe_1400_qty, total_net_premium, atm):
        """Calculate payoff at a specific strike"""
        ce_400_payoff = max(0, strike - (atm + 400)) * base_qties['400'] * 100 if strike > atm + 400 else 0
        ce_600_payoff = -max(0, strike - (atm + 600)) * base_qties['600'] * 100 if strike > atm + 600 else 0
        ce_1400_payoff = max(0, strike - (atm + 1400)) * ce_1400_qty * 100 if strike > atm + 1400 else 0

        pe_400_payoff = max(0, (atm - 400) - strike) * base_qties['400'] * 100 if strike < atm - 400 else 0
        pe_600_payoff = -max(0, (atm - 600) - strike) * base_qties['600'] * 100 if strike < atm - 600 else 0
        pe_1400_payoff = max(0, (atm - 1400) - strike) * pe_1400_qty * 100 if strike < atm - 1400 else 0

        total = (ce_400_payoff + ce_600_payoff + ce_1400_payoff +
                pe_400_payoff + pe_600_payoff + pe_1400_payoff -
                total_net_premium)
        return total

    ce_short_loss = calc_payoff_at_strike(ce_short, ce_ltps, pe_ltps, base_qties, ce_1400_qty, pe_1400_qty, total_net_premium, atm)
    pe_short_loss = calc_payoff_at_strike(pe_short, ce_ltps, pe_ltps, base_qties, ce_1400_qty, pe_1400_qty, total_net_premium, atm)

    # Draw vertical lines for key strikes with labels and loss amounts
    for strike, label, color, style, loss_val in [
        (pe_extreme, "PE:1400", "#FF9999", "dotted", None),
        (pe_short, "PE:600(S)", "#FF6B6B", "solid", pe_short_loss),
        (ce_short, "CE:600(S)", "#4CAF50", "solid", ce_short_loss),
        (ce_extreme, "CE:1400", "#99FF99", "dotted", None)
    ]:
        x = margin + (strike - min(strike_range)) * x_scale
        if margin <= x <= width - margin:
            svg += f'<line x1="{x}" y1="{margin}" x2="{x}" y2="{margin+plot_height}" stroke="{color}" stroke-width="0.8" opacity="0.4" stroke-dasharray="{("3,3" if style == "dotted" else "0")}"/>'
            # Add label at top
            label_y = margin - 8
            svg += f'<text x="{x}" y="{label_y}" font-size="7" fill="{color}" text-anchor="middle" opacity="0.6">{label}</text>'

            # Add loss amount for sold legs
            if loss_val is not None:
                loss_color = "#FF6B6B" if loss_val < 0 else "#00e676"
                loss_label = f"₹{int(loss_val):,}" if loss_val != 0 else "0"
                loss_y = zero_y + 10
                svg += f'<text x="{x}" y="{loss_y}" font-size="7" fill="{loss_color}" text-anchor="middle" font-weight="bold">{loss_label}</text>'

    # Find and mark breakeven points
    breakevens = []
    for i in range(len(payoff_points) - 1):
        pnl1 = payoff_points[i][1]
        pnl2 = payoff_points[i + 1][1]
        if pnl1 * pnl2 < 0:  # Sign change = breakeven crossed
            breakevens.append((payoff_points[i][0] + payoff_points[i + 1][0]) / 2)

    for be_strike in breakevens:
        x = margin + (be_strike - min(strike_range)) * x_scale
        if margin <= x <= width - margin:
            svg += f'<circle cx="{x}" cy="{zero_y}" r="2" fill="#FFA500" opacity="0.7"/>'

    # Draw payoff curve and fill areas
    points_str = ""
    for i, (strike, pnl) in enumerate(payoff_points):
        x = margin + (strike - min(strike_range)) * x_scale
        y = zero_y - (pnl * y_scale)
        points_str += f"{x},{y} "

    # Create polygon for loss area (red) - below zero
    loss_path = f"M {margin},{zero_y} "
    for strike, pnl in payoff_points:
        if pnl < 0:
            x = margin + (strike - min(strike_range)) * x_scale
            y = zero_y - (pnl * y_scale)
            loss_path += f"L {x},{y} "
    loss_path += f"L {margin + plot_width},{zero_y} Z"
    svg += f'<path d="{loss_path}" fill="#FF6B6B" opacity="0.3"/>'

    # Create polygon for profit area (green) - above zero
    profit_path = f"M {margin},{zero_y} "
    for strike, pnl in payoff_points:
        if pnl > 0:
            x = margin + (strike - min(strike_range)) * x_scale
            y = zero_y - (pnl * y_scale)
            profit_path += f"L {x},{y} "
    profit_path += f"L {margin + plot_width},{zero_y} Z"
    svg += f'<path d="{profit_path}" fill="#00e676" opacity="0.3"/>'

    # Draw payoff curve line
    svg += f'<polyline points="{points_str}" fill="none" stroke="#00e676" stroke-width="1.5" opacity="0.8"/>'

    # Draw axis labels (simplified)
    svg += f'<text x="{margin + plot_width/2}" y="{height-5}" font-size="9" fill="#666" text-anchor="middle">ATM-1400 → ATM+1400</text>'
    svg += f'<text x="5" y="{zero_y-5}" font-size="8" fill="#666">P</text>'
    svg += f'<text x="5" y="{zero_y+10}" font-size="8" fill="#666">L</text>'

    # Draw max values
    max_loss_str = f"₹{int(min_loss):,}" if min_loss < 0 else "0"
    max_profit_str = f"₹{int(max_profit):,}" if max_profit > 0 else "0"
    svg += f'<text x="{margin+2}" y="{margin-5}" font-size="8" fill="#00e676">{max_profit_str}</text>'
    svg += f'<text x="{margin+2}" y="{height-margin+10}" font-size="8" fill="#FF6B6B">{max_loss_str}</text>'

    svg += '</svg>'
    return svg

def _current_pnl_display(atm, ce_map, pe_map, ce_1400_qty=2, pe_1400_qty=2, opening_ce_prices=None, opening_pe_prices=None, symbol='NIFTY', days_to_expiry=1):
    """
    Display current running P&L at center (spot) and probable losses at extreme ends.

    P&L Formula (simple):
    - For LONG: P&L = (LTP - Entry) × Qty
    - For SHORT: P&L = (Entry - LTP) × Qty

    Quantities from trade setup (1, 3, adjusted_qty) already account for lot size.

    Shows:
    - Current P&L at spot (intraday)
    - Probable loss at CE extreme (highest CE strike)
    - Probable loss at PE extreme (lowest PE strike)
    """
    if not opening_ce_prices or not opening_pe_prices:
        return ""  # No entry prices provided, skip display

    # Define trade setup strikes and quantities
    ce_400 = atm + 400
    ce_600 = atm + 600
    ce_1400 = atm + 1400

    pe_400 = atm - 400
    pe_600 = atm - 600
    pe_1400 = atm - 1400

    # Map strikes to quantities
    ce_qty_map = {ce_400: 1, ce_600: 3, ce_1400: ce_1400_qty}
    pe_qty_map = {pe_400: 1, pe_600: 3, pe_1400: pe_1400_qty}

    # Get current LTPs from ce_map/pe_map
    current_pnl = 0
    ce_pnl_list = []
    pe_pnl_list = []

    # Calculate P&L for CE positions
    for ce_strike, ce_data in opening_ce_prices.items():
        entry_price = ce_data['price']
        is_short = ce_data['is_short']

        # Get quantity from trade setup (1, 3, or adjusted 1400 qty)
        qty = ce_qty_map.get(ce_strike, 1)

        # Get current LTP
        current_ltp = float(ce_map.get(ce_strike, ce_map.get(str(ce_strike), 0)) or 0) if ce_map else entry_price

        # Calculate P&L using trade setup quantities
        if is_short:
            position_pnl = (entry_price - current_ltp) * qty
        else:
            position_pnl = (current_ltp - entry_price) * qty

        current_pnl += position_pnl
        ce_pnl_list.append((ce_strike, position_pnl))

    # Calculate P&L for PE positions
    for pe_strike, pe_data in opening_pe_prices.items():
        entry_price = pe_data['price']
        is_short = pe_data['is_short']

        # Get quantity from trade setup (1, 3, or adjusted 1400 qty)
        qty = pe_qty_map.get(pe_strike, 1)

        # Get current LTP
        current_ltp = float(pe_map.get(pe_strike, pe_map.get(str(pe_strike), 0)) or 0) if pe_map else entry_price

        # Calculate P&L using trade setup quantities
        if is_short:
            position_pnl = (entry_price - current_ltp) * qty
        else:
            position_pnl = (current_ltp - entry_price) * qty

        current_pnl += position_pnl
        pe_pnl_list.append((pe_strike, position_pnl))

    # Calculate extreme losses using Black-Scholes predictions for ATM±1400 strikes
    ce_extreme_loss = 0
    pe_extreme_loss = 0

    # CE Extreme (ATM+1400) - use BS prediction if available
    ce_extreme_strike = ce_1400
    if ce_extreme_strike in opening_ce_prices:
        entry_price = opening_ce_prices[ce_extreme_strike]['price']
        is_short = opening_ce_prices[ce_extreme_strike]['is_short']
        qty = ce_qty_map.get(ce_extreme_strike, 1)

        # Predict CE price at extreme strike using Black-Scholes
        try:
            predicted_ce_price, _, _ = predict_extreme_prices(atm, ce_extreme_strike, ce_map, pe_map, atm, days_to_expiry)
            if is_short:
                ce_extreme_loss = (entry_price - predicted_ce_price) * qty
            else:
                ce_extreme_loss = (predicted_ce_price - entry_price) * qty
        except:
            # Fallback to minimum from list if BS fails
            ce_losses = [p[1] for p in ce_pnl_list if p[0] == ce_extreme_strike]
            ce_extreme_loss = min(ce_losses) if ce_losses else 0

    # PE Extreme (ATM-1400) - use BS prediction if available
    pe_extreme_strike = pe_1400
    if pe_extreme_strike in opening_pe_prices:
        entry_price = opening_pe_prices[pe_extreme_strike]['price']
        is_short = opening_pe_prices[pe_extreme_strike]['is_short']
        qty = pe_qty_map.get(pe_extreme_strike, 1)

        # Predict PE price at extreme strike using Black-Scholes
        try:
            _, predicted_pe_price, _ = predict_extreme_prices(atm, pe_extreme_strike, ce_map, pe_map, atm, days_to_expiry)
            if is_short:
                pe_extreme_loss = (entry_price - predicted_pe_price) * qty
            else:
                pe_extreme_loss = (predicted_pe_price - entry_price) * qty
        except:
            # Fallback to minimum from list if BS fails
            pe_losses = [p[1] for p in pe_pnl_list if p[0] == pe_extreme_strike]
            pe_extreme_loss = min(pe_losses) if pe_losses else 0

    # Calculate total entry capital for percentage calculation
    total_entry_capital = 0
    for strike, data in opening_ce_prices.items():
        qty = ce_qty_map.get(strike, 1)
        total_entry_capital += data['price'] * qty
    for strike, data in opening_pe_prices.items():
        qty = pe_qty_map.get(strike, 1)
        total_entry_capital += data['price'] * qty

    # Calculate percentage changes
    current_pct = (current_pnl / total_entry_capital * 100) if total_entry_capital > 0 else 0
    ce_pct = (ce_extreme_loss / total_entry_capital * 100) if total_entry_capital > 0 else 0
    pe_pct = (pe_extreme_loss / total_entry_capital * 100) if total_entry_capital > 0 else 0

    # Color coding
    current_color = "#00e676" if current_pnl >= 0 else "#FF6B6B"
    ce_color = "#FF6B6B" if ce_extreme_loss < 0 else "#00e676"
    pe_color = "#FF6B6B" if pe_extreme_loss < 0 else "#00e676"

    # Format numbers with percentage change (like PCR OI | PCR Δ OI)
    current_str = f"₹{int(current_pnl):,} | {current_pct:+.2f}%"
    ce_str = f"₹{int(ce_extreme_loss):,} | {ce_pct:+.2f}%"
    pe_str = f"₹{int(pe_extreme_loss):,} | {pe_pct:+.2f}%"

    html = (f"<div style='display:flex; gap:12px; margin-top:4px; font-size:11px;'>"
            f"<div style='flex:1; background:#1a1a1a; border-left:3px solid {current_color}; padding:6px 8px; border-radius:3px;'>"
            f"<div style='color:#888; font-size:9px;'>CENTER (Spot)</div>"
            f"<div style='color:{current_color}; font-weight:bold; font-size:11px;'>{current_str}</div>"
            f"</div>"
            f"<div style='flex:1; background:#1a1a1a; border-left:3px solid {ce_color}; padding:6px 8px; border-radius:3px;'>"
            f"<div style='color:#888; font-size:9px;'>CE EXTREME (ATM+1400)</div>"
            f"<div style='color:{ce_color}; font-weight:bold; font-size:11px;'>{ce_str}</div>"
            f"</div>"
            f"<div style='flex:1; background:#1a1a1a; border-left:3px solid {pe_color}; padding:6px 8px; border-radius:3px;'>"
            f"<div style='color:#888; font-size:9px;'>PE EXTREME (ATM-1400)</div>"
            f"<div style='color:{pe_color}; font-weight:bold; font-size:11px;'>{pe_str}</div>"
            f"</div>"
            f"</div>")

    return html

def _risk_profile_chart(atm, ce_map, pe_map, ce_1400_qty=2, pe_1400_qty=2, total_capital=1):
    """
    Render a compact loss profile chart showing max losses at extreme CE and PE strikes.

    Displays:
    - CE extreme loss at ATM+1400 strike (in rupees and % of capital)
    - PE extreme loss at ATM-1400 strike (in rupees and % of capital)
    """
    # Get LTPs for short strikes (where max loss occurs)
    ce_short_strike = atm + 600
    pe_short_strike = atm - 600

    if ce_map:
        ce_short_ltp = float(ce_map.get(ce_short_strike, ce_map.get(str(ce_short_strike), 0)) or 0)
    else:
        ce_short_ltp = 0

    if pe_map:
        pe_short_ltp = float(pe_map.get(pe_short_strike, pe_map.get(str(pe_short_strike), 0)) or 0)
    else:
        pe_short_ltp = 0

    # Max loss at extreme strikes (spread width × quantity × 100)
    # For iron condor: max loss = (extreme_strike - short_strike) × quantity × 100
    ce_extreme_strike = atm + 1400
    pe_extreme_strike = atm - 1400

    ce_max_loss = (ce_extreme_strike - ce_short_strike) * 100 * ce_1400_qty  # 80,000 × qty
    pe_max_loss = (pe_extreme_strike - pe_short_strike) * 100 * pe_1400_qty  # 80,000 × qty

    ce_loss_pct = (ce_max_loss / total_capital * 100) if total_capital > 0 else 0
    pe_loss_pct = (pe_max_loss / total_capital * 100) if total_capital > 0 else 0

    # Determine colors based on loss %
    ce_color = "#00e676" if ce_loss_pct < 1.2 else "#FFA500" if ce_loss_pct < 1.8 else "#FF6B6B"
    pe_color = "#00e676" if pe_loss_pct < 1.2 else "#FFA500" if pe_loss_pct < 1.8 else "#FF6B6B"

    # Calculate bar widths (max 60px for 100% capital loss)
    ce_bar_width = min(60, (ce_loss_pct / 5) * 60)  # Scale 0-5% to 0-60px
    pe_bar_width = min(60, (pe_loss_pct / 5) * 60)

    chart_html = (f"<div style='font-size:10px; margin-top:3px; padding:4px; background:#1a1a1a; border-radius:3px;'>"
                  f"<div style='margin-bottom:2px;'>"
                  f"<span style='color:#888;'>CE Extreme (₹{int(ce_max_loss):,}</span> "
                  f"<span style='color:{ce_color};'>{ce_loss_pct:.2f}%)</span>"
                  f"<div style='height:8px; background:#333; border-radius:2px; margin-top:1px;'>"
                  f"<div style='height:100%; width:{ce_bar_width}px; background:{ce_color}; border-radius:2px;'></div>"
                  f"</div>"
                  f"</div>"
                  f"<div>"
                  f"<span style='color:#888;'>PE Extreme (₹{int(pe_max_loss):,}</span> "
                  f"<span style='color:{pe_color};'>{pe_loss_pct:.2f}%)</span>"
                  f"<div style='height:8px; background:#333; border-radius:2px; margin-top:1px;'>"
                  f"<div style='height:100%; width:{pe_bar_width}px; background:{pe_color}; border-radius:2px;'></div>"
                  f"</div>"
                  f"</div>"
                  f"</div>")

    return chart_html

def _trade_setup_badge(atm, step, spcl_val=None, ce_1400_qty=2, pe_1400_qty=2, loss_pct=0):
    """
    Render predefined trade setup showing CE and PE side positions with Buy/Sell and quantities.
    Highlights strikes that are <= SPCL VAL.

    CE Side: ATM+400(B)[1], ATM+600(S)[3], ATM+1400(B)[adjusted]
    PE Side: ATM-400(B)[1], ATM-600(S)[3], ATM-1400(B)[adjusted]

    Quantities for far legs (1400) are adjusted based on which side has more loss potential.
    Max loss is constrained to stay < 1.8% of capital deployed (displayed as risk indicator).
    """
    # CE side positions
    ce_400 = atm + 400
    ce_600 = atm + 600
    ce_1400 = atm + 1400

    # PE side positions
    pe_400 = atm - 400
    pe_600 = atm - 600
    pe_1400 = atm - 1400

    # Helper function to format strike with highlighting for range (SPCL VAL - 5) to SPCL VAL
    def format_setup_item(strike, action, qty, spcl_val):
        strike_html = f"<span class='trade-strike'>{strike}</span>"
        if spcl_val is not None and not math.isnan(spcl_val):
            lower_bound = spcl_val - 5
            upper_bound = spcl_val
            if lower_bound <= strike <= upper_bound:
                strike_html = f"<span class='trade-strike trade-strike-valid'>{strike}</span>"

        action_class = "trade-buy" if action == "B" else "trade-sell"
        return f"{strike_html}<span class='{action_class}'>({action})</span>[{qty}]"

    ce_400_fmt = format_setup_item(ce_400, "B", 1, spcl_val)
    ce_600_fmt = format_setup_item(ce_600, "S", 3, spcl_val)
    ce_1400_fmt = format_setup_item(ce_1400, "B", ce_1400_qty, spcl_val)
    pe_400_fmt = format_setup_item(pe_400, "B", 1, spcl_val)
    pe_600_fmt = format_setup_item(pe_600, "S", 3, spcl_val)
    pe_1400_fmt = format_setup_item(pe_1400, "B", pe_1400_qty, spcl_val)

    # Determine risk color based on loss percentage
    risk_color = "#00e676" if loss_pct < 1.2 else "#FFA500" if loss_pct < 1.8 else "#FF6B6B"
    risk_label = "✓ Safe" if loss_pct < 1.2 else "⚠ Caution" if loss_pct < 1.8 else "⛔ High"

    setup_html = (f"<div class='trade-setup-wrap'>"
                  f"<span class='trade-setup-label'>Setup</span>"
                  f"<div class='trade-side trade-ce'>"
                  f"CE: {ce_400_fmt} | {ce_600_fmt} | {ce_1400_fmt}"
                  f"</div>"
                  f"<div class='trade-side trade-pe'>"
                  f"PE: {pe_400_fmt} | {pe_600_fmt} | {pe_1400_fmt}"
                  f"</div>"
                  f"<span style='font-size:11px; color:{risk_color}; margin-left:4px;'>Loss: {loss_pct:.2f}% {risk_label}</span>"
                  f"</div>")
    return setup_html

# NSE F&O Lot Sizes (as per SEBI regulations)
LOT_SIZES = {
    'NIFTY': 65,
    'BANKNIFTY': 30,
    'FINNIFTY': 60,
    'MIDCPNIFTY': 120,
    'NIFTYNXT50': 25,
    'HDFCBANK': 550,
    'ICICIBANK': 1100,
    'SBIN': 1500,
    'RELIANCE': 500,
    'HDFC': 200,
    'INFY': 600,
    'TCS': 200,
    'WIPRO': 700,
    'AXISBANK': 700,
    'LT': 250,
}

def get_lot_size(symbol):
    """Get lot size for a given symbol. Default to 100 if not found."""
    return LOT_SIZES.get(symbol.upper(), 100)

def calculate_days_to_expiry(expiry_date_str, now_ist):
    """Calculate days remaining until expiry from expiry date string (YYYY-MM-DD)."""
    try:
        expiry_dt = datetime.strptime(expiry_date_str, "%Y-%m-%d").replace(tzinfo=pytz.timezone('Asia/Kolkata'))
        # Set expiry time to market close (3:30 PM IST)
        expiry_dt = expiry_dt.replace(hour=15, minute=30, second=0)
        days = (expiry_dt - now_ist).total_seconds() / 86400.0
        return max(days, 0.01)  # Minimum 0.01 days to avoid division by zero
    except:
        return 1  # Default to 1 day if parsing fails

def parse_entry_prices(text_input):
    """
    Parse entry prices from user text input with buy/sell notation.

    Supports formats:
    - CE 24000(B): 65.5    [Bought call]
    - CE 24400(S): 45.0    [Sold call]
    - CE 24000 BUY: 65.5   [Bought call]
    - CE 24400 SELL: 45.0  [Sold call]
    - CE 24000: 65.5       [Assumed bought]
    - PE 23600: 85.0

    Quantities are automatically used from trade setup:
    - ATM±400: 1 lot
    - ATM±600: 3 lots
    - ATM±1400: adjusted based on risk balance

    Returns:
    --------
    (ce_data_dict, pe_data_dict) : tuple of dicts
        {strike: {'price': float, 'is_short': bool}, ...}
    """
    ce_data = {}
    pe_data = {}

    if not text_input or text_input.strip() == "":
        return ce_data, pe_data

    lines = text_input.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line or ':' not in line:
            continue

        try:
            # Parse different formats
            parts = line.split(':')
            if len(parts) != 2:
                continue

            label_strike = parts[0].strip()
            price = float(parts[1].strip())

            # Detect if SHORT (S) or SELL
            is_short = '(S)' in label_strike or 'SELL' in label_strike.upper()

            # Remove (B)/(S) or BUY/SELL notation
            label_strike_clean = label_strike.replace('(B)', '').replace('(S)', '').replace('BUY', '').replace('SELL', '').strip()

            # Detect CE/PE and extract strike
            if label_strike_clean.startswith('CE'):
                strike = int(label_strike_clean.replace('CE', '').strip())
                ce_data[strike] = {'price': price, 'is_short': is_short}
            elif label_strike_clean.startswith('PE'):
                strike = int(label_strike_clean.replace('PE', '').strip())
                pe_data[strike] = {'price': price, 'is_short': is_short}
            else:
                # Try to parse as just strike number
                try:
                    strike = int(label_strike_clean)
                    # Auto-detect based on value
                    if price > 50:
                        ce_data[strike] = {'price': price, 'is_short': is_short}
                    else:
                        pe_data[strike] = {'price': price, 'is_short': is_short}
                except ValueError:
                    continue

        except (ValueError, IndexError):
            continue

    return ce_data, pe_data

# ================== FIXED FUNCTION ==================
def _calculate_26_11_levels(spot, symbol):
    """
    Calculate 26.11% reversal levels based on intraday high/low.
    Uses Upstox V2 market-quote/quotes for live session OHLC.
    """
    now_ist = datetime.now(IST)
    is_market_open = now_ist.weekday() < 5 and 9 <= now_ist.hour < 16  # Mon-Fri, 9am-4pm

    tracking_key = f"tracking_26_11_{symbol}"
    yesterday_key = f"yesterday_26_11_{symbol}"

    if is_market_open:
        # ─────────────────────────────────────────────────────────────────────
        # MARKET LIVE: fetch intraday high/low every 3 minutes
        # ─────────────────────────────────────────────────────────────────────
        should_fetch = False

        if tracking_key not in st.session_state:
            should_fetch = True
        else:
            tracking = st.session_state[tracking_key]
            if tracking.get("date") != now_ist.date():
                should_fetch = True
            else:
                last_update = tracking.get("last_update")
                if last_update:
                    time_elapsed = (now_ist - last_update).total_seconds() / 60
                    if time_elapsed >= 3:
                        should_fetch = True
                else:
                    should_fetch = True

        if should_fetch:
            try:
                instrument_key = INSTRUMENT_KEY.get(symbol)
                token = st.session_state.get("access_token")   # ← FIXED token key

                if not instrument_key or not token:
                    raise ValueError("Missing instrument key or token")

                url = "https://api.upstox.com/v2/market-quote/quotes"
                params = {"instrument_key": instrument_key}
                headers = {
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}"
                }

                response = requests.get(url, params=params, headers=headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success" and data.get("data"):
                        quote = data["data"].get(instrument_key, {})
                        ohlc = quote.get("ohlc", {})
                        high = float(ohlc.get("high", spot))
                        low  = float(ohlc.get("low", spot))

                        if high < low:
                            high, low = low, high

                        # ── Store for display in debug panel ──
                        st.session_state[f"api_response_{symbol}"] = {
                            "symbol": symbol,
                            "ohlc_keys": list(ohlc.keys()),
                            "ohlc_data": ohlc,
                            "extracted_high": high,
                            "extracted_low": low,
                            "timestamp": str(now_ist),
                            "status": "SUCCESS"
                        }

                        st.session_state[tracking_key] = {
                            "high": high,
                            "low": low,
                            "date": now_ist.date(),
                            "last_update": now_ist
                        }
                    else:
                        raise ValueError(f"API success=False or no data: {data}")
                else:
                    raise ValueError(f"HTTP {response.status_code}")
            except Exception as e:
                # Fallback: keep previous or use spot
                if tracking_key not in st.session_state:
                    st.session_state[tracking_key] = {
                        "high": spot,
                        "low": spot,
                        "date": now_ist.date(),
                        "last_update": now_ist
                    }
                # Store error in debug
                st.session_state[f"api_response_{symbol}"] = {
                    "symbol": symbol,
                    "status": "ERROR",
                    "error": str(e),
                    "timestamp": str(now_ist)
                }

        tracking = st.session_state[tracking_key]
        high = tracking.get("high", spot)
        low = tracking.get("low", spot)

    else:
        # ─────────────────────────────────────────────────────────────────────
        # MARKET CLOSED: use yesterday's high/low from historical candles
        # ─────────────────────────────────────────────────────────────────────
        if yesterday_key not in st.session_state:
            try:
                yesterday = datetime.now(IST) - timedelta(days=1)
                yesterday_str = yesterday.strftime("%Y-%m-%d")
                day_before_str = (yesterday - timedelta(days=1)).strftime("%Y-%m-%d")

                instrument_key = INSTRUMENT_KEY.get(symbol)
                token = st.session_state.get("access_token")   # ← FIXED

                if instrument_key and token:
                    url = f"https://api.upstox.com/v3/historical-candle/{instrument_key}/days/1/{yesterday_str}/{day_before_str}"
                    headers = {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'Authorization': f'Bearer {token}'
                    }
                    response = requests.get(url, headers=headers, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("status") == "success" and data.get("data"):
                            candles = data["data"].get("candles", [])
                            if candles:
                                candle = candles[0]  # [timestamp, open, high, low, close, volume]
                                high = float(candle[2])  # HIGH
                                low  = float(candle[3])  # LOW
                                if high < low:
                                    high, low = low, high
                                st.session_state[yesterday_key] = {"high": high, "low": low}
                            else:
                                raise ValueError("No candles")
                        else:
                            raise ValueError("API error")
                    else:
                        raise ValueError(f"HTTP {response.status_code}")
                else:
                    raise ValueError("Missing key or token")
            except Exception as e:
                high = spot
                low = spot
                st.session_state[yesterday_key] = {"high": high, "low": low}
                st.session_state[f"api_response_{symbol}"] = {
                    "symbol": symbol,
                    "status": "ERROR (yesterday)",
                    "error": str(e),
                    "timestamp": str(now_ist)
                }
        else:
            hl = st.session_state[yesterday_key]
            high = hl["high"]
            low = hl["low"]

    # Calculate 26.11% levels
    range_val = high - low
    if range_val < 1:
        range_val = spot * 0.01  # fallback

    level_26_11_lower = low + (range_val * 0.2611)
    level_26_11_upper = high - (range_val * 0.2611)

    return {
        "lower": round(level_26_11_lower, 2),
        "upper": round(level_26_11_upper, 2),
        "high": round(high, 2),
        "low": round(low, 2),
        "is_market_open": is_market_open
    }
# ================== END FIXED FUNCTION ==================

def _update_pcr_history(symbol, pcr_value):
    """Track last 6 PCR values for trend analysis."""
    history_key = f"pcr_history_{symbol}"
    history = st.session_state.get(history_key, [])

    # Add new PCR value
    history.append(round(pcr_value, 2))

    # Keep only last 6 values
    if len(history) > 6:
        history = history[-6:]

    st.session_state[history_key] = history
    return history

def _get_pcr_history(symbol):
    """Retrieve PCR history for trend display."""
    history_key = f"pcr_history_{symbol}"
    return st.session_state.get(history_key, [])

def pcr_html(pcr, pcr_oi_chg=None, atm_ce_oi_chg=None, atm_pe_oi_chg=None, spcl_val=None, atm=None, step=None, bullish=None, ce_map=None, pe_map=None, opening_ce_prices=None, opening_pe_prices=None, symbol='NIFTY', days_to_expiry=1):
    """
    Render PCR badges with OI change information, SPCL VAL, and trade setup.
    - PCR OI   : based on total open interest (standard) with last 6 values trend
    - PCR Δ OI : based on intraday OI additions (fresh writing sentiment)
    - SPCL VAL : Special value indicator (sqrt(CE_LTP + PE_LTP) * π/2, adjusted for VIX)
               Color: Green if bullish (Bu), Dark Orange if bearish (Be)
    - Trade Setup: Predefined positions (CE/PE sides with strikes and quantities)
    - Valid Strikes: Shows strikes from complete option chain within (SPCL VAL - 5) to SPCL VAL range
    - OI Change: Shows ATM Calls/Puts SHORT/LONG status based on OI direction
    """
    # Track and get PCR history for trend analysis
    pcr_history = _update_pcr_history(symbol, pcr)

    badges = _pcr_badge(pcr, "PCR OI", show_range_note=True, history=pcr_history)

    if pcr_oi_chg is not None and pcr_oi_chg > 0:
        badges += "<span class='pcr-divider'>│</span>"
        badges += _pcr_badge(pcr_oi_chg, "PCR Δ OI")

    # Add SPCL VAL next to PCR (with bias coloring)
    if spcl_val is not None:
        badges += "<span class='pcr-divider'>│</span>"
        badges += _spcl_badge(spcl_val, "SPCL VAL", bullish=bullish)

    # Add Trade Setup next to SPCL VAL (with SPCL VAL comparison and highlights)
    risk_chart_html = ""
    if atm is not None and step is not None:
        badges += "<span class='pcr-divider'>│</span>"
        # Calculate risk-balanced quantities for far legs (capped at 1.8% max loss)
        adjusted_qties = _calculate_qty_adjustment(atm, ce_map, pe_map, opening_ce_prices, opening_pe_prices)
        badges += _trade_setup_badge(atm, step, spcl_val, adjusted_qties['ce_1400_qty'], adjusted_qties['pe_1400_qty'], adjusted_qties['loss_pct'])

        # Calculate capital for risk profile chart
        base_qties = {'400': 1, '600': 3, '1400': 2}
        ce_ltps = {}
        pe_ltps = {}
        for offset in ['400', '600', '1400']:
            ce_strike = atm + int(offset)
            pe_strike = atm - int(offset)

            # Use provided bought price if available, else Wednesday opening from ce_map/pe_map
            if opening_ce_prices and ce_strike in opening_ce_prices:
                ce_ltps[offset] = float(opening_ce_prices[ce_strike]) if opening_ce_prices[ce_strike] else 0
            else:
                ce_ltps[offset] = float(ce_map.get(ce_strike, ce_map.get(str(ce_strike), 0)) or 0) if ce_map else 0

            if opening_pe_prices and pe_strike in opening_pe_prices:
                pe_ltps[offset] = float(opening_pe_prices[pe_strike]) if opening_pe_prices[pe_strike] else 0
            else:
                pe_ltps[offset] = float(pe_map.get(pe_strike, pe_map.get(str(pe_strike), 0)) or 0) if pe_map else 0

        ce_capital = (ce_ltps['400'] * base_qties['400'] + ce_ltps['1400'] * base_qties['1400']) - (ce_ltps['600'] * base_qties['600'])
        pe_capital = (pe_ltps['400'] * base_qties['400'] + pe_ltps['1400'] * base_qties['1400']) - (pe_ltps['600'] * base_qties['600'])
        total_capital = ce_capital + pe_capital

        # Generate current P&L display (with correct lot size for symbol)
        current_pnl_html = _current_pnl_display(atm, ce_map, pe_map, adjusted_qties['ce_1400_qty'], adjusted_qties['pe_1400_qty'], opening_ce_prices, opening_pe_prices, symbol, days_to_expiry)

        # Generate payoff chart (uses opening prices if provided, with BS-predicted prices)
        payoff_chart = _payoff_chart(atm, ce_map, pe_map, adjusted_qties['ce_1400_qty'], adjusted_qties['pe_1400_qty'], opening_ce_prices, opening_pe_prices, days_to_expiry, symbol)
        risk_chart_html = current_pnl_html + payoff_chart

    html = f"<div class='pcr-row'>{badges}"

    # Add Valid Strikes summary next to Setup on the same row
    valid_strikes = _valid_strikes_summary(atm, spcl_val, ce_map, pe_map, step) if atm is not None else ""
    if valid_strikes:
        html += f"<span class='pcr-divider'>│</span>{valid_strikes}"

    html += "</div>"

    # Add risk profile chart below main row
    if risk_chart_html:
        html += f"<div style='margin-top:2px; margin-left:8px;'>{risk_chart_html}</div>"

    # Add OI Change row showing ATM Calls and Puts direction
    if atm_ce_oi_chg is not None and atm_pe_oi_chg is not None:
        ce_direction = "↑ LONG" if atm_ce_oi_chg > 0 else "↓ SHORT"
        pe_direction = "↑ LONG" if atm_pe_oi_chg > 0 else "↓ SHORT"
        ce_color = "#00e676" if atm_ce_oi_chg > 0 else "#ff5252"
        pe_color = "#00e676" if atm_pe_oi_chg > 0 else "#ff5252"

        html += f"""<div class='pcr-row' style='margin-top:5px;'>
            <div style='font-family:var(--mono);font-size:11px;color:var(--muted);'>
                ATM Calls: <span style='color:{ce_color};font-weight:600;'>{ce_direction} (OI {abs(atm_ce_oi_chg):.1f}%)</span>
                <span class='pcr-divider'>│</span>
                ATM Puts: <span style='color:{pe_color};font-weight:600;'>{pe_direction} (OI {abs(atm_pe_oi_chg):.1f}%)</span>
            </div>
        </div>"""

    return html

def oi_change_table(result, symbol, expiry):
    """
    Render OI and OI CHANGE combined table.
    Shows strikes with both base OI and OI change values.
    Top 5 strikes by OI change magnitude for each side.
    """
    if not result:
        return ""

    ce_oi = result.get("ce_oi", {})
    pe_oi = result.get("pe_oi", {})
    ce_oi_chg = result.get("ce_oi_chg", {})
    pe_oi_chg = result.get("pe_oi_chg", {})

    if not ce_oi_chg and not pe_oi_chg:
        return ""

    # Get top 5 strikes by OI change for each side
    ce_top = sorted([(s, v) for s, v in ce_oi_chg.items()], key=lambda x: abs(x[1]), reverse=True)[:5]
    pe_top = sorted([(s, v) for s, v in pe_oi_chg.items()], key=lambda x: abs(x[1]), reverse=True)[:5]

    # Don't render if all OI changes are zero
    if not ce_top and not pe_top:
        return ""
    if all(v == 0 for s, v in ce_top) and all(v == 0 for s, v in pe_top):
        return ""

    html = f"""
    <div style='margin-top:12px;'>
        <div class='sec-hdr' style='font-size:12px; margin-bottom:8px;'>📊 OI & OI CHANGE TABLE — {symbol} {expiry}</div>
        <table class='opt-table' style='font-size:10px;'>
            <thead>
                <tr style='background:#1a1a1a; border-bottom:1px solid #333;'>
                    <th style='padding:4px;text-align:center;width:40px;'>Type</th>
                    <th style='padding:4px;text-align:center;width:70px;'>Strike</th>
                    <th style='padding:4px;text-align:right;width:80px;'>OI</th>
                    <th style='padding:4px;text-align:right;width:80px;'>OI Change</th>
                    <th style='padding:4px;text-align:right;width:60px;'>%Δ</th>
                </tr>
            </thead>
            <tbody>
    """

    # CE rows
    for strike, change in ce_top:
        oi_val = ce_oi.get(strike, 0)
        change_color = "#00e676" if change > 0 else "#FF6B6B" if change < 0 else "#999"
        pct_change = (change / oi_val * 100) if oi_val > 0 else 0
        html += f"""
                <tr style='border-bottom:1px solid #222;'>
                    <td style='padding:4px;text-align:center;'><span style='background:#0a4a2e;color:#00e676;padding:2px 6px;border-radius:3px;font-size:9px;'>CE</span></td>
                    <td style='padding:4px;text-align:center;font-weight:600;'>{strike}</td>
                    <td style='padding:4px;text-align:right;color:#999;'>{oi_val:,.0f}</td>
                    <td style='padding:4px;text-align:right;color:{change_color};font-weight:600;'>{change:+,.0f}</td>
                    <td style='padding:4px;text-align:right;color:{change_color};'>{pct_change:+.1f}%</td>
                </tr>
        """

    # PE rows
    for strike, change in pe_top:
        oi_val = pe_oi.get(strike, 0)
        change_color = "#FF6B6B" if change > 0 else "#00e676" if change < 0 else "#999"
        pct_change = (change / oi_val * 100) if oi_val > 0 else 0
        html += f"""
                <tr style='border-bottom:1px solid #222;'>
                    <td style='padding:4px;text-align:center;'><span style='background:#4a0a2e;color:#FF6B6B;padding:2px 6px;border-radius:3px;font-size:9px;'>PE</span></td>
                    <td style='padding:4px;text-align:center;font-weight:600;'>{strike}</td>
                    <td style='padding:4px;text-align:right;color:#999;'>{oi_val:,.0f}</td>
                    <td style='padding:4px;text-align:right;color:{change_color};font-weight:600;'>{change:+,.0f}</td>
                    <td style='padding:4px;text-align:right;color:{change_color};'>{pct_change:+.1f}%</td>
                </tr>
        """

    html += """
            </tbody>
        </table>
    </div>
    """

    return html

def _trend_row_class(signal):
    s = signal.upper()
    if any(x in s for x in ["⬆", "BULL", "PUT WRITER", "GAMMA↑", "PRE-GAMMA ↑", "SMART BULL", "EXP VOL"]):
        return "r-trend-bull"
    if any(x in s for x in ["⬇", "BEAR", "CALL WRITER", "IV CRUSH", "GAMMA↓", "PRE-GAMMA ↓", "EXP TRAP", "SMART BEAR"]):
        return "r-trend-bear"
    if any(x in s for x in ["CONFLICT", "PENDING", "BUILDING"]):
        return "r-trend-conf"
    return "r-trend-neut"

def render_table(r, symbol, expiry, analysis=None):
    bear       = r["bearish"]
    bias_cls   = "r-bias-bear" if bear else "r-bias-bull"
    bias_arrow = "▼" if bear else "▲"
    bias_txt   = "BEARISH" if bear else "BULLISH"
    bias_detail = (f"√CE {r['ce_sqrt']:.2f} &gt; √PE {r['pe_sqrt']:.2f}"
                   if bear else
                   f"√PE {r['pe_sqrt']:.2f} &gt; √CE {r['ce_sqrt']:.2f}")

    def ce_row(x):
        return (f"<tr class='r-ce-bg'><td><span class='tag-ce'>CE</span></td>"
                f"<td class='r-ce'>{x['label']}</td>"
                f"<td class='strike-num'>{x['strike']}</td>"
                f"<td class='price-num r-ce'>{x['price']:.2f}</td></tr>")

    def pe_row(x):
        return (f"<tr class='r-pe-bg'><td><span class='tag-pe'>PE</span></td>"
                f"<td class='r-pe'>{x['label']}</td>"
                f"<td class='strike-num'>{x['strike']}</td>"
                f"<td class='price-num r-pe'>{x['price']:.2f}</td></tr>")

    ce_rows_html = "".join(ce_row(x) for x in r["ce_rows"])
    pe_rows_html = "".join(pe_row(x) for x in r["pe_rows"])

    trend_row_html = ""
    if analysis:
        ta     = analysis.get("trend_arrow", "")
        src    = analysis.get("signal_source", "")
        wb     = analysis.get("warmup_bars", 0)
        warm   = "" if wb >= 6 else f" <span style='color:#666;font-size:9px;'>⚠ warming {wb}/6</span>"
        tr_cls = _trend_row_class(ta)
        trend_row_html = (
            f"<tr class='r-trend {tr_cls}'>"
            f"<td colspan='2'>📡 TREND  <span style='font-size:9px;opacity:.6;font-weight:400;'>({src}){warm}</span></td>"
            f"<td colspan='2'>{ta}</td>"
            f"</tr>"
        )

    st.markdown(f"""
    <table class='opt-table'>
      <thead><tr>
        <th style='width:32px;'></th><th>Strike</th><th>Label</th><th>LTP</th>
      </tr></thead>
      <tbody>
        {ce_rows_html}
        <tr class='r-sum'><td colspan='3'>CE SUM</td><td>{r['ce_sum']:.2f}</td></tr>
        <tr class='r-sqrt'><td colspan='3'>√ CE</td><td>{r['ce_sqrt']:.2f}</td></tr>
        {pe_rows_html}
        <tr class='r-sum'><td colspan='3'>PE SUM</td><td>{r['pe_sum']:.2f}</td></tr>
        <tr class='r-sqrt'><td colspan='3'>√ PE</td><td>{r['pe_sqrt']:.2f}</td></tr>
        <tr class='r-bias {bias_cls}'>
          <td colspan='2'>{bias_arrow} {bias_txt}</td>
          <td colspan='2'>{bias_detail}</td>
        </tr>
        {trend_row_html}
      </tbody>
    </table>
    """, unsafe_allow_html=True)

def _sig_row_class(sig_color):
    return {"bull": "signal-bull", "bear": "signal-bear", "conf": "signal-conf"}.get(sig_color, "signal-neut")

def _btst_cls(btst_color):
    return {"bull": "btst-bull", "bear": "btst-bear"}.get(btst_color, "btst-neut")

def render_rrs_table(a, symbol, expiry):
    def row(label, v_left, v_right, lc="v-w", rc="v-gray"):
        return (f"<tr><td class='lbl'>{label}</td>"
                f"<td class='{lc}'>{v_left}</td>"
                f"<td class='{rc}'>{v_right}</td></tr>")

    def sec(title, c1="CALL", c2="PUT"):
        return (f"<tr class='sec-hdr-row'>"
                f"<td>── {title} ──</td><td>{c1}</td><td>{c2}</td></tr>")

    sig_cls  = _sig_row_class(a["sig_color"])
    btst_cls = _btst_cls(a["btst_color"])

    ta = a["trend_arrow"]
    if any(x in ta for x in ["⬆", "BULL", "PUT WRITER", "GAMMA↑", "PRE-GAMMA ↑"]):
        ta_c = "v-g"
    elif any(x in ta for x in ["⬇", "BEAR", "CALL WRITER", "IV CRUSH", "GAMMA↓", "PRE-GAMMA ↓"]):
        ta_c = "v-r"
    elif any(x in ta for x in ["PENDING", "CONFLICT", "BUILDING"]):
        ta_c = "v-y"
    else:
        ta_c = "v-gray"

    gs  = a["gamma_score"]
    gsc = "v-g" if gs > 70 else ("v-o" if gs > 40 else "v-r")
    gs_label = "High — near ATM" if gs > 70 else ("Medium" if gs > 40 else "Low — far OTM")

    thr   = DOMINANCE_THRESHOLD
    dom_c = "v-g" if a["dominance"] >  thr else ("v-r" if a["dominance"] < -thr else "v-gray")
    mom_c = "v-g" if a["momentum_diff"] > 0 else ("v-r" if a["momentum_diff"] < 0 else "v-gray")
    mom_state = "Strong" if a["strong_move"] else ("Sideways" if a["sideways"] else "Moderate")

    em_up = _na(a["em_upper_strike"], "{:.0f}")
    em_lo = _na(a["em_lower_strike"], "{:.0f}")
    emp   = _na(a["exp_move_pts"],    "{:.2f}")
    ul    = _na(a["upper_level"],     "{:.0f}")
    ll    = _na(a["lower_level"],     "{:.0f}")
    em_ce_str = f"+{emp} → {ul}" if a["exp_move_pts"] else "N/A"
    em_pe_str = f"-{emp} → {ll}" if a["exp_move_pts"] else "N/A"
    spcl  = _na(a["spcl_val"], "{:.2f}")

    ct   = a.get("confirmed_trend", "neutral")
    ct_c = "v-g" if ct == "bull" else ("v-r" if ct == "bear" else "v-gray")

    sub_signals = " · ".join(filter(None, [
        a.get("writer_signal", ""),
        a.get("pre_gamma_signal", ""),
        a.get("gamma_signal", ""),
        a.get("smart_bias", ""),
    ])) or "—"

    html = f"""
    <table class='rrs-table'><tbody>
      {sec("Option Data")}
      {row("LTP (ATM)", _na(a['ce_atm']), _na(a['pe_atm']), "v-o","v-o")}
      {row("Intrinsic Value", _na(a['ce_intrinsic']), _na(a['pe_intrinsic']), "v-g","v-g")}
      {row("Time Value", _na(a['ce_tv']), _na(a['pe_tv']), "v-aq","v-aq")}
      {row("IV % of Premium", f"{a['ce_iv_pct']:.1f}%", f"{a['pe_iv_pct']:.1f}%", "v-g","v-g")}
      {sec("VIX & Expected Move","Value","Details")}
      {row("Current VIX", _na(a['vix_current']), "India VIX", "v-o","v-gray")}
      {row("VIX Day Open", _na(a['vix_day_open']), "Day's opening VIX", "v-o","v-gray")}
      {row("Trading Days Left", str(a['trading_days_left']), f"to {expiry}", "v-y","v-gray")}
      {row("VIX Per Day", _na(a['vix_per_day']), "VIX ÷ Days Left", "v-o","v-gray")}
      {row("Expected Move %", (_na(a['exp_move_pct'])+"%" if a['exp_move_pct'] else "N/A"), "VIX/√365×√Days", "v-g","v-gray")}
      {row("Expected Move (Pts)", emp, "Price × Move%", "v-g","v-gray")}
      {row("EM Range (CE side)", em_ce_str, f"→ {em_up}", "v-g","v-gray")}
      {row("EM Range (PE side)", em_pe_str, f"→ {em_lo}", "v-r","v-gray")}
      {sec("Gamma + Spike Signal")}
      {row("Dist from ATM", _na(a['dist_from_atm']), "pts (0=max gamma)", "v-y","v-gray")}
      {row("Gamma Score", f"{a['gamma_score']:.1f}", gs_label, gsc, gsc)}
      {row("VIX Boost", f"{a['vix_boost']:.2f}x", "VIX ÷ 15", "v-o","v-gray")}
      {row("Spike Score", f"{a['ce_spike_score']:.1f}", f"{a['pe_spike_score']:.1f}", "v-ce","v-pe")}
      {row("Score Edge", f"{abs(a['score_diff']):.1f}", "Directional" if abs(a['score_diff'])>10 else "Balanced", "v-w","v-gray")}
      <tr class='{sig_cls}'>
        <td class='lbl'>SPIKE SIGNAL (4-OTM)</td>
        <td>{a['spike_signal']}</td>
        <td>{sub_signals}</td>
      </tr>
      {sec("Pine Trend (Priority Chain)","Signal","Source")}
      <tr>
        <td class='lbl'>TREND ARROW</td>
        <td class='{ta_c}' style='font-weight:800;font-size:12px;'>{ta}</td>
        <td class='v-gray' style='font-size:10px;'>{a.get("signal_source","")}</td>
      </tr>
      {row("Confirmed Trend", ct.upper(), f"bull={ct=='bull'} bear={ct=='bear'}", ct_c, ct_c)}
      {row("Smart Probability", f"{a['smart_prob']}%", "EXPIRY" if a['is_expiry_day'] else "—", "v-o", "v-r" if a['is_expiry_day'] else "v-gray")}
      <tr class='sec-hdr-row'><td colspan='3' style='text-align:center;'>── SPCL VAL ──</td></tr>
      <tr><td class='lbl'>SPCL VAL</td><td class='spcl-val' colspan='2'>{spcl}</td></tr>
      {sec("RRS Dominance","Value","State")}
      {row("RRS Dominance", f"{a['dominance']:.4f}", f"domAvg={a['dom_avg']:.4f}", dom_c, dom_c)}
      {row("RRS Momentum (EMA5)", f"{a['momentum_diff']:.4f}", mom_state, mom_c, mom_c)}
      {sec("BTST Decay Edge","After 15:15","Opening Bias")}
      <tr>
        <td class='lbl'>BTST Signal</td>
        <td class='{btst_cls}'>{a['btst_signal']}</td>
        <td class='{btst_cls}'>{a['btst_target']}</td>
      </tr>
      {row("Decay Split (3-min avg)", f"CE {a['ce_edge_pct']:.1f}%", f"PE {a['pe_edge_pct']:.1f}%", "v-r","v-g")}
      {row("Decay Velocity", f"{a['decay_velocity']:.4f}", "Trend", "v-o","v-gray")}
    </tbody></table>
    """
    st.markdown(html, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PER-SYMBOL RENDER
# ─────────────────────────────────────────────
def render_symbol(access_token, sym, vix_info, now_ist):
    with st.spinner(f"Loading {DISPLAY_NAME[sym]}..."):
        expiry_dates, exp_err = fetch_expiry_dates(access_token, sym)

    if exp_err == "token_expired":
        del st.session_state["access_token"]; st.rerun()
    if exp_err or not expiry_dates:
        st.markdown(f"<div class='err-box'>⚠️ {DISPLAY_NAME[sym]}: {exp_err}</div>", unsafe_allow_html=True)
        return

    expiry_key = f"selected_expiry_{sym}"
    if expiry_key not in st.session_state:               st.session_state[expiry_key] = expiry_dates[0]
    if st.session_state[expiry_key] not in expiry_dates: st.session_state[expiry_key] = expiry_dates[0]

    col1, col2 = st.columns([4, 1])
    with col1:
        selected = st.selectbox(f"Expiry — {DISPLAY_NAME[sym]}", options=expiry_dates,
                                index=expiry_dates.index(st.session_state[expiry_key]),
                                key=f"sb_{sym}")
    with col2:
        debug_key = f"show_debug_{sym}"
        if debug_key not in st.session_state:
            st.session_state[debug_key] = False
        if st.button("🔍 Log", key=f"btn_debug_{sym}", use_container_width=True):
            st.session_state[debug_key] = not st.session_state[debug_key]

    st.session_state[expiry_key] = selected

    with st.spinner(""):
        data, chain_err, used_url = fetch_chain(access_token, sym, selected)

    if chain_err == "token_expired":
        del st.session_state["access_token"]; st.rerun()
    if chain_err or not data:
        st.markdown(f"<div class='err-box'>⚠️ {DISPLAY_NAME[sym]}: {chain_err}</div>", unsafe_allow_html=True)
        with st.expander("🔍 Debug"):
            st.write(f"**Key:** `{INSTRUMENT_KEY[sym]}`")
            st.write(f"**Expiry:** `{selected}`")
            st.json(st.session_state.get(f"raw_{sym}", {}))
        return

    try:
        result = parse(data, sym)
    except Exception as e:
        st.markdown(f"<div class='err-box'>⚠️ Parse error — {e}</div>", unsafe_allow_html=True)
        return

    otm_ltps   = fetch_otm_ltps(access_token, sym, selected, result["atm"], result["step"], data)
    state_key  = f"rrs_state_{sym}_{selected}"
    prev_state = st.session_state.get(state_key, {})

    try:
        analysis = compute_rrs_analysis(result, otm_ltps, selected, vix_info, now_ist, prev_state, sym)
        st.session_state[state_key] = analysis["new_state"]
    except Exception as e:
        analysis = None
        st.markdown(f"<div class='err-box'>⚠️ Analysis error — {e}</div>", unsafe_allow_html=True)

    # ── Instrument card with both PCR badges and OI Change ──────────────────
    pcr_oi_chg = result.get("pcr_oi_chg")
    atm_ce_oi_chg = result.get("atm_ce_oi_chg_pct")
    atm_pe_oi_chg = result.get("atm_pe_oi_chg_pct")
    spcl_val = analysis.get("spcl_val") if analysis else None
    bullish = not result.get("bearish", False)  # Invert bearish to get bullish
    ce_map = result.get("ce_map")  # Complete CE strikes map
    pe_map = result.get("pe_map")  # Complete PE strikes map

    # ── Entry Price Input (Optional - to lock P&L to specific entry prices) ──────
    opening_ce_prices = None
    opening_pe_prices = None

    # Initialize session state for this symbol+expiry combo
    state_key = f"entry_prices_{sym}_{selected}"
    if state_key not in st.session_state:
        st.session_state[state_key] = ""

    with st.expander(f"🔒 Lock Entry Prices — {DISPLAY_NAME[sym]} ({selected})", expanded=False):
        st.markdown("**Format:** `CE/PE Strike(B/S): Price` or `CE/PE Strike: Price`")
        st.markdown("Examples:")
        st.code("CE 24000(B): 67.5\nCE 24400(S): 45.0\nPE 23600(B): 85.0\nPE 23200(S): 50.0")

        entry_prices_text = st.text_area(
            "Paste entry prices (persists till expiry changes)",
            value=st.session_state[state_key],
            placeholder="CE 24000(B): 67.5\nCE 24400(S): 45.0\nPE 23600(B): 85.0\nPE 23200(S): 50.0",
            height=100,
            key=f"ta_{sym}_{selected}"
        )

        # Save to session state
        st.session_state[state_key] = entry_prices_text

        if entry_prices_text.strip():
            opening_ce_prices, opening_pe_prices = parse_entry_prices(entry_prices_text)
            if opening_ce_prices or opening_pe_prices:
                st.success(f"✓ Locked: {len(opening_ce_prices)} CE + {len(opening_pe_prices)} PE strikes")

    # Calculate days to expiry for Black-Scholes pricing
    days_to_expiry = calculate_days_to_expiry(selected, now_ist)

    # Calculate 26.11 reversal levels (this fetches API data and stores in session_state)
    levels_26_11 = _calculate_26_11_levels(result['spot'], sym)

    # DEBUG SECTION - Now API data is available in session_state
    debug_key = f"show_debug_{sym}"
    if st.session_state.get(debug_key, False):
        with st.expander("🔍 **DEBUG LOG** - 26.11 Levels API Data", expanded=True):
            # Try multiple keys to find the data
            api_debug = st.session_state.get(f"api_response_{sym}") or \
                       st.session_state.get("last_api_debug") or \
                       {}

            if api_debug and api_debug.get("status") == "SUCCESS":
                st.success(f"✅ API Data captured at: {api_debug.get('timestamp', 'N/A')}")
                st.write("**Symbol:**", api_debug.get("symbol", "N/A"))
                st.write("**OHLC Keys:**", api_debug.get("ohlc_keys", []))
                st.info(f"🔑 **Extracted HIGH: {api_debug.get('extracted_high', 'N/A')}**")
                st.info(f"🔑 **Extracted LOW: {api_debug.get('extracted_low', 'N/A')}**")
                st.write("**Calculated Levels:**")
                st.write(f"  • Upper (26.11%): {levels_26_11['upper']}")
                st.write(f"  • Lower (26.11%): {levels_26_11['lower']}")
                st.write("**Full OHLC Response:**")
                st.json(api_debug.get("ohlc_data", {}))
            else:
                st.warning("❌ No API data stored - checking conditions...")
                st.write(f"**Calculated levels anyway:** Upper={levels_26_11['upper']}, Lower={levels_26_11['lower']}")
                st.write(f"**High used:** {levels_26_11['high']}, **Low used:** {levels_26_11['low']}")
                all_keys = [k for k in st.session_state.keys() if "api" in k.lower() or "26_11" in k.lower()]
                st.write(f"Session keys with 'api' or '26_11': {all_keys}")

    st.markdown(
        f"<div class='inst-card'>"
        f"<div style='display:flex;justify-content:space-between;align-items:flex-start;'>"
        f"  <div><div class='inst-name'>{DISPLAY_NAME[sym]}</div>"
        f"       <div class='inst-meta'>EXP {selected} ({days_to_expiry:.1f}d)</div></div>"
        f"  <div style='text-align:right;'>"
        f"    <div class='inst-spot'>₹{result['spot']:,.2f}</div>"
        f"    <div class='inst-atm'>ATM → {result['atm']}</div>"
        f"    <div style='font-family:var(--mono);font-size:9px;color:#ffc940;margin-top:4px;'>"
        f"      (26.11% High) · {levels_26_11['upper']} <span style='color:#999;font-size:8px;'>(H:{levels_26_11['high']} L:{levels_26_11['low']})</span>"
        f"      <br/>"
        f"      (26.11% Low) · {levels_26_11['lower']} <span style='color:#999;font-size:8px;'>(H:{levels_26_11['high']} L:{levels_26_11['low']})</span>"
        f"    </div>"
        f"  </div></div>"
        f"{pcr_html(result['pcr'], pcr_oi_chg, atm_ce_oi_chg, atm_pe_oi_chg, spcl_val, result['atm'], result['step'], bullish, ce_map, pe_map, opening_ce_prices, opening_pe_prices, sym, days_to_expiry)}"
        f"</div>", unsafe_allow_html=True)

    render_table(result, sym, selected, analysis)

    # Show separate OI Change table
    oi_chg_html = oi_change_table(result, sym, selected)
    if oi_chg_html:
        st.markdown(oi_chg_html, unsafe_allow_html=True)

    if analysis:
        render_rrs_table(analysis, sym, selected)

# ─────────────────────────────────────────────
# FETCH INTRADAY TICK DATA
# ─────────────────────────────────────────────
# NORMALIZE DATE FORMAT
# ─────────────────────────────────────────────
def normalize_date(date_str):
    """Convert various date formats to YYYY-MM-DD"""
    if not date_str:
        return None

    # Already in YYYY-MM-DD format
    if isinstance(date_str, str) and len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
        return date_str

    # Try parsing common formats
    formats = [
        "%Y-%m-%d",      # 2025-01-30
        "%d-%m-%Y",      # 30-01-2025
        "%d/%m/%Y",      # 30/01/2025
        "%Y/%m/%d",      # 2025/01/30
        "%d %b %Y",      # 30 Jan 2025
        "%d-%b-%Y",      # 30-Jan-2025
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(str(date_str), fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # If all else fails, return as-is
    return str(date_str)

# ─────────────────────────────────────────────
# FETCH HISTORICAL CANDLE DATA
# ─────────────────────────────────────────────
def fetch_intraday_data(token, symbol, expiry_date, timeframe_minutes, candle_date=None):
    """
    Fetch historical option candles for ATM strikes
    timeframe_minutes: 1, 3, 15
    candle_date: Date to fetch candles for (YYYY-MM-DD format)
    Returns: Dict with 'ce_candles' and 'pe_candles' for replay
    """
    try:
        # Normalize expiry date to YYYY-MM-DD format
        normalized_expiry = normalize_date(expiry_date)
        normalized_candle_date = normalize_date(candle_date) if candle_date else normalized_expiry

        # Step 1: Get current option chain to find ATM strike
        oc_url = UPSTOX_OC_URLS[1]
        oc_params = {
            "instrument_key": INSTRUMENT_KEY[symbol],
            "expiry_date": normalized_expiry,
        }
        oc_response = requests.get(oc_url, params=oc_params, headers=upstox_headers(token), timeout=15)
        oc_data = oc_response.json()

        if oc_data.get("status") != "success" or not oc_data.get("data"):
            return None

        # Parse to find ATM strike
        parsed = parse(oc_data.get("data", []), symbol)
        atm_strike = parsed.get("atm")

        if not atm_strike:
            return None

        # Step 2: Construct option instrument keys for ATM CE and PE
        exp_date_obj = datetime.strptime(normalized_expiry, "%Y-%m-%d")
        exp_month = exp_date_obj.strftime("%b").upper()
        exp_year = str(exp_date_obj.year)[-1]

        ce_key = f"NSE_FO|{symbol}{exp_year}{exp_month}{int(atm_strike)}CE"
        pe_key = f"NSE_FO|{symbol}{exp_year}{exp_month}{int(atm_strike)}PE"

        # Step 3: Fetch historical candles for both CE and PE
        candle_url = UPSTOX_HISTORICAL_CANDLE
        ce_url = f"{candle_url}/{ce_key}/minutes/{timeframe_minutes}/{normalized_candle_date}/{normalized_candle_date}"
        pe_url = f"{candle_url}/{pe_key}/minutes/{timeframe_minutes}/{normalized_candle_date}/{normalized_candle_date}"

        # Fetch CE candles
        ce_response = requests.get(ce_url, headers=upstox_headers(token), timeout=15)
        ce_data = ce_response.json()
        ce_candles = ce_data.get("data", []) if ce_data.get("status") == "success" else []

        # Fetch PE candles
        pe_response = requests.get(pe_url, headers=upstox_headers(token), timeout=15)
        pe_data = pe_response.json()
        pe_candles = pe_data.get("data", []) if pe_data.get("status") == "success" else []

        if not ce_candles and not pe_candles:
            return None

        return {
            "atm_strike": atm_strike,
            "ce_key": ce_key,
            "pe_key": pe_key,
            "ce_candles": ce_candles,
            "pe_candles": pe_candles,
            "oc_data": oc_data.get("data", []),
        }

    except Exception as e:
        st.error(f"Error fetching replay data: {str(e)}")
        return None

# ─────────────────────────────────────────────
# REPLAY PAGE
# ─────────────────────────────────────────────
def show_replay_page(access_token, vix_info, now):
    """Display replay interface with controls"""
    st.markdown(f"<div class='sec-hdr'>🎬 SIGNAL REPLAY</div>", unsafe_allow_html=True)

    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("← Back to Live", use_container_width=True):
            st.session_state["page"] = "live"
            st.rerun()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        symbol = st.selectbox(
            "Symbol",
            options=["NIFTY", "BANKNIFTY", "HDFCBANK", "ICICIBANK", "SBIN", "RELIANCE"],
            key="replay_symbol"
        )

    with col2:
        replay_date = st.date_input(
            "Date",
            value=now.date(),
            key="replay_date"
        )

    with col3:
        expiry_dates, _ = fetch_expiry_dates(access_token, symbol)
        if expiry_dates:
            selected_expiry = st.selectbox(
                "Expiry",
                options=expiry_dates,
                key="replay_expiry"
            )
        else:
            st.error("No expiry dates available")
            return

    with col4:
        timeframe = st.selectbox(
            "Timeframe",
            options=["1-min", "3-min", "15-min"],
            key="replay_timeframe"
        )

    st.divider()

    # Replay controls
    col_controls = st.columns([2, 1, 1, 3, 1, 1])

    with col_controls[0]:
        if "replay_time_index" not in st.session_state:
            st.session_state["replay_time_index"] = 0
        if "is_replaying" not in st.session_state:
            st.session_state["is_replaying"] = False

        play_col, pause_col = st.columns(2)
        with play_col:
            if st.button("▶ Play", use_container_width=True, key="replay_play"):
                st.session_state["is_replaying"] = True
        with pause_col:
            if st.button("⏸ Pause", use_container_width=True, key="replay_pause"):
                st.session_state["is_replaying"] = False

    with col_controls[1]:
        st.write("")  # Spacer

    with col_controls[2]:
        speed = st.radio("Speed", ["1x", "2x", "4x"], horizontal=True, key="replay_speed_radio")
        speed_multiplier = {"1x": 1.0, "2x": 2.0, "4x": 4.0}[speed]

    with col_controls[3]:
        st.write("")  # Spacer

    with col_controls[4]:
        if st.button("⏮ Reset", use_container_width=True, key="replay_reset"):
            st.session_state["replay_time_index"] = 0

    st.divider()

    # Fetch and display replay data
    # Convert replay_date to string format for API calls
    replay_date_str = replay_date.strftime("%Y-%m-%d") if hasattr(replay_date, 'strftime') else str(replay_date)

    # Create a datetime for replay date in IST timezone for days_to_expiry calculation
    replay_date_ist = datetime.strptime(replay_date_str, "%Y-%m-%d").replace(tzinfo=pytz.timezone('Asia/Kolkata'))

    try:
        candle_data = fetch_intraday_data(access_token, symbol, selected_expiry, int(timeframe.split("-")[0]), replay_date_str)

        if candle_data:
            ce_candles = candle_data.get("ce_candles", [])
            pe_candles = candle_data.get("pe_candles", [])
            oc_data = candle_data.get("oc_data", [])
            atm_strike = candle_data.get("atm_strike")

            if not ce_candles or not pe_candles:
                st.warning("No candle data available for selected ATM strike")
                return

            # Determine number of candles available
            num_candles = min(len(ce_candles), len(pe_candles))

            # Show time slider
            current_idx = st.slider(
                "Trading Time",
                min_value=0,
                max_value=num_candles - 1,
                value=st.session_state.get("replay_time_index", 0),
                step=1,
                key="replay_slider"
            )
            st.session_state["replay_time_index"] = current_idx

            # Get candle data at current index
            ce_candle = ce_candles[current_idx]
            pe_candle = pe_candles[current_idx]
            ce_timestamp = ce_candle.get("timestamp", "")
            pe_timestamp = pe_candle.get("timestamp", "")

            # Extract timestamp for display (format: "2025-01-04T10:15:00Z")
            try:
                time_obj = datetime.fromisoformat(ce_timestamp.replace("Z", "+00:00"))
                time_display = time_obj.strftime("%H:%M")
            except:
                time_display = "N/A"

            st.markdown(f"### Current Time: {time_display} IST", unsafe_allow_html=True)

            st.divider()

            # Construct synthetic option chain data from candles
            # Using close prices from historical candles
            ce_close = ce_candle.get("close", 0)
            pe_close = pe_candle.get("close", 0)
            ce_oi = ce_candle.get("volume", 0)  # Using volume as proxy for OI
            pe_oi = pe_candle.get("volume", 0)

            # Build synthetic option chain entry
            synthetic_oc = [{
                "strike_price": float(atm_strike),
                "call_options": [{
                    "ltp": float(ce_close),
                    "oi": float(ce_oi),
                    "bid_qty": 0,
                    "ask_qty": 0,
                }],
                "put_options": [{
                    "ltp": float(pe_close),
                    "oi": float(pe_oi),
                    "bid_qty": 0,
                    "ask_qty": 0,
                }],
            }]

            # Parse to get metrics
            result = parse(synthetic_oc, symbol)

            # Display card with current data
            pcr_oi_chg = result.get("pcr_oi_chg")
            atm_ce_oi_chg = result.get("atm_ce_oi_chg_pct", 0)
            atm_pe_oi_chg = result.get("atm_pe_oi_chg_pct", 0)
            spcl_val = result.get("spcl_val")  # May be None in replay mode
            bullish = not result.get("bearish", False)  # Invert bearish to get bullish
            ce_map = result.get("ce_map")  # Complete CE strikes map
            pe_map = result.get("pe_map")  # Complete PE strikes map

            # ── Entry Price Input (Optional - to lock P&L to specific entry prices) ──────
            opening_ce_prices = None
            opening_pe_prices = None

            # Initialize session state for replay
            replay_state_key = f"replay_entry_prices_{symbol}_{selected_expiry}"
            if replay_state_key not in st.session_state:
                st.session_state[replay_state_key] = ""

            with st.expander(f"🔒 Lock Entry Prices — {DISPLAY_NAME[symbol]} Replay ({selected_expiry})", expanded=False):
                st.markdown("**Format:** `CE/PE Strike(B/S): Price` or `CE/PE Strike: Price`")
                st.markdown("Examples:")
                st.code("CE 24000(B): 67.5\nCE 24400(S): 45.0\nPE 23600(B): 85.0\nPE 23200(S): 50.0")

                entry_prices_text = st.text_area(
                    "Paste entry prices (persists till expiry changes)",
                    value=st.session_state[replay_state_key],
                    placeholder="CE 24000(B): 67.5\nCE 24400(S): 45.0\nPE 23600(B): 85.0\nPE 23200(S): 50.0",
                    height=100,
                    key=f"replay_ta_{symbol}_{selected_expiry}"
                )

                # Save to session state
                st.session_state[replay_state_key] = entry_prices_text

                if entry_prices_text.strip():
                    opening_ce_prices, opening_pe_prices = parse_entry_prices(entry_prices_text)
                    if opening_ce_prices or opening_pe_prices:
                        st.success(f"✓ Locked: {len(opening_ce_prices)} CE + {len(opening_pe_prices)} PE strikes")

            # Calculate days to expiry for Black-Scholes pricing
            replay_days_to_expiry = calculate_days_to_expiry(selected_expiry, replay_date_ist)

            st.markdown(
                f"<div class='inst-card'>"
                f"<div style='display:flex;justify-content:space-between;align-items:flex-start;'>"
                f"  <div><div class='inst-name'>{DISPLAY_NAME[symbol]}</div>"
                f"       <div class='inst-meta'>EXP {selected_expiry} ({replay_days_to_expiry:.1f}d)</div></div>"
                f"  <div style='text-align:right;'>"
                f"    <div class='inst-spot'>CE: ₹{ce_close:.2f} | PE: ₹{pe_close:.2f}</div>"
                f"    <div class='inst-atm'>ATM → {result['atm']}</div>"
                f"  </div></div>"
                f"{pcr_html(result['pcr'], pcr_oi_chg, atm_ce_oi_chg, atm_pe_oi_chg, spcl_val, result['atm'], result['step'], bullish, ce_map, pe_map, opening_ce_prices, opening_pe_prices, sym, replay_days_to_expiry)}"
                f"</div>", unsafe_allow_html=True)

            st.markdown(f"<div class='refresh-note'>⏱ Replay at {speed} speed (x{speed_multiplier})</div>", unsafe_allow_html=True)
        else:
            st.warning("No data available for selected parameters. Check that historical data exists for this date.")

    except Exception as e:
        st.error(f"Replay error: {str(e)}")

# ─────────────────────────────────────────────
# SETUP GUIDE
# ─────────────────────────────────────────────
def show_setup_guide():
    st.markdown("""
    <div class='setup-box'>
    <b style='font-size:14px;color:white;'>⚙️ One-time Upstox setup</b><br><br>
    <b>Step 1</b> — developer.upstox.com → My Apps → Create New App<br>
    &nbsp;&nbsp;• Redirect URL = your Streamlit app URL<br>
    &nbsp;&nbsp;• Copy <b>API Key</b> and <b>Secret Key</b><br><br>
    <b>Step 2</b> — Streamlit Cloud → Settings → Secrets:<br><br>
    <code>[upstox]<br>
    api_key      = "your_api_key"<br>
    api_secret   = "your_secret_key"<br>
    redirect_uri = "https://yourapp.streamlit.app"</code><br><br>
    <b>Step 3</b> — Click Login once each morning.
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
now       = datetime.now(IST)
mkt       = now.weekday() < 5 and (9, 15) <= (now.hour, now.minute) <= (15, 30)
dot       = "🟢" if mkt else "🔴"
mkt_label = "OPEN" if mkt else "CLOSED"

st.markdown(
    f"<div class='app-header'>"
    f"<span class='app-title'>ATM Options Tracker</span>"
    f"<span class='app-sub'>{dot} {mkt_label} &nbsp;·&nbsp; "
    f"{now.strftime('%d %b %Y %H:%M IST')} &nbsp;·&nbsp; Upstox API</span>"
    f"</div>", unsafe_allow_html=True)

if not secrets_ok():
    st.markdown("<p style='color:#fc8181;font-size:13px;'>⚠️ Upstox credentials not found in Streamlit secrets.</p>",
                unsafe_allow_html=True)
    show_setup_guide()
    st.stop()

api_key      = st.secrets["upstox"]["api_key"]
api_secret   = st.secrets["upstox"]["api_secret"]
redirect_uri = st.secrets["upstox"]["redirect_uri"]

qp        = st.query_params
auth_code = qp.get("code")

if auth_code and "access_token" not in st.session_state:
    with st.spinner("Completing Upstox login..."):
        token, err = exchange_code(api_key, api_secret, redirect_uri, auth_code)
    if token:
        st.session_state["access_token"]   = token
        st.session_state["token_acquired"] = time.time()
        st.query_params.clear()
        st.rerun()
    else:
        st.error(f"Login failed: {err}")
        st.stop()

if "access_token" in st.session_state:
    if time.time() - st.session_state.get("token_acquired", 0) > 86400:
        del st.session_state["access_token"]
        st.rerun()

if "access_token" not in st.session_state:
    auth_url = build_auth_url(api_key, redirect_uri)
    st.markdown(f"""
    <div class='login-box'>
      <p style='font-family:var(--display);font-size:20px;font-weight:700;color:white;margin-bottom:.4rem;'>
        Login with Upstox</p>
      <p style='color:#4a6080;font-size:12px;font-family:var(--mono);margin-bottom:1.5rem;'>
        One click per trading day</p>
      <a href='{auth_url}'
         style='display:inline-block;background:linear-gradient(135deg,#2979ff,#651fff);
                color:white;padding:11px 28px;border-radius:8px;text-decoration:none;
                font-family:var(--mono);font-size:13px;font-weight:600;letter-spacing:.5px;'>
        CONNECT →</a>
    </div>""", unsafe_allow_html=True)
    st.stop()

access_token = st.session_state["access_token"]
vix_info     = fetch_vix(access_token)

# Initialize page state
if "page" not in st.session_state:
    st.session_state["page"] = "live"

# Sidebar navigation
with st.sidebar:
    st.markdown("### 📱 Navigation")
    page = st.radio(
        "Select View",
        options=["📊 Live", "🎬 Replay"],
        key="page_radio",
        label_visibility="collapsed"
    )
    st.session_state["page"] = "live" if "Live" in page else "replay"
    st.divider()

# Show appropriate page
if st.session_state["page"] == "live":
    for group_title, symbols in SYMBOL_GROUPS:
        st.markdown(f"<div class='sec-hdr'>{group_title}</div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        for col, sym in zip([col1, col2], symbols):
            with col:
                render_symbol(access_token, sym, vix_info, now)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([4, 1, 1])
    with c2:
        if st.button("🔓 Logout"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

else:  # Replay page
    show_replay_page(access_token, vix_info, now)

st.markdown(
    f"<p class='refresh-note'>↻ auto-refresh 3 min &nbsp;·&nbsp; "
    f"Updated {now.strftime('%H:%M:%S IST')}</p>",
    unsafe_allow_html=True)

time.sleep(180)
st.rerun()
