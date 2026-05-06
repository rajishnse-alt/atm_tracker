import streamlit as st
import requests
import math
import time
from datetime import datetime
import pytz

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="ATM Options Tracker",
    page_icon="📊",
    layout="wide",
)

st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    .stApp { background: #0e1117; }
    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    th { background: #1a237e; color: white; padding: 8px 12px; text-align: left; font-weight: 500; }
    td { padding: 7px 12px; border-bottom: 1px solid #2a2a3a; }
    .ce-lbl  { background: #0d47a1; color: white; }
    .pe-lbl  { background: #4a148c; color: white; }
    .sum-row { background: #004d40; color: white; font-weight: 500; }
    .sqrt-row{ background: #e65100; color: white; font-weight: 500; }
    .bias-bear{ background: #ffcccc; color: #cc0000; font-weight: 600; }
    .bias-bull{ background: #ccffcc; color: #006600; font-weight: 600; }
    .val-cell { background: white; color: #1a1a1a; }
    .strike-ce{ background: white; color: #1565c0; font-weight: 500; }
    .strike-pe{ background: white; color: #6a1b9a; font-weight: 500; }
    .price-ce { background: white; color: #0d47a1; }
    .price-pe { background: white; color: #4a148c; }
    .hdr-cell { font-size: 13px; }
    .status-ok  { color: #00e676; font-size: 12px; }
    .status-err { color: #ff5252; font-size: 12px; }
    .spot-val { font-size: 22px; font-weight: 600; color: white; }
    .spot-lbl { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    .card { background: #1a1a2e; border-radius: 10px; padding: 1rem 1.25rem;
            border: 1px solid #2a2a4a; margin-bottom: 0.5rem; }
    .refresh-note { font-size: 11px; color: #555; text-align: right; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
STRIKE_STEP = {"NIFTY": 50, "BANKNIFTY": 100}
NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://www.nseindia.com/option-chain",
}
IST = pytz.timezone("Asia/Kolkata")

# ─────────────────────────────────────────────
# NSE SESSION (cached 3 min)
# ─────────────────────────────────────────────
@st.cache_resource(ttl=170)
def make_session():
    s = requests.Session()
    try:
        s.get("https://www.nseindia.com", headers=NSE_HEADERS, timeout=10)
        time.sleep(0.8)
        s.get("https://www.nseindia.com/option-chain", headers=NSE_HEADERS, timeout=10)
    except Exception:
        pass
    return s

# ─────────────────────────────────────────────
# FETCH OPTION CHAIN (cached 3 min)
# ─────────────────────────────────────────────
@st.cache_data(ttl=180, show_spinner=False)
def fetch_chain(symbol: str):
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    for attempt in range(3):
        try:
            sess = make_session()
            r = sess.get(url, headers=NSE_HEADERS, timeout=15)
            if r.status_code == 200:
                return r.json(), None
            if attempt < 2:
                st.cache_resource.clear()
                time.sleep(1)
        except Exception as e:
            if attempt == 2:
                return None, str(e)
            time.sleep(1)
    return None, f"HTTP {r.status_code}"

# ─────────────────────────────────────────────
# PARSE & COMPUTE
# ─────────────────────────────────────────────
def atm_strike(spot, step):
    return int(round(spot / step) * step)

def parse(data, symbol):
    step = STRIKE_STEP[symbol]
    spot = data["records"]["underlyingValue"]
    expiry = data["records"]["expiryDates"][0]
    atm = atm_strike(spot, step)

    ce_map, pe_map = {}, {}
    for rec in data["records"]["data"]:
        if rec["expiryDate"] != expiry:
            continue
        s = rec["strikePrice"]
        if "CE" in rec:
            ce_map[s] = rec["CE"].get("lastPrice") or 0
        if "PE" in rec:
            pe_map[s] = rec["PE"].get("lastPrice") or 0

    ce0 = ce_map.get(atm,            0)
    ce1 = ce_map.get(atm + step,     0)
    ce2 = ce_map.get(atm + 2 * step, 0)

    pe0 = pe_map.get(atm,            0)
    pe1 = pe_map.get(atm - step,     0)
    pe2 = pe_map.get(atm - 2 * step, 0)

    ce_sum  = ce0 + ce1 + ce2
    pe_sum  = pe0 + pe1 + pe2
    ce_sqrt = math.sqrt(ce_sum) if ce_sum > 0 else 0
    pe_sqrt = math.sqrt(pe_sum) if pe_sum > 0 else 0

    return {
        "spot":   spot,
        "expiry": expiry,
        "atm":    atm,
        "step":   step,
        "ce": [
            {"label": "ATM CE",   "strike": atm,            "price": ce0},
            {"label": "ATM+1 CE", "strike": atm + step,     "price": ce1},
            {"label": "ATM+2 CE", "strike": atm + 2 * step, "price": ce2},
        ],
        "pe": [
            {"label": "ATM PE",   "strike": atm,            "price": pe0},
            {"label": "ATM-1 PE", "strike": atm - step,     "price": pe1},
            {"label": "ATM-2 PE", "strike": atm - 2 * step, "price": pe2},
        ],
        "ce_sum":  ce_sum,
        "pe_sum":  pe_sum,
        "ce_sqrt": ce_sqrt,
        "pe_sqrt": pe_sqrt,
        "bearish": ce_sqrt > pe_sqrt,
    }

# ─────────────────────────────────────────────
# RENDER TABLE
# ─────────────────────────────────────────────
def render_table(result, symbol):
    bias_class = "bias-bear" if result["bearish"] else "bias-bull"
    bias_text  = (f"▼ &nbsp;BEARISH &nbsp;(√CE {result['ce_sqrt']:.2f} > √PE {result['pe_sqrt']:.2f})"
                  if result["bearish"] else
                  f"▲ &nbsp;BULLISH &nbsp;(√PE {result['pe_sqrt']:.2f} > √CE {result['ce_sqrt']:.2f})")

    rows_ce = "".join(
        f"<tr>"
        f"  <td class='ce-lbl'>{r['label']}</td>"
        f"  <td class='strike-ce'>{r['strike']}</td>"
        f"  <td class='price-ce'>{r['price']:.2f}</td>"
        f"</tr>"
        for r in result["ce"]
    )
    rows_pe = "".join(
        f"<tr>"
        f"  <td class='pe-lbl'>{r['label']}</td>"
        f"  <td class='strike-pe'>{r['strike']}</td>"
        f"  <td class='price-pe'>{r['price']:.2f}</td>"
        f"</tr>"
        for r in result["pe"]
    )

    html = f"""
    <table>
      <thead>
        <tr>
          <th class='hdr-cell'>{symbol} &nbsp;|&nbsp; ATM: {result['atm']}
              &nbsp;|&nbsp; Exp: {result['expiry']}</th>
          <th class='hdr-cell'>Strike</th>
          <th class='hdr-cell'>Price</th>
        </tr>
      </thead>
      <tbody>
        {rows_ce}
        <tr class='sum-row'>
          <td>CE SUM ▶</td><td></td>
          <td>{result['ce_sum']:.2f}</td>
        </tr>
        <tr class='sqrt-row'>
          <td>√ CE</td><td></td>
          <td>{result['ce_sqrt']:.2f}</td>
        </tr>
        {rows_pe}
        <tr class='sum-row'>
          <td>PE SUM ▶</td><td></td>
          <td>{result['pe_sum']:.2f}</td>
        </tr>
        <tr class='sqrt-row'>
          <td>√ PE</td><td></td>
          <td>{result['pe_sqrt']:.2f}</td>
        </tr>
        <tr class='{bias_class}'>
          <td>BIAS</td>
          <td>√CE vs √PE</td>
          <td>{bias_text}</td>
        </tr>
      </tbody>
    </table>
    """
    st.markdown(html, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
now_ist = datetime.now(IST)
is_market_hours = (
    now_ist.weekday() < 5
    and (9, 15) <= (now_ist.hour, now_ist.minute) <= (15, 30)
)

st.markdown(
    f"<h2 style='color:white;margin-bottom:0;'>📊 ATM Options Tracker</h2>"
    f"<p style='color:#888;font-size:12px;margin-top:4px;'>"
    f"{'🟢 Market open' if is_market_hours else '🔴 Market closed'} &nbsp;·&nbsp; "
    f"IST: {now_ist.strftime('%d %b %Y &nbsp;%H:%M:%S')} &nbsp;·&nbsp; "
    f"Auto-refresh every 3 min</p>",
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)

for col, symbol in [(col1, "NIFTY"), (col2, "BANKNIFTY")]:
    with col:
        with st.spinner(f"Loading {symbol}..."):
            data, err = fetch_chain(symbol)

        if err or data is None:
            st.error(f"{symbol}: Failed to fetch — {err}. NSE may be blocking. Retry in 3 min.")
            continue

        try:
            result = parse(data, symbol)
        except Exception as e:
            st.error(f"{symbol}: Parse error — {e}")
            continue

        st.markdown(
            f"<div class='card'>"
            f"  <div class='spot-lbl'>{symbol} Spot</div>"
            f"  <div class='spot-val'>₹ {result['spot']:,.2f}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        render_table(result, symbol)

st.markdown(
    f"<p class='refresh-note'>Last updated: {now_ist.strftime('%H:%M:%S IST')} &nbsp;·&nbsp; "
    f"Next refresh in ~3 min &nbsp;·&nbsp; Data source: NSE India</p>",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# AUTO REFRESH every 3 minutes
# ─────────────────────────────────────────────
if is_market_hours:
    time.sleep(180)
    st.rerun()
else:
    st.markdown(
        "<p style='color:#555;font-size:12px;text-align:center;margin-top:1rem;'>"
        "Market is closed. Page will auto-refresh when market opens (Mon–Fri 9:15–15:30 IST).</p>",
        unsafe_allow_html=True,
    )
    # Still refresh every 5 min outside market hours to check if it opened
    time.sleep(300)
    st.rerun()
