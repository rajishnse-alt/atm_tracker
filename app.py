import streamlit as st
import requests
import math
import time
from datetime import date, timedelta, datetime
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

# Upstox instrument keys for indices
INSTRUMENT_KEY = {
    "NIFTY":     "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
}

# Upstox API endpoints
UPSTOX_AUTH_URL  = "https://api.upstox.com/v2/login/authorization/dialog"
UPSTOX_TOKEN_URL = "https://api.upstox.com/v2/login/authorization/token"
UPSTOX_OC_URL    = "https://api.upstox.com/v2/option/chain"

# ─────────────────────────────────────────────
# SECRETS CHECK
# ─────────────────────────────────────────────
def secrets_ok():
    try:
        _ = st.secrets["upstox"]["api_key"]
        _ = st.secrets["upstox"]["api_secret"]
        _ = st.secrets["upstox"]["redirect_uri"]
        return True
    except Exception:
        return False

# ─────────────────────────────────────────────
# NEAREST EXPIRY
# Nifty weekly = Thursday | BankNifty weekly = Wednesday
# ─────────────────────────────────────────────
def nearest_expiry(symbol: str) -> str:
    today      = date.today()
    target_dow = 3 if symbol == "NIFTY" else 2   # Thu=3, Wed=2
    days       = target_dow - today.weekday()
    if days < 0:
        days += 7
    return (today + timedelta(days=days)).strftime("%Y-%m-%d")  # "2025-05-08"

# ─────────────────────────────────────────────
# OAUTH HELPERS
# ─────────────────────────────────────────────
def build_auth_url(api_key: str, redirect_uri: str) -> str:
    return (
        f"{UPSTOX_AUTH_URL}"
        f"?response_type=code"
        f"&client_id={api_key}"
        f"&redirect_uri={redirect_uri}"
    )

def exchange_code(api_key, api_secret, redirect_uri, code):
    try:
        r = requests.post(
            UPSTOX_TOKEN_URL,
            data={
                "code":          code,
                "client_id":     api_key,
                "client_secret": api_secret,
                "redirect_uri":  redirect_uri,
                "grant_type":    "authorization_code",
            },
            headers={"Accept": "application/json"},
            timeout=15,
        )
        d = r.json()
        if "access_token" in d:
            return d["access_token"], None
        return None, d.get("message") or d.get("error_description") or str(d)
    except Exception as e:
        return None, str(e)

# ─────────────────────────────────────────────
# FETCH OPTION CHAIN  (session-state cache 3 min)
# ─────────────────────────────────────────────
def fetch_chain(access_token: str, symbol: str, expiry: str):
    cache_key  = f"oc_{symbol}"
    time_key   = f"oc_time_{symbol}"
    now        = time.time()

    # Return cached data if fresher than 3 minutes
    if (cache_key in st.session_state and
            time_key in st.session_state and
            now - st.session_state[time_key] < 180):
        return st.session_state[cache_key], None

    try:
        r = requests.get(
            UPSTOX_OC_URL,
            params={
                "instrument_key": INSTRUMENT_KEY[symbol],
                "expiry_date":    expiry,
            },
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept":        "application/json",
            },
            timeout=15,
        )
        d = r.json()

        if r.status_code == 401:
            # Token expired — force re-login
            if "access_token" in st.session_state:
                del st.session_state["access_token"]
            return None, "token_expired"

        if d.get("status") == "success" and d.get("data"):
            st.session_state[cache_key] = d["data"]
            st.session_state[time_key]  = now
            return d["data"], None

        return None, d.get("message") or d.get("errors") or "No data"

    except Exception as e:
        return None, str(e)

# ─────────────────────────────────────────────
# PARSE & COMPUTE
# ─────────────────────────────────────────────
def snap(price: float, step: int) -> int:
    return int(round(price / step) * step)

