import streamlit as st
import requests
import math
import time
import logging
from datetime import datetime
import pytz

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(page_title="ATM Options Tracker", page_icon="📊", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    .stApp { background: #0e1117; }
    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    th { background: #1a237e; color: white; padding: 8px 12px; text-align: left; font-weight: 500; }
    td { padding: 7px 12px; border-bottom: 1px solid #2a2a3a; }
    .ce-lbl   { background: #0d47a1; color: white; }
    .pe-lbl   { background: #4a148c; color: white; }
    .sum-row  { background: #004d40; color: white; font-weight: 500; }
    .sqrt-row { background: #bf360c; color: white; font-weight: 500; }
    .bias-bear{ background: #ffcccc; color: #cc0000; font-weight: 600; }
    .bias-bull{ background: #ccffcc; color: #006600; font-weight: 600; }
    .strike-ce{ background: white; color: #1565c0; font-weight: 500; }
    .strike-pe{ background: white; color: #6a1b9a; font-weight: 500; }
    .price-ce { background: white; color: #0d47a1; }
    .price-pe { background: white; color: #4a148c; }
    .spot-val { font-size: 22px; font-weight: 600; color: white; }
    .spot-lbl { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    .atm-val  { font-size: 14px; color: #ffd54f; margin-top: 2px; }
    .card     { background: #1a1a2e; border-radius: 10px; padding: 0.85rem 1.25rem;
                border: 1px solid #2a2a4a; margin-bottom: 0.6rem; }
    .err-box  { background: #2a1a1a; border: 1px solid #7f1d1d; border-radius: 8px;
                padding: 0.75rem 1rem; color: #fc8181; font-size: 13px; margin-bottom: 0.6rem; }
    .refresh-note { font-size: 11px; color: #555; text-align: right; margin-top: 6px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
STRIKE_STEP = {"NIFTY": 50, "BANKNIFTY": 100}
IST         = pytz.timezone("Asia/Kolkata")
logger      = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# NSE SESSION  (your proven session code)
# ─────────────────────────────────────────────
@st.cache_resource(ttl=170)
def create_nse_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept":          "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection":      "keep-alive",
        "Referer":         "https://www.nseindia.com/get-quotes/derivatives?symbol=NIFTY",
    })
    try:
        session.get("https://www.nseindia.com/", timeout=10)
        time.sleep(2)
        session.get(
            "https://www.nseindia.com/market-data/live-market-indices",
            timeout=10
        )
        time.sleep(1)
        return session
    except Exception as e:
        logger.error(f"Session init failed: {e}")
        return None

# ─────────────────────────────────────────────
# FETCH NSE OPTION CHAIN  (cached 3 min)
# Returns full data dict which includes:
#   data["records"]["underlyingValue"] → live spot  ← used for ATM
#   data["records"]["data"]            → CE/PE rows
# ─────────────────────────────────────────────
@st.cache_data(ttl=180, show_spinner=False)
def fetch_chain(symbol: str):
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"

    for attempt in range(3):
        try:
            sess = create_nse_session()
            if sess is None:
                return None, "Could not create NSE session"

            r = sess.get(url, timeout=15)

            if r.status_code == 200:
                data = r.json()
                if "records" in data:
                    return data, None
                # Got JSON but no 'records' → stale session
                logger.warning(f"No 'records' in response for {symbol}, attempt {attempt+1}")

            # Clear stale session and retry
            st.cache_resource.clear()
            time.sleep(2 + attempt)

        except Exception as e:
            logger.error(f"{symbol} fetch error attempt {attempt+1}: {e}")
            if attempt == 2:
                return None, str(e)
            time.sleep(2)

    return None, "NSE did not return valid data after 3 attempts"

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def snap_atm(price: float, step: int) -> int:
    return int(round(price / step) * step)

def parse(chain: dict, symbol: str) -> dict:
    step   = STRIKE_STEP[symbol]
    spot   = chain["records"]["underlyingValue"]   # live spot from NSE
    expiry = chain["records"]["expiryDates"][0]     # nearest expiry
    atm    = snap_atm(spot, step)                   # snap spot → ATM

    ce_map, pe_map = {}, {}
    for rec in chain["records"]["data"]:
        if rec["expiryDate"] != expiry:
            continue
        s = rec["strikePrice"]
        if "CE" in rec:
            ce_map[s] = rec["CE"].get("lastPrice") or 0.0
        if "PE" in rec:
            pe_map[s] = rec["PE"].get("lastPrice") or 0.0

    # CE: ATM, ATM+1, ATM+2 → strikes go UP (OTM calls)
    ce_rows = [
        {"label": "ATM CE",   "strike": atm,            "price": ce_map.get(atm,            0.0)},
        {"label": "ATM+1 CE", "strike": atm + step,     "price": ce_map.get(atm + step,     0.0)},
        {"label": "ATM+2 CE", "strike": atm + 2 * step, "price": ce_map.get(atm + 2 * step, 0.0)},
    ]
    # PE: ATM, ATM-1, ATM-2 → strikes go DOWN (OTM puts)
    pe_rows = [
        {"label": "ATM PE",   "strike": atm,            "price": pe_map.get(atm,            0.0)},
        {"label": "ATM-1 PE", "strike": atm - step,     "price": pe_map.get(atm - step,     0.0)},
        {"label": "ATM-2 PE", "strike": atm - 2 * step, "price": pe_map.get(atm - 2 * step, 0.0)},
    ]

    ce_sum  = sum(r["price"] for r in ce_rows)
    pe_sum  = sum(r["price"] for r in pe_rows)
    ce_sqrt = math.sqrt(ce_sum) if ce_sum > 0 else 0.0
    pe_sqrt = math.sqrt(pe_sum) if pe_sum > 0 else 0.0

    return dict(
        spot    = spot,
        atm     = atm,
        expiry  = expiry,
        ce_rows = ce_rows,
        pe_rows = pe_rows,
        ce_sum  = ce_sum,
        pe_sum  = pe_sum,
        ce_sqrt = ce_sqrt,
        pe_sqrt = pe_sqrt,
        bearish = ce_sqrt > pe_sqrt,
    )

def render_table(r: dict, symbol: str):
    bear  = r["bearish"]
    bcls  = "bias-bear" if bear else "bias-bull"
    btxt  = (
        f"▼ &nbsp;BEARISH &nbsp;(√CE {r['ce_sqrt']:.2f} > √PE {r['pe_sqrt']:.2f})"
        if bear else
        f"▲ &nbsp;BULLISH &nbsp;(√PE {r['pe_sqrt']:.2f} > √CE {r['ce_sqrt']:.2f})"
    )
    ce_html = "".join(
        f"<tr><td class='ce-lbl'>{x['label']}</td>"
        f"<td class='strike-ce'>{x['strike']}</td>"
        f"<td class='price-ce'>{x['price']:.2f}</td></tr>"
        for x in r["ce_rows"]
    )
    pe_html = "".join(
        f"<tr><td class='pe-lbl'>{x['label']}</td>"
        f"<td class='strike-pe'>{x['strike']}</td>"
        f"<td class='price-pe'>{x['price']:.2f}</td></tr>"
        for x in r["pe_rows"]
    )
    st.markdown(f"""
    <table>
      <thead><tr>
        <th>{symbol} &nbsp;|&nbsp; ATM: {r['atm']}
            &nbsp;|&nbsp; Exp: {r['expiry']}</th>
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
# MAIN
# ─────────────────────────────────────────────
now  = datetime.now(IST)
mkt  = now.weekday() < 5 and (9, 15) <= (now.hour, now.minute) <= (15, 30)
dot  = "🟢 Market open" if mkt else "🔴 Market closed"

st.markdown(
    f"<h2 style='color:white;margin-bottom:0;'>📊 ATM Options Tracker</h2>"
    f"<p style='color:#888;font-size:12px;margin-top:4px;'>"
    f"{dot} &nbsp;·&nbsp; IST: {now.strftime('%d %b %Y &nbsp; %H:%M:%S')}"
    f" &nbsp;·&nbsp; ATM from live NSE spot"
    f" &nbsp;·&nbsp; Auto-refresh every 3 min</p>",
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)

for col, sym in [(col1, "NIFTY"), (col2, "BANKNIFTY")]:
    with col:
        with st.spinner(f"Loading {sym}..."):
            chain, err = fetch_chain(sym)

        if err or chain is None:
            st.markdown(
                f"<div class='err-box'>⚠️ {sym}: {err}<br>"
                f"<small>NSE may be slow — will retry automatically in 3 min.</small></div>",
                unsafe_allow_html=True,
            )
            continue

        try:
            result = parse(chain, sym)
        except Exception as e:
            st.markdown(
                f"<div class='err-box'>⚠️ {sym}: Parse error — {e}</div>",
                unsafe_allow_html=True,
            )
            continue

        st.markdown(
            f"<div class='card'>"
            f"<div class='spot-lbl'>{sym} Live Spot</div>"
            f"<div class='spot-val'>₹ {result['spot']:,.2f}</div>"
            f"<div class='atm-val'>ATM Strike → {result['atm']}"
            f" &nbsp;|&nbsp; Expiry: {result['expiry']}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        render_table(result, sym)

st.markdown(
    f"<p class='refresh-note'>Updated: {now.strftime('%H:%M:%S IST')}"
    f" &nbsp;·&nbsp; Source: NSE India (live spot + option chain)</p>",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# AUTO-REFRESH every 3 min
# ─────────────────────────────────────────────
time.sleep(180)
st.rerun()
