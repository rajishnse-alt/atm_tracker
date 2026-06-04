# 🔍 WebSocket Debug Guide - Diagnostics & Troubleshooting

**Issue**: WebSocket shows "Started" but receiving 0 messages

---

## ✅ What I Fixed

I've added **detailed diagnostic logging** to track exactly where the WebSocket is failing:

1. **Enhanced Logging** - INFO level shows all WebSocket activity
2. **Detailed Callbacks** - Each step logs what it's doing:
   - on_open: When connection established + subscription sent
   - on_message: Every message received + type + data
   - on_error: Any errors
   - on_close: When connection closes

3. **Live Debug Panel** - See logs in real-time in Streamlit UI
4. **Message Inspection** - Shows exact message structure received

---

## 🚀 How to Debug

### Step 1: Restart Streamlit App
```bash
# Kill old session
pkill -f "streamlit run"

# Restart with fresh session
streamlit run app.py
```

### Step 2: Login with Upstox Token
- Click "CONNECT"
- Complete Upstox login
- Go to sidebar → "🔌 Real-Time Data"

### Step 3: Watch the Debug Logs
In the **"🔍 DEBUG LOG - SMAs & WebSocket Candles"** expander:
- Scroll to **"📋 Live Debug Logs"** section at the bottom
- You'll see real-time WebSocket activity

---

## 📊 What to Look For

### If you see:
```
🔗 [NIFTY] WebSocket OPEN - Sending subscription...
📤 [NIFTY] Sending payload: {"guid": "...", "method": "sub", ...}
✅ [NIFTY] Subscription sent to NSE_INDEX|Nifty 50
```

✅ **GOOD** - WebSocket connected and subscription was sent!

---

### If you then see:
```
✅ [NIFTY] market_info received: NSE
📡 [NIFTY] live_feed - Available feeds: ['NSE_INDEX|Nifty 50']
✅ [NIFTY] Tick #1: 24500.25 | Vol: 1000000
```

✅ **PERFECT** - WebSocket is receiving ticks! Everything works!

---

### If you see NOTHING:
```
🔗 [NIFTY] WebSocket OPEN - Sending subscription...
📤 [NIFTY] Sending payload: {...}
✅ [NIFTY] Subscription sent to NSE_INDEX|Nifty 50
(then silence - no more messages)
```

⚠️ **PROBLEM** - WebSocket connected but not receiving messages from Upstox

**Causes:**
1. Token is invalid or expired
2. Market is closed
3. Instrument key format is wrong
4. Upstox API has an issue

**Solution:**
- Get fresh token from app (expires daily)
- Check market hours (9:15-15:30 IST, Mon-Fri)
- Check instrument key is correct: `NSE_INDEX|Nifty 50`

---

### If you see:
```
❌ WebSocket ERROR for NIFTY: Connection refused
```

⚠️ **PROBLEM** - Cannot connect to Upstox WebSocket

**Causes:**
1. Network issue
2. Upstox API down
3. Invalid WebSocket URL

**Solution:**
- Check internet connection
- Try again in a moment
- Check Upstox API status

---

### If you see:
```
❌ JSON decode error for NIFTY: Expecting value
   Raw message: Some garbage data
```

⚠️ **PROBLEM** - Receiving data but can't parse as JSON

**Causes:**
1. Upstox API changed message format
2. Binary data instead of JSON
3. Compression or encoding issue

**Solution:**
- Check Upstox API docs
- Contact Upstox support

---

## 🔧 Detailed Log Interpretation

### Message Flow (if working):
```
1. on_open called
   └─ WebSocket connection established

2. on_open sends subscription payload
   └─ Tells Upstox what data to send

3. on_message called (first message)
   └─ Type: market_info
   └─ Contains segment status

4. on_message called (continuous)
   └─ Type: live_feed
   └─ Contains: {"feeds": {"NSE_INDEX|Nifty 50": {ltp, volume, oi, ...}}}
   └─ Processed as tick

5. Repeat step 4 for every tick
   └─ ~1000-5000 per second during market hours
```

