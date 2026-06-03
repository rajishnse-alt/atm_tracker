# 🤖 ATM Tracker Background Tick Collector

**Zero-manual work automated tick collection** that runs 24/7, collecting Upstox market ticks automatically.

## ⚡ Quick Start (2 minutes)

### 1. Get Your Upstox Token

```bash
# Option A: From the Streamlit app
# 1. Run: streamlit run app.py
# 2. Click "CONNECT" to login with Upstox
# 3. Copy the token from sidebar → "🔌 Real-Time Data" → Debug panel

# Option B: From Upstox website
# Visit: https://upstox.com/developer/ → Copy OAuth token
```

### 2. Run Setup (ONE command)

```bash
cd ~/Documents/Trading/githuh_only_Projects/atm_tracker
bash setup_background_collector.sh
```

That's it! The setup script will:
- ✅ Check Python dependencies
- ✅ Create virtual environment
- ✅ Save your Upstox token securely
- ✅ Test the API connection
- ✅ Ask how you want to run it (screen/nohup/systemd)
- ✅ Start the collector

### 3. Verify It's Working

```bash
# Check logs
tail -f ~/Documents/Trading/githuh_only_Projects/atm_tracker/background_collector.log

# Or view the screen session
screen -r atm-collector
```

## 📋 What It Does

### Automatically
- ✅ **Starts at 9:15 AM IST** on trading days (Mon-Fri)
- ✅ **Collects every tick** from Upstox WebSocket
- ✅ **Saves to CSV files**: `data/ticks/NIFTY.csv`, `data/ticks/BANKNIFTY.csv`
- ✅ **Auto-purges data** older than 30 days
- ✅ **Stops at 15:30 IST** (market close)
- ✅ **Resumes next trading day** at 9:15 AM
- ✅ **Handles token refresh** gracefully
- ✅ **Logs everything** to `background_collector.log`

### Data Collected (per tick)
| Field | Description |
|-------|-------------|
| timestamp | ISO format with IST timezone |
| open | LTP at tick time |
| high | LTP at tick time |
| low | LTP at tick time |
| close | LTP at tick time |
| volume | Total volume |
| oi | Open Interest |
| bid | Bid price |
| ask | Ask price |
| bid_qty | Bid quantity |
| ask_qty | Ask quantity |
| type | 'tick' (regular ticks) |

## 🚀 Different Launch Methods

### Option 1: Screen (Recommended for Testing)
```bash
bash setup_background_collector.sh
# Choose option 1

# View it
screen -r atm-collector

# Detach (leaves it running)
Ctrl+A then D

# Stop it
screen -S atm-collector -X quit
```

### Option 2: Nohup (Background, survives logout)
```bash
bash setup_background_collector.sh
# Choose option 2

# View logs
tail -f logs/collector.log

# Find and kill it
ps aux | grep background_tick_collector
kill <PID>
```

### Option 3: Systemd (Production, auto-restart)
```bash
bash setup_background_collector.sh
# Choose option 3

# Then run the suggested commands:
mkdir -p ~/.config/systemd/user/
cp atm-collector.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable atm-collector
systemctl --user start atm-collector

# View status
systemctl --user status atm-collector

# View logs
journalctl --user -u atm-collector -f
```

## 🔍 Manual Setup (if setup script doesn't work)

### Step 1: Create Virtual Environment
```bash
cd ~/Documents/Trading/githuh_only_Projects/atm_tracker
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
pip install python-dotenv
```

### Step 3: Create .env File
```bash
cat > .env << EOF
UPSTOX_ACCESS_TOKEN=your_token_here
EOF
chmod 600 .env
```

### Step 4: Test It
```bash
python3 verify_setup.py
python3 background_tick_collector.py
```

### Step 5: Run in Screen
```bash
screen -S atm-collector
source venv/bin/activate
python3 background_tick_collector.py
# Ctrl+A then D to detach
```

## 📊 Output & Monitoring

### Log File
```bash
tail -f background_collector.log
```

Output:
```
2026-06-03 09:15:00 [INFO] 🟢 Market is OPEN - Starting tick collection...
2026-06-03 09:15:05 [INFO] 🔌 WebSocket thread started for NIFTY
2026-06-03 09:15:10 [INFO] ✅ [NIFTY] Tick #100: 24500.25 | Vol: 1000000
2026-06-03 09:15:15 [INFO] ✅ [BANKNIFTY] Tick #100: 45000.50 | Vol: 2000000
```

### Data Files
```bash
# View collected data
ls -lh data/ticks/

# Example output:
# -rw-r--r-- 1 user user 5.2M Jun 03 15:30 NIFTY.csv
# -rw-r--r-- 1 user user 4.8M Jun 03 15:30 BANKNIFTY.csv

# View first few ticks
head -20 data/ticks/NIFTY.csv
```