def parse(data: list, symbol: str) -> dict:
    step    = STRIKE_STEP[symbol]
    ce_map  = {}
    pe_map  = {}
    spot    = None

    for row in data:
        strike = float(row.get("strike_price", 0))

        if spot is None:
            sp = row.get("underlying_spot_price")
            if sp:
                spot = float(sp)

        # Call options
        call = row.get("call_options") or {}
        call_md = call.get("market_data") or {}
        ce_map[strike] = float(call_md.get("ltp") or 0)

        # Put options
        put = row.get("put_options") or {}
        put_md = put.get("market_data") or {}
        pe_map[strike] = float(put_md.get("ltp") or 0)

    if spot is None:
        # Fallback: strike where |CE - PE| is minimum
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
def render_table(r: dict, symbol: str, expiry: str):
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

    <b>Step 1 — Create Upstox API app</b><br>
    &nbsp;&nbsp;• Go to <b>developer.upstox.com</b> → Login → My Apps → Create New App<br>
    &nbsp;&nbsp;• App Name: ATM Tracker<br>
    &nbsp;&nbsp;• Redirect URL: <b>your Streamlit app URL</b>
      (e.g. https://yourname-atm-tracker-xxxx.streamlit.app)<br>
    &nbsp;&nbsp;• Copy the <b>API Key</b> and <b>Secret Key</b><br><br>

    <b>Step 2 — Add secrets to Streamlit Cloud</b><br>
    &nbsp;&nbsp;• Streamlit Cloud → your app → <b>Settings → Secrets</b> → paste:<br><br>

    <code style='display:block;background:#1a1a2e;padding:12px;border-radius:6px;
                 color:#90caf9;font-size:13px;line-height:2;'>
    [upstox]<br>
    api_key      = "your_upstox_api_key"<br>
    api_secret   = "your_upstox_secret_key"<br>
    redirect_uri = "https://yourname-atm-tracker-xxxx.streamlit.app"
    </code><br>

    <b>Step 3 — Daily login (once per trading day, 15 seconds)</b><br>
    &nbsp;&nbsp;• Click the <b>Login with Upstox</b> button that appears<br>
    &nbsp;&nbsp;• Login on Upstox → redirects back automatically<br>
    &nbsp;&nbsp;• Done — app runs all day without any more logins<br><br>

    <small style='color:#666;'>Upstox tokens last until end of trading day.
    You only need to click Login once each morning.</small>
    </div>
    """, unsafe_allow_html=True)

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

# ── Setup guide if secrets missing ────────────────────────────
if not secrets_ok():
    st.markdown(
        "<p style='color:#fc8181;'>⚠️ Upstox credentials not found in Streamlit secrets.</p>",
        unsafe_allow_html=True)
    show_setup_guide()
    st.stop()

api_key      = st.secrets["upstox"]["api_key"]
api_secret   = st.secrets["upstox"]["api_secret"]
redirect_uri = st.secrets["upstox"]["redirect_uri"]

# ── Handle OAuth callback (code in URL after Upstox login) ────
qp = st.query_params
auth_code = qp.get("code")

if auth_code and "access_token" not in st.session_state:
    with st.spinner("Completing Upstox login..."):
        token, err = exchange_code(api_key, api_secret, redirect_uri, auth_code)
    if token:
        st.session_state["access_token"]  = token
        st.session_state["token_acquired"] = time.time()
        st.query_params.clear()   # remove ?code= from URL
        st.rerun()
    else:
        st.markdown(
            f"<div class='err-box'>❌ Login failed: {err}<br>"
            f"<small>Try clicking Login again.</small></div>",
            unsafe_allow_html=True)
        st.stop()

# ── Check token validity (Upstox tokens last ~24 hrs) ─────────
if "access_token" in st.session_state:
    age = time.time() - st.session_state.get("token_acquired", 0)
    if age > 86400:   # > 24 hours → force re-login
        del st.session_state["access_token"]
        st.rerun()

# ── Login screen if no token ───────────────────────────────────
if "access_token" not in st.session_state:
    auth_url = build_auth_url(api_key, redirect_uri)
    st.markdown(f"""
    <div class='login-box'>
      <p style='color:#90caf9;font-size:18px;font-weight:500;margin-bottom:0.5rem;'>
        🔐 Login with Upstox
      </p>
      <p style='color:#888;font-size:13px;margin-bottom:1.5rem;'>
        One click per trading day.<br>
        You'll be redirected back here automatically.
      </p>
      <a href='{auth_url}'
         style='display:inline-block;background:#5c4fbd;color:white;
                padding:12px 32px;border-radius:8px;text-decoration:none;
                font-size:15px;font-weight:500;'>
        Login with Upstox →
      </a>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Fetch and render both indices ─────────────────────────────
access_token = st.session_state["access_token"]
col1, col2   = st.columns(2)

for col, sym in [(col1, "NIFTY"), (col2, "BANKNIFTY")]:
    with col:
        expiry = nearest_expiry(sym)

        with st.spinner(f"Loading {sym}..."):
            data, err = fetch_chain(access_token, sym, expiry)

        if err == "token_expired":
            st.markdown(
                "<div class='err-box'>🔒 Upstox token expired — please login again.</div>",
                unsafe_allow_html=True)
            st.rerun()

        if err or data is None:
            st.markdown(
                f"<div class='err-box'>⚠️ {sym}: {err}</div>",
                unsafe_allow_html=True)
            continue

        try:
            result = parse(data, sym)
        except Exception as e:
            st.markdown(
                f"<div class='err-box'>⚠️ {sym}: Parse error — {e}</div>",
                unsafe_allow_html=True)
            continue

        st.markdown(
            f"<div class='card'>"
            f"<div class='spot-lbl'>{sym} Underlying Spot</div>"
            f"<div class='spot-val'>₹ {result['spot']:,.2f}</div>"
            f"<div class='atm-val'>ATM → {result['atm']}"
            f" &nbsp;|&nbsp; Expiry: {expiry}</div>"
            f"</div>",
            unsafe_allow_html=True)
        render_table(result, sym, expiry)

# ── Logout button (bottom right) ──────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
col_a, col_b, col_c = st.columns([4, 1, 1])
with col_c:
    if st.button("🔓 Logout"):
        del st.session_state["access_token"]
        st.rerun()

st.markdown(
    f"<p class='refresh-note'>Updated: {now.strftime('%H:%M:%S IST')}"
    f" &nbsp;·&nbsp; Source: Upstox API v2 (works from any server globally)</p>",
    unsafe_allow_html=True)

# ── Auto-refresh every 3 min ──────────────────────────────────
time.sleep(180)
st.rerun()
