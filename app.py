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

# Try both API versions
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

# ─────────────────────────────────────────────
# STEP 1: GET EXPIRY DATES FROM UPSTOX
# Much more reliable than calculating manually
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
        if r.status_code == 401:
            return None, "token_expired"
        if d.get("status") == "success" and d.get("data"):
            raw = d["data"]
            # Upstox returns either list of strings OR list of dicts
            if raw and isinstance(raw[0], dict):
                # Extract expiry string from each dict
                # Try common key names
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

# ─────────────────────────────────────────────
# STEP 2: GET OPTION CHAIN FOR NEAREST EXPIRY
# Tries v2 then v3 endpoint automatically
# ─────────────────────────────────────────────
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

    # Store raw response for debug
    st.session_state[f"raw_{symbol}"] = last_raw
    return None, last_err, UPSTOX_OC_URLS[-1]

# ─────────────────────────────────────────────
# PARSE & COMPUTE
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

        call   = (row.get("call_options") or {})
        call_md = call.get("market_data") or {}
        ce_map[strike] = float(call_md.get("ltp") or 0)

        put    = (row.get("put_options") or {})
        put_md = put.get("market_data") or {}
        pe_map[strike] = float(put_md.get("ltp") or 0)

    if spot is None:
        common = set(ce_map) & set(pe_map)
        if common:
            spot = float(min(common, key=lambda s: abs(ce_map[s] - pe_map[s])))

    if spot is None:
        raise ValueError("Could not determine underlying spot price")

    atm = snap(spot, step)

    ce_rows = [
        {"label": "ATM CE",   "strike": atm,            "price": ce_map.get(float(atm),            0.0)},
        {"label": "ATM+1 CE", "strike": atm + step,     "price": ce_map.get(float(atm + step),     0.0)},
        {"label": "ATM+2 CE", "strike": atm + 2 * step, "price": ce_map.get(float(atm + 2 * step), 0.0)},
    ]
    pe_rows = [
        {"label": "ATM PE",   "strike": atm,            "price": pe_map.get(float(atm),            0.0)},
        {"label": "ATM-1 PE", "strike": atm - step,     "price": pe_map.get(float(atm - step),     0.0)},
        {"label": "ATM-2 PE", "strike": atm - 2 * step, "price": pe_map.get(float(atm - 2 * step), 0.0)},
    ]

    ce_sum  = sum(r["price"] for r in ce_rows)
    pe_sum  = sum(r["price"] for r in pe_rows)
    ce_sqrt = math.sqrt(ce_sum) if ce_sum > 0 else 0.0
    pe_sqrt = math.sqrt(pe_sum) if pe_sum > 0 else 0.0

    return dict(spot=spot, atm=atm,
                ce_rows=ce_rows, pe_rows=pe_rows,
                ce_sum=ce_sum,   pe_sum=pe_sum,
                ce_sqrt=ce_sqrt, pe_sqrt=pe_sqrt,
                bearish=ce_sqrt > pe_sqrt)

