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
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Syne:wght@600;700;800&display=swap');

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

  /* ── Header ───────────────────────────────── */
  .app-header {
    display: flex; align-items: baseline; gap: 10px;
    margin-bottom: 4px;
  }
  .app-title {
    font-family: var(--display); font-size: 22px; font-weight: 800;
    color: white; letter-spacing: -.3px;
  }
  .app-sub {
    font-family: var(--mono); font-size: 11px;
    color: var(--muted); letter-spacing: .5px;
  }
  .mkt-dot { font-size: 11px; font-family: var(--mono); }

  /* ── Section header ───────────────────────── */
  .sec-hdr {
    font-family: var(--display); font-size: 11px; font-weight: 700;
    color: var(--muted); letter-spacing: 2px; text-transform: uppercase;
    margin: 1.1rem 0 .45rem; padding-bottom: 5px;
    border-bottom: 1px solid var(--border);
  }

  /* ── Instrument card ──────────────────────── */
  .inst-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: .6rem .85rem .55rem;
    margin-bottom: .45rem;
    position: relative;
    overflow: hidden;
  }
  .inst-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, var(--ce), var(--pe));
  }
  .inst-name {
    font-family: var(--display); font-size: 16px; font-weight: 800;
    color: white; letter-spacing: .4px; line-height: 1;
  }
  .inst-meta {
    font-family: var(--mono); font-size: 10px;
    color: var(--muted); margin-top: 3px; letter-spacing: .3px;
  }
  .inst-spot {
    font-family: var(--mono); font-size: 18px; font-weight: 600;
    color: white; letter-spacing: -.5px;
  }
  .inst-atm {
    font-family: var(--mono); font-size: 11px;
    color: var(--gold); margin-top: 1px;
  }

  /* ── PCR badge ────────────────────────────── */
  .pcr-wrap {
    display: inline-flex; align-items: center; gap: 6px;
    background: var(--surface); border: 1px solid var(--border2);
    border-radius: 6px; padding: 3px 9px 3px 7px;
    margin-top: 5px;
  }
  .pcr-label {
    font-family: var(--mono); font-size: 10px;
    color: var(--muted); letter-spacing: 1px; text-transform: uppercase;
  }
  .pcr-val { font-family: var(--mono); font-size: 13px; font-weight: 600; }
  .pcr-bull-c { color: var(--bull); }
  .pcr-bear-c { color: var(--bear); }
  .pcr-neut-c { color: var(--gold); }
  .pcr-tag {
    font-family: var(--mono); font-size: 9px; font-weight: 600;
    padding: 1px 5px; border-radius: 3px; letter-spacing: .5px;
    text-transform: uppercase;
  }
  .pcr-tag-bull { background: var(--bull-dim); color: var(--bull); }
  .pcr-tag-bear { background: var(--bear-dim); color: var(--bear); }
  .pcr-tag-neut { background: var(--gold-dim); color: var(--gold); }

  /* ── Options table ────────────────────────── */
  .opt-table {
    width: 100%; border-collapse: collapse;
    font-family: var(--mono); font-size: 11px;
    margin-bottom: .5rem;
  }
  .opt-table thead th {
    background: transparent; color: var(--muted);
    font-size: 9px; font-weight: 600; letter-spacing: 1.5px;
    text-transform: uppercase; padding: 4px 6px;
    border-bottom: 1px solid var(--border);
    text-align: left;
  }
  .opt-table thead th:last-child { text-align: right; }
  .opt-table td {
    padding: 3px 6px; border-bottom: 1px solid var(--border);
    white-space: nowrap;
  }
  .opt-table td:last-child { text-align: right; }

  /* row types */
  .r-ce    { color: var(--ce); }
  .r-pe    { color: var(--pe); }
  .r-ce-bg { background: var(--ce-dim); }
  .r-pe-bg { background: var(--pe-dim); }
  .r-sum   { background: #0a1a10; }
  .r-sum td { color: #4caf50 !important; font-weight: 600; font-size: 11px; }
  .r-sqrt  { background: #150b00; }
  .r-sqrt td { color: var(--gold) !important; font-weight: 600; font-size: 11px; }
  .r-bias  { border-radius: 0 0 6px 6px; }
  .r-bias td { font-weight: 700; font-size: 11px; padding: 4px 6px; }
  .r-bias-bull { background: var(--bull-dim); }
  .r-bias-bull td { color: var(--bull) !important; }
  .r-bias-bear { background: var(--bear-dim); }
  .r-bias-bear td { color: var(--bear) !important; }

  .tag-ce {
    display: inline-block;
    background: #102040; color: var(--ce);
    font-size: 9px; font-weight: 600; padding: 1px 5px;
    border-radius: 3px; letter-spacing: .5px;
    border: 1px solid #1a3060;
  }
  .tag-pe {
    display: inline-block;
    background: #1e0a28; color: var(--pe);
    font-size: 9px; font-weight: 600; padding: 1px 5px;
    border-radius: 3px; letter-spacing: .5px;
    border: 1px solid #3a1a50;
  }
  .strike-num { color: var(--text); font-weight: 500; }
  .price-num  { font-weight: 600; }

  /* ── Error / misc ─────────────────────────── */
  .err-box {
    background: #1a0808; border: 1px solid #5a1a1a;
    border-radius: 8px; padding: .6rem .9rem;
    color: #fc8181; font-family: var(--mono); font-size: 12px;
    margin-bottom: .5rem;
  }
  .login-box {
    background: var(--surface); border: 1px solid var(--border2);
    border-radius: 14px; padding: 2.5rem 2rem;
    text-align: center; max-width: 460px; margin: 3rem auto;
  }
  .setup-box {
    background: #0d1a10; border: 1px solid #1a4020;
    border-radius: 10px; padding: 1rem 1.25rem;
    color: #a5d6a7; font-family: var(--mono); font-size: 12px;
    line-height: 2;
  }
  .refresh-note {
    font-family: var(--mono); font-size: 10px;
    color: var(--muted); text-align: right; margin-top: 8px;
  }
  code {
    background: #1a2030; padding: 2px 6px;
    border-radius: 4px; font-size: 12px;
    color: #90caf9; font-family: var(--mono);
  }

  /* hide streamlit chrome */
  #MainMenu, footer, header { visibility: hidden; }
  .stSpinner > div { border-top-color: var(--ce) !important; }
  div[data-testid="stSelectbox"] label {
    font-family: var(--mono) !important; font-size: 11px !important;
    color: var(--muted) !important;
  }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
IST = pytz.timezone("Asia/Kolkata")

STRIKE_STEP_FIXED = {"NIFTY": 50, "BANKNIFTY": 100}

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
    "NIFTY":     "NIFTY",
    "BANKNIFTY": "BANKNIFTY",
    "HDFCBANK":  "HDFC Bank",
    "ICICIBANK": "ICICI Bank",
    "SBIN":      "SBI",
    "RELIANCE":  "Reliance",
}

SYMBOL_GROUPS = [
    ("📈 Index Options",     ["NIFTY",    "BANKNIFTY"]),
    ("🏦 Bank Stocks",       ["HDFCBANK", "ICICIBANK"]),
    ("🏢 Large Cap Stocks",  ["SBIN",     "RELIANCE"]),
]

UPSTOX_OC_URLS      = ["https://api.upstox.com/v2/option/chain", "https://api.upstox.com/v3/option/chain"]
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
# FETCH
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
                             item.get("date") or item.get("expiryDate") or "")
                         for item in raw]
                dates = [x for x in dates if x]
            else:
                dates = [str(x) for x in raw]
            dates = sorted(set(dates))
            return (dates, None) if dates else (None, "Empty expiry list")
        return None, f"Expiry fetch failed: {d}"
    except Exception as e:
        return None, str(e)

