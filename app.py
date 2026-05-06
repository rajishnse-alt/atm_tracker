import streamlit as st
import requests
import yfinance as yf
import math
import time
from datetime import datetime
import pytz

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
    .open-val { font-size: 14px; color: #ffd54f; margin-top: 2px; }
    .card { background: #1a1a2e; border-radius: 10px; padding: 0.85rem 1.25rem;
            border: 1px solid #2a2a4a; margin-bottom: 0.6rem; }
    .err-box  { background: #2a1a1a; border: 1px solid #7f1d1d; border-radius: 8px;
                padding: 0.75rem 1rem; color: #fc8181; font-size: 13px; }
    .refresh-note { font-size: 11px; color: #555; text-align: right; margin-top: 6px; }
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────
STRIKE_STEP = {"NIFTY": 50, "BANKNIFTY": 100}
YF_TICKER   = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK"}
IST         = pytz.timezone("Asia/Kolkata")
NSE_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0.0.0 Safari/537.36"),
    "Accept":          "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection":      "keep-alive",
    "Referer":         "https://www.nseindia.com/option-chain",
}

# ── Last 3-min candle open via yfinance ───────────────────────
@st.cache_data(ttl=180, show_spinner=False)
def get_3min_open(symbol: str):
    """
    Returns (candle_open, live_spot, candle_time_str)
    candle_open = open of last COMPLETED 3-min candle  ← used for ATM
    live_spot   = close of the most recent candle       ← display only
    """
    try:
        hist = yf.Ticker(YF_TICKER[symbol]).history(period="2d", interval="3m")
        if hist.empty:
            return None, None, "N/A"
        # iloc[-1] may be an in-progress candle → use iloc[-2] when available
        idx          = -2 if len(hist) >= 2 else -1
        candle_open  = float(hist["Open"].iloc[idx])
        live_spot    = float(hist["Close"].iloc[-1])
        candle_time  = hist.index[idx].tz_convert(IST).strftime("%H:%M")
        return candle_open, live_spot, candle_time
    except Exception as e:
        return None, None, str(e)

# ── NSE session ────────────────────────────────────────────────
@st.cache_resource(ttl=170)
def make_session():
    s = requests.Session()
    try:
        s.get("https://www.nseindia.com",       headers=NSE_HEADERS, timeout=10)
        time.sleep(1)
        s.get("https://www.nseindia.com/option-chain", headers=NSE_HEADERS, timeout=10)
    except Exception:
        pass
    return s

# ── NSE option chain ───────────────────────────────────────────
@st.cache_data(ttl=180, show_spinner=False)
def fetch_chain(symbol: str):
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    for attempt in range(3):
        try:
            r = make_session().get(url, headers=NSE_HEADERS, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if "records" in data:
                    return data, None
            # Session stale — clear and retry
            st.cache_resource.clear()
            time.sleep(2)
        except Exception as e:
            if attempt == 2:
                return None, str(e)
            time.sleep(2)
    return None, "NSE did not return valid data after 3 attempts"

# ── Helpers ────────────────────────────────────────────────────
def snap(price: float, step: int) -> int:
    return int(round(price / step) * step)

def parse(chain, symbol: str, atm_base: float) -> dict:
    step   = STRIKE_STEP[symbol]
    spot   = chain["records"]["underlyingValue"]
    expiry = chain["records"]["expiryDates"][0]
    atm    = snap(atm_base, step)

    ce_map, pe_map = {}, {}
    for rec in chain["records"]["data"]:
        if rec["expiryDate"] != expiry:
            continue
        s = rec["strikePrice"]
        if "CE" in rec:
            ce_map[s] = rec["CE"].get("lastPrice") or 0.0
        if "PE" in rec:
            pe_map[s] = rec["PE"].get("lastPrice") or 0.0

    ce_rows = [
        {"label": "ATM CE",   "strike": atm,            "price": ce_map.get(atm,            0.0)},
        {"label": "ATM+1 CE", "strike": atm + step,     "price": ce_map.get(atm + step,     0.0)},
        {"label": "ATM+2 CE", "strike": atm + 2 * step, "price": ce_map.get(atm + 2 * step, 0.0)},
    ]
    pe_rows = [
        {"label": "ATM PE",   "strike": atm,            "price": pe_map.get(atm,            0.0)},
        {"label": "ATM-1 PE", "strike": atm - step,     "price": pe_map.get(atm - step,     0.0)},
        {"label": "ATM-2 PE", "strike": atm - 2 * step, "price": pe_map.get(atm - 2 * step, 0.0)},
    ]

    ce_sum  = sum(r["price"] for r in ce_rows)
    pe_sum  = sum(r["price"] for r in pe_rows)
    ce_sqrt = math.sqrt(ce_sum) if ce_sum > 0 else 0.0
    pe_sqrt = math.sqrt(pe_sum) if pe_sum > 0 else 0.0

    return dict(spot=spot, atm=atm, expiry=expiry,
                ce_rows=ce_rows, pe_rows=pe_rows,
                ce_sum=ce_sum,   pe_sum=pe_sum,
                ce_sqrt=ce_sqrt, pe_sqrt=pe_sqrt,
                bearish=ce_sqrt > pe_sqrt)

def render_table(r: dict, symbol: str):
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
        <th>{symbol} &nbsp;|&nbsp; ATM: {r['atm']} &nbsp;|&nbsp; Exp: {r['expiry']}</th>
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

# ── Header ─────────────────────────────────────────────────────
now  = datetime.now(IST)
mkt  = now.weekday() < 5 and (9, 15) <= (now.hour, now.minute) <= (15, 30)
dot  = "🟢 Market open" if mkt else "🔴 Market closed"

st.markdown(
    f"<h2 style='color:white;margin-bottom:0;'>📊 ATM Options Tracker</h2>"
    f"<p style='color:#888;font-size:12px;margin-top:4px;'>"
    f"{dot} &nbsp;·&nbsp; IST: {now.strftime('%d %b %Y &nbsp; %H:%M:%S')}"
    f" &nbsp;·&nbsp; ATM = last 3-min candle open"
    f" &nbsp;·&nbsp; Auto-refresh every 3 min</p>",
    unsafe_allow_html=True)

# ── Two-column layout ──────────────────────────────────────────
col1, col2 = st.columns(2)

for col, sym in [(col1, "NIFTY"), (col2, "BANKNIFTY")]:
    with col:
        # Step 1 — 3-min open (yfinance, always works)
        candle_open, live_spot, candle_time = get_3min_open(sym)

        if candle_open is None:
            st.markdown(
                f"<div class='err-box'>⚠️ {sym}: Yahoo Finance unavailable.<br>"
                f"<small>{candle_time}</small></div>",
                unsafe_allow_html=True)
            continue

        # Step 2 — NSE option chain
        chain, err = fetch_chain(sym)

        if err or chain is None:
            atm_display = snap(candle_open, STRIKE_STEP[sym])
            st.markdown(
                f"<div class='err-box'>⚠️ {sym}: NSE option chain unavailable.<br>"
                f"<small>{err}</small><br>"
                f"ATM would be <b>{atm_display}</b> (3-min open ₹{candle_open:,.2f} at {candle_time})"
                f" — option prices will load when NSE responds.</div>",
                unsafe_allow_html=True)
            continue

        # Step 3 — Parse using 3-min open as ATM base
        try:
            result = parse(chain, sym, atm_base=candle_open)
        except Exception as e:
            st.markdown(
                f"<div class='err-box'>⚠️ {sym}: Parse error — {e}</div>",
                unsafe_allow_html=True)
            continue

        # Step 4 — Render
        st.markdown(
            f"<div class='card'>"
            f"<div class='spot-lbl'>{sym} Live Spot</div>"
            f"<div class='spot-val'>₹ {live_spot:,.2f}</div>"
            f"<div class='open-val'>"
            f"Last 3-min open: ₹ {candle_open:,.2f} ({candle_time} IST)"
            f" &nbsp;→&nbsp; ATM locked: {result['atm']}"
            f"</div></div>",
            unsafe_allow_html=True)

        render_table(result, sym)

st.markdown(
    f"<p class='refresh-note'>Updated: {now.strftime('%H:%M:%S IST')}"
    f" &nbsp;·&nbsp; Sources: Yahoo Finance (3-min open) + NSE India (option prices)</p>",
    unsafe_allow_html=True)

# ── Auto-refresh every 3 min ───────────────────────────────────
time.sleep(180)
st.rerun()