# ─────────────────────────────────────────────
# RENDER TABLE
# ─────────────────────────────────────────────
def render_table(r, symbol, expiry):
    bear  = r["bearish"]
    bcls  = "bias-bear" if bear else "bias-bull"
    btxt  = (f"▼ &nbsp;BEARISH &nbsp;(√CE {r['ce_sqrt']:.2f} > √PE {r['pe_sqrt']:.2f})"
             if bear else
             f"▲ &nbsp;BULLISH &nbsp;(√PE {r['pe_sqrt']:.2f} > √CE {r['ce_sqrt']:.2f})")
    ce_html = "".join(
        f"<tr><td class='ce-lbl'>{x['label']}</td>"
        f"<td class='strike-ce'>{x['strike']}</td>"
        f"<td class='price-ce'>{x['price']:.2f}</td></tr>"
        for x in r["ce_rows"])
    pe_html = "".join(
        f"<tr><td class='pe-lbl'>{x['label']}</td>"
        f"<td class='strike-pe'>{x['strike']}</td>"
        f"<td class='price-pe'>{x['price']:.2f}</td></tr>"
        for x in r["pe_rows"])
    st.markdown(f"""
    <table>
      <thead><tr>
        <th>{symbol} &nbsp;|&nbsp; ATM: {r['atm']}
            &nbsp;|&nbsp; Spot: ₹{r['spot']:,.2f}
            &nbsp;|&nbsp; Exp: {expiry}</th>
        <th>Strike</th><th>Price</th>
      </tr></thead>
      <tbody>
        {ce_html}
        <tr class='sum-row'><td>CE SUM ▶</td><td></td><td>{r['ce_sum']:.2f}</td></tr>
        <tr class='sqrt-row'><td>√ CE</td><td></td><td>{r['ce_sqrt']:.2f}</td></tr>
        {pe_html}
        <tr class='sum-row'><td>PE SUM ▶</td><td></td><td>{r['pe_sum']:.2f}</td></tr>
        <tr class='sqrt-row'><td>√ PE</td><td></td><td>{r['pe_sqrt']:.2f}</td></tr>
        <tr class='{bcls}'><td>BIAS</td><td>√CE vs √PE</td><td>{btxt}</td></tr>
      </tbody>
    </table>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SETUP GUIDE
# ─────────────────────────────────────────────
def show_setup_guide():
    st.markdown("""
    <div class='setup-box'>
    <b style='font-size:15px;color:white;'>⚙️ One-time Upstox setup (5 minutes)</b><br><br>
    <b>Step 1</b> — Go to <b>developer.upstox.com</b> → Login → My Apps → Create New App<br>
    &nbsp;&nbsp;• Redirect URL = your Streamlit app URL<br>
    &nbsp;&nbsp;• Copy <b>API Key</b> and <b>Secret Key</b><br><br>
    <b>Step 2</b> — Streamlit Cloud → your app → <b>Settings → Secrets</b>:<br><br>
    <code style='display:block;background:#1a1a2e;padding:12px;border-radius:6px;
                 color:#90caf9;font-size:13px;line-height:2;'>
    [upstox]<br>
    api_key      = "your_api_key"<br>
    api_secret   = "your_secret_key"<br>
    redirect_uri = "https://yourname-atm-tracker-xxxx.streamlit.app"
    </code><br>
    <b>Step 3</b> — Click <b>Login with Upstox</b> once each morning. Done!
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
now = datetime.now(IST)
mkt = now.weekday() < 5 and (9, 15) <= (now.hour, now.minute) <= (15, 30)
dot = "🟢 Market open" if mkt else "🔴 Market closed"

st.markdown(
    f"<h2 style='color:white;margin-bottom:0;'>📊 ATM Options Tracker</h2>"
    f"<p style='color:#888;font-size:12px;margin-top:4px;'>"
    f"{dot} &nbsp;·&nbsp; IST: {now.strftime('%d %b %Y &nbsp; %H:%M:%S')}"
    f" &nbsp;·&nbsp; Data: Upstox API"
    f" &nbsp;·&nbsp; Auto-refresh every 3 min</p>",
    unsafe_allow_html=True)

if not secrets_ok():
    st.markdown("<p style='color:#fc8181;'>⚠️ Upstox credentials not found in Streamlit secrets.</p>",
                unsafe_allow_html=True)
    show_setup_guide()
    st.stop()

api_key      = st.secrets["upstox"]["api_key"]
api_secret   = st.secrets["upstox"]["api_secret"]
redirect_uri = st.secrets["upstox"]["redirect_uri"]

# ── OAuth callback ─────────────────────────────────────────────
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

# ── Token expiry check ─────────────────────────────────────────
if "access_token" in st.session_state:
    if time.time() - st.session_state.get("token_acquired", 0) > 86400:
        del st.session_state["access_token"]
        st.rerun()

# ── Login screen ───────────────────────────────────────────────
if "access_token" not in st.session_state:
    auth_url = build_auth_url(api_key, redirect_uri)
    st.markdown(f"""
    <div class='login-box'>
      <p style='color:#90caf9;font-size:18px;font-weight:500;margin-bottom:.5rem;'>
        🔐 Login with Upstox</p>
      <p style='color:#888;font-size:13px;margin-bottom:1.5rem;'>
        One click per trading day.</p>
      <a href='{auth_url}'
         style='display:inline-block;background:#5c4fbd;color:white;
                padding:12px 32px;border-radius:8px;text-decoration:none;
                font-size:15px;font-weight:500;'>
        Login with Upstox →</a>
    </div>""", unsafe_allow_html=True)
    st.stop()

# ── Fetch & render ─────────────────────────────────────────────
access_token = st.session_state["access_token"]
col1, col2   = st.columns(2)

for col, sym in [(col1, "NIFTY"), (col2, "BANKNIFTY")]:
    with col:

        # Step 1: get expiry dates from Upstox
        with st.spinner(f"Getting {sym} expiry dates..."):
            expiry_dates, exp_err = fetch_expiry_dates(access_token, sym)

        if exp_err == "token_expired":
            del st.session_state["access_token"]
            st.rerun()

        if exp_err or not expiry_dates:
            st.markdown(
                f"<div class='err-box'>⚠️ {sym}: Could not get expiry dates — {exp_err}</div>",
                unsafe_allow_html=True)
            continue

        nearest = expiry_dates[0]   # already sorted, first = nearest

        # Step 2: get option chain for nearest expiry
        with st.spinner(f"Loading {sym} option chain ({nearest})..."):
            data, chain_err, used_url = fetch_chain(access_token, sym, nearest)

        if chain_err == "token_expired":
            del st.session_state["access_token"]
            st.rerun()

        if chain_err or not data:
            st.markdown(
                f"<div class='err-box'>⚠️ {sym}: {chain_err}</div>",
                unsafe_allow_html=True)
            # Debug panel — shows raw API response
            with st.expander(f"🔍 Debug — {sym} raw API response"):
                st.write(f"**Instrument key used:** `{INSTRUMENT_KEY[sym]}`")
                st.write(f"**Expiry date used:** `{nearest}`")
                st.write(f"**URL tried:** `{used_url}`")
                st.write(f"**Available expiries:** `{expiry_dates}`")
                raw = st.session_state.get(f"raw_{sym}", {})
                st.json(raw if raw else {"note": "No raw response captured"})
            continue

        # Step 3: parse and render
        try:
            result = parse(data, sym)
        except Exception as e:
            st.markdown(
                f"<div class='err-box'>⚠️ {sym}: Parse error — {e}</div>",
                unsafe_allow_html=True)
            with st.expander(f"🔍 Debug — {sym} first data row"):
                st.json(data[0] if data else {})
            continue

        st.markdown(
            f"<div class='card'>"
            f"<div class='spot-lbl'>{sym} Underlying Spot</div>"
            f"<div class='spot-val'>₹ {result['spot']:,.2f}</div>"
            f"<div class='atm-val'>ATM → {result['atm']}"
            f" &nbsp;|&nbsp; Expiry: {nearest}</div>"
            f"</div>",
            unsafe_allow_html=True)
        render_table(result, sym, nearest)

# ── Logout + debug ─────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
c1, c2, c3 = st.columns([3, 1, 1])
with c2:
    if st.button("🔓 Logout"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

st.markdown(
    f"<p class='refresh-note'>Updated: {now.strftime('%H:%M:%S IST')}"
    f" &nbsp;·&nbsp; Source: Upstox API v2/v3</p>",
    unsafe_allow_html=True)

time.sleep(180)
st.rerun()