def fetch_chain(token, symbol, expiry_date):
    cache_key = f"oc_{symbol}_{expiry_date}"
    time_key  = f"oc_time_{symbol}_{expiry_date}"
    now = time.time()
    if (cache_key in st.session_state
            and time_key in st.session_state
            and now - st.session_state[time_key] < 180):
        return st.session_state[cache_key], None, "cached"

    last_err = "No response"; last_raw = {}
    for url in UPSTOX_OC_URLS:
        try:
            r = requests.get(url, params={"instrument_key": INSTRUMENT_KEY[symbol],
                                          "expiry_date": expiry_date},
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
# PARSE & COMPUTE
# ─────────────────────────────────────────────
def snap(price, step):
    return int(round(price / step) * step)

def parse(data, symbol):
    step   = STRIKE_STEP_FIXED.get(symbol) or infer_strike_step(data)
    ce_map = {}; pe_map = {}; ce_oi = {}; pe_oi = {}; spot = None

    for row in data:
        strike = float(row.get("strike_price", 0))
        if spot is None:
            sp = row.get("underlying_spot_price")
            if sp: spot = float(sp)

        call_md = (row.get("call_options") or {}).get("market_data") or {}
        ce_map[strike] = float(call_md.get("ltp") or 0)
        ce_oi[strike]  = float(call_md.get("oi")  or 0)

        put_md  = (row.get("put_options") or {}).get("market_data") or {}
        pe_map[strike] = float(put_md.get("ltp") or 0)
        pe_oi[strike]  = float(put_md.get("oi")  or 0)

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

    # PCR: CE = ATM to ATM+6, PE = ATM to ATM-6
    ce_pcr_strikes = [atm + (i * step) for i in range(-4, 7)]   # ATM, +1 … +6
    pe_pcr_strikes = [atm - (i * step) for i in range(-4, 7)]   # ATM, -1 … -6
    total_ce_oi  = sum(ce_oi.get(float(s), 0.0) for s in ce_pcr_strikes)
    total_pe_oi  = sum(pe_oi.get(float(s), 0.0) for s in pe_pcr_strikes)
    pcr = (total_pe_oi / total_ce_oi) if total_ce_oi > 0 else 0.0

    return dict(spot=spot, atm=atm,
                ce_rows=ce_rows, pe_rows=pe_rows,
                ce_sum=ce_sum,   pe_sum=pe_sum,
                ce_sqrt=ce_sqrt, pe_sqrt=pe_sqrt,
                bearish=ce_sqrt > pe_sqrt,
                pcr=pcr,
                total_pe_oi=total_pe_oi,
                total_ce_oi=total_ce_oi)

# ─────────────────────────────────────────────
# RENDER
# ─────────────────────────────────────────────
def pcr_html(pcr):
    if pcr > 1.2:
        cls, tag, text = "pcr-bull-c", "pcr-tag-bull", "BULLISH"
    elif pcr < 0.8:
        cls, tag, text = "pcr-bear-c", "pcr-tag-bear", "BEARISH"
    else:
        cls, tag, text = "pcr-neut-c", "pcr-tag-neut", "NEUTRAL"
    return (f"<div class='pcr-wrap'>"
            f"<span class='pcr-label'>PCR</span>"
            f"<span class='pcr-val {cls}'>{pcr:.2f}</span>"
            f"<span class='pcr-tag {tag}'>{text}</span>"
            f"<span class='pcr-label' style='margin-left:4px;font-size:9px;'>CE:ATM→+6 | PE:ATM→-6</span>"
            f"</div>")

def render_table(r, symbol, expiry):
    bear = r["bearish"]
    bias_cls   = "r-bias-bear" if bear else "r-bias-bull"
    bias_arrow = "▼" if bear else "▲"
    bias_txt   = "BEARISH" if bear else "BULLISH"
    bias_detail = (f"√CE {r['ce_sqrt']:.2f} &gt; √PE {r['pe_sqrt']:.2f}"
                   if bear else
                   f"√PE {r['pe_sqrt']:.2f} &gt; √CE {r['ce_sqrt']:.2f}")

    def ce_row(x):
        return (f"<tr class='r-ce-bg'>"
                f"<td><span class='tag-ce'>CE</span></td>"
                f"<td class='r-ce'>{x['label']}</td>"
                f"<td class='strike-num'>{x['strike']}</td>"
                f"<td class='price-num r-ce'>{x['price']:.2f}</td>"
                f"</tr>")

    def pe_row(x):
        return (f"<tr class='r-pe-bg'>"
                f"<td><span class='tag-pe'>PE</span></td>"
                f"<td class='r-pe'>{x['label']}</td>"
                f"<td class='strike-num'>{x['strike']}</td>"
                f"<td class='price-num r-pe'>{x['price']:.2f}</td>"
                f"</tr>")

    ce_rows_html = "".join(ce_row(x) for x in r["ce_rows"])
    pe_rows_html = "".join(pe_row(x) for x in r["pe_rows"])

    st.markdown(f"""
    <table class='opt-table'>
      <thead>
        <tr>
          <th style='width:32px;'></th>
          <th>Strike</th>
          <th>Label</th>
          <th>LTP</th>
        </tr>
      </thead>
      <tbody>
        {ce_rows_html}
        <tr class='r-sum'>
          <td colspan='3'>CE SUM</td>
          <td>{r['ce_sum']:.2f}</td>
        </tr>
        <tr class='r-sqrt'>
          <td colspan='3'>√ CE</td>
          <td>{r['ce_sqrt']:.2f}</td>
        </tr>
        {pe_rows_html}
        <tr class='r-sum'>
          <td colspan='3'>PE SUM</td>
          <td>{r['pe_sum']:.2f}</td>
        </tr>
        <tr class='r-sqrt'>
          <td colspan='3'>√ PE</td>
          <td>{r['pe_sqrt']:.2f}</td>
        </tr>
        <tr class='r-bias {bias_cls}'>
          <td colspan='2'>{bias_arrow} {bias_txt}</td>
          <td colspan='2'>{bias_detail}</td>
        </tr>
      </tbody>
    </table>
    """, unsafe_allow_html=True)

def render_symbol(access_token, sym):
    with st.spinner(f"Loading {DISPLAY_NAME[sym]}..."):
        expiry_dates, exp_err = fetch_expiry_dates(access_token, sym)

    if exp_err == "token_expired":
        del st.session_state["access_token"]; st.rerun()

    if exp_err or not expiry_dates:
        st.markdown(f"<div class='err-box'>⚠️ {DISPLAY_NAME[sym]}: {exp_err}</div>",
                    unsafe_allow_html=True)
        return

    expiry_key = f"selected_expiry_{sym}"
    if expiry_key not in st.session_state:
        st.session_state[expiry_key] = expiry_dates[0]
    if st.session_state[expiry_key] not in expiry_dates:
        st.session_state[expiry_key] = expiry_dates[0]

    selected = st.selectbox(
        f"Expiry — {DISPLAY_NAME[sym]}",
        options=expiry_dates,
        index=expiry_dates.index(st.session_state[expiry_key]),
        key=f"sb_{sym}",
    )
    st.session_state[expiry_key] = selected

    with st.spinner(""):
        data, chain_err, used_url = fetch_chain(access_token, sym, selected)

    if chain_err == "token_expired":
        del st.session_state["access_token"]; st.rerun()

    if chain_err or not data:
        st.markdown(f"<div class='err-box'>⚠️ {DISPLAY_NAME[sym]}: {chain_err}</div>",
                    unsafe_allow_html=True)
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

    # ── Instrument card ───────────────────────
    st.markdown(
        f"<div class='inst-card'>"
        f"<div style='display:flex;justify-content:space-between;align-items:flex-start;'>"
        f"  <div>"
        f"    <div class='inst-name'>{DISPLAY_NAME[sym]}</div>"
        f"    <div class='inst-meta'>EXP {selected}</div>"
        f"  </div>"
        f"  <div style='text-align:right;'>"
        f"    <div class='inst-spot'>₹{result['spot']:,.2f}</div>"
        f"    <div class='inst-atm'>ATM → {result['atm']}</div>"
        f"  </div>"
        f"</div>"
        f"{pcr_html(result['pcr'])}"
        f"</div>",
        unsafe_allow_html=True)

    render_table(result, sym, selected)

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
now = datetime.now(IST)
mkt = now.weekday() < 5 and (9, 15) <= (now.hour, now.minute) <= (15, 30)
dot = "🟢" if mkt else "🔴"
mkt_label = "OPEN" if mkt else "CLOSED"

st.markdown(
    f"<div class='app-header'>"
    f"<span class='app-title'>ATM Options Tracker</span>"
    f"<span class='app-sub'>{dot} {mkt_label} &nbsp;·&nbsp; "
    f"{now.strftime('%d %b %Y %H:%M IST')} &nbsp;·&nbsp; Upstox API</span>"
    f"</div>",
    unsafe_allow_html=True)

if not secrets_ok():
    st.markdown("<p style='color:#fc8181;font-size:13px;'>⚠️ Upstox credentials not found in Streamlit secrets.</p>",
                unsafe_allow_html=True)
    show_setup_guide()
    st.stop()

api_key      = st.secrets["upstox"]["api_key"]
api_secret   = st.secrets["upstox"]["api_secret"]
redirect_uri = st.secrets["upstox"]["redirect_uri"]

# ── OAuth callback ──────────────────────────────────────────────
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

# ── Render groups ───────────────────────────────────────────────
access_token = st.session_state["access_token"]

for group_title, symbols in SYMBOL_GROUPS:
    st.markdown(f"<div class='sec-hdr'>{group_title}</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    for col, sym in zip([col1, col2], symbols):
        with col:
            render_symbol(access_token, sym)

# ── Logout ──────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
c1, c2, c3 = st.columns([4, 1, 1])
with c2:
    if st.button("🔓 Logout"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

st.markdown(
    f"<p class='refresh-note'>↻ auto-refresh 3 min &nbsp;·&nbsp; "
    f"Updated {now.strftime('%H:%M:%S IST')}</p>",
    unsafe_allow_html=True)

time.sleep(180)
st.rerun()