### If stuck after step 2:
```
1. ✅ on_open called
2. ✅ Subscription sent
3. ❌ No more on_message calls

This means:
- WebSocket connection established OK
- Subscription was sent OK
- But Upstox not sending data back

Likely causes:
- Invalid subscription payload format
- Token invalid/expired
- Market closed
- Instrument key wrong
```

---

## 🎯 Quick Checklist

- [ ] Restarted Streamlit app
- [ ] Got fresh token from Upstox
- [ ] It's during market hours (9:15-15:30 IST, Mon-Fri)
- [ ] It's a trading day (Mon-Fri)
- [ ] Watching the "📋 Live Debug Logs" section
- [ ] Internet connection is working
- [ ] Token is not expired

---

## 🔧 If You Need to Check Code

The WebSocket code is in `app.py`:
- Function: `_start_upstox_websocket()` (line ~2407)
- on_open callback: Sends subscription
- on_message callback: Processes ticks
- on_error callback: Logs errors
- on_close callback: Logs disconnection

All callbacks now have detailed logging at INFO level.

---

## 📝 Sample Output (Expected)

When working correctly, you should see:
```
09:15:23 [INFO] Got WebSocket URL for NIFTY: wss://api.upstox.com/...
09:15:23 [INFO] 🔌 WebSocket thread started for NIFTY
09:15:25 [INFO] 🔗 [NIFTY] WebSocket OPEN - Sending subscription...
09:15:25 [INFO] 📤 [NIFTY] Sending payload: {"guid": "...", "method": "sub", ...}
09:15:25 [INFO] ✅ [NIFTY] Subscription sent to NSE_INDEX|Nifty 50
09:15:26 [INFO] 📨 [NIFTY] RECEIVED MESSAGE (length: 123)
09:15:26 [INFO] 📊 [NIFTY] Parsed JSON - Type: market_info, Keys: ['type', 'segment', ...]
09:15:26 [INFO] ✅ [NIFTY] market_info received: NSE
09:15:26 [INFO] 📨 [NIFTY] RECEIVED MESSAGE (length: 456)
09:15:26 [INFO] 📊 [NIFTY] Parsed JSON - Type: live_feed, Keys: ['type', 'feeds', 'timestamp']
09:15:26 [INFO] 📡 [NIFTY] live_feed - Available feeds: ['NSE_INDEX|Nifty 50']
09:15:26 [INFO] ✅ [NIFTY] Tick #1: 24500.50 | Vol: 1000000 | OI: 0
```

---

## 🆘 If Still Not Working

1. **Collect logs**: Screenshot the "📋 Live Debug Logs" section
2. **Check what you see**:
   - Does it say "RECEIVED MESSAGE"?
   - What's the message type?
   - Are there any ERROR lines?
3. **Check basics**:
   - Market hours? (9:15-15:30 IST, Mon-Fri)
   - Trading day? (Mon-Fri, not holiday)
   - Token fresh? (expires daily)
4. **Restart and retry**:
   - Kill app: `pkill -f streamlit`
   - Get fresh token from Upstox
   - Restart: `streamlit run app.py`

---

## 📞 Debug Output Locations

### In Streamlit UI:
- Sidebar → "🔌 Real-Time Data"
- "🔍 DEBUG LOG - SMAs & WebSocket Candles"
- Scroll to "📋 Live Debug Logs" (at bottom)

### In Terminal/Server Logs:
```bash
# If running locally
# Logs appear in terminal where you ran: streamlit run app.py

# If running in background
tail -f background_collector.log
```

---

**Status**: 🟡 **Diagnostics Added**

Next: 
1. Restart Streamlit
2. Login with Upstox
3. Watch the "📋 Live Debug Logs"
4. Report what you see

This will tell us exactly where the WebSocket issue is! 🔍