### Screen Session
```bash
# View live output
screen -r atm-collector

# Detach
Ctrl+A then D

# List all sessions
screen -ls
```

## ⚠️ Troubleshooting

### "UPSTOX_ACCESS_TOKEN not found"
```bash
# Create .env with your token
echo "UPSTOX_ACCESS_TOKEN=your_token_here" > .env
chmod 600 .env

# Or run setup script again
bash setup_background_collector.sh
```

### "Token is invalid or expired"
```bash
# Tokens expire after 24 hours
# Get a new one from the Streamlit app and update .env
echo "UPSTOX_ACCESS_TOKEN=new_token_here" > .env
```

### "No ticks being recorded"
```bash
# Check if it's market hours
date  # Should show 9:15-15:30 IST on Mon-Fri

# View the log
tail -50 background_collector.log

# Test manually
python3 verify_setup.py

# If API token fails, get a new token from the app
```

### "Too many open files"
```bash
# Increase file limits
ulimit -n 4096

# Or permanently in /etc/security/limits.conf
echo "* soft nofile 4096" | sudo tee -a /etc/security/limits.conf
```

### "Port already in use"
The collector doesn't use ports, but if you have another collector running:
```bash
# Find and stop it
ps aux | grep background_tick_collector
kill <PID>

# Or stop the screen session
screen -S atm-collector -X quit
```

## 🔐 Security Notes

- **Token in .env**: File is created with `chmod 600` (readable only by you)
- **Never commit .env**: Add to `.gitignore`
- **Token expiry**: Tokens expire daily, need to refresh from app
- **CSV data**: Contains no sensitive info, just market ticks

## 📈 Performance

- **Memory**: ~50-100 MB per symbol
- **Disk**: ~10-20 MB per trading day per symbol
- **Network**: Minimal (WebSocket keeps single connection)
- **CPU**: <1% during normal operation

## 🎯 Integration with Streamlit App

The Streamlit app (`app.py`) automatically:
1. Reads tick data from `data/ticks/NIFTY.csv` and `data/ticks/BANKNIFTY.csv`
2. Uses the collected ticks for 26.11% reversal levels
3. Updates SMAs with real-time data
4. No manual sync needed - data is shared via CSV files

## ✅ Verification Checklist

- [ ] Run `python3 verify_setup.py` - all tests pass
- [ ] See collector running: `ps aux | grep background_tick_collector`
- [ ] See tick data: `ls -lh data/ticks/`
- [ ] See logs: `tail -f background_collector.log`
- [ ] Open Streamlit app and see real-time data updating
- [ ] Check that 26.11% reversal levels use real-time highs/lows

## 📝 Logs & Monitoring

Logs are saved to: `background_collector.log`

You can monitor live:
```bash
# All messages
tail -f background_collector.log

# Only errors
tail -f background_collector.log | grep ERROR

# Only info
tail -f background_collector.log | grep INFO

# Only ticks (every 100)
tail -f background_collector.log | grep "Tick #"
```

## 🔄 Workflow (What Happens Automatically)

### At 9:14 AM IST
- Collector wakes up and checks if it's a trading day
- Verifies token is still valid

### At 9:15 AM IST (Market Open)
```
1. WebSocket connects to Upstox API
2. Subscribes to NIFTY and BANKNIFTY
3. Receives first "market_info" message
4. Starts receiving "live_feed" messages (ticks)
5. Each tick → logged to CSV file
6. Every 100 ticks → status logged
```

### During Market Hours (9:15-15:30)
- Ticks arrive continuously
- Each tick → logged to CSV within milliseconds
- Status check every 5 minutes
- Auto-purge old data (once per day)

### At 15:30 IST (Market Close)
- WebSocket closes gracefully
- Collector sleeps until next day
- Status: "🔴 Market is CLOSED"

### Overnight/Weekends
- Collector sleeps
- Calculates next market open time
- Waits for that time

## 🛠️ Advanced

### Run Multiple Symbols
Edit `background_tick_collector.py` and add to `INSTRUMENTS`:
```python
INSTRUMENTS = {
    "NIFTY": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "FINNIFTY": "NSE_INDEX|Nifty Financial Services",  # Add this
}
```

### Change Purge Period
Edit `background_tick_collector.py`, line ~330:
```python
purge_old_ticks(symbol, days=60)  # Keep 60 days instead of 30
```

### Change Log Level
Edit `background_tick_collector.py`, line ~46:
```python
logging.basicConfig(level=logging.DEBUG)  # Show debug messages
```

## 📞 Support

If something doesn't work:
1. Run `python3 verify_setup.py` to diagnose
2. Check `background_collector.log` for errors
3. Ensure token is fresh (get new one from Streamlit app)
4. Make sure it's market hours (9:15-15:30 IST, Mon-Fri)

---

**Status**: ✅ Production Ready  
**Last Updated**: June 2026  
**Upstox API Version**: V3  
