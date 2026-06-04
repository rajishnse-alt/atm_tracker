# 🔐 Baked-In Token Setup (No Manual Work Every Time)

Now the app will use your token directly from secrets **without requiring manual OAuth every time**.

---

## ✅ How to Set It Up (One Time Only)

### Option 1: Local Setup (`.streamlit/secrets.toml`)

If running locally on your computer:

#### Step 1: Create secrets file
```bash
mkdir -p ~/.streamlit
nano ~/.streamlit/secrets.toml
```

#### Step 2: Add your token
```toml
[upstox]
api_key      = "your_api_key"
api_secret   = "your_api_secret"
redirect_uri = "https://yourapp.streamlit.app"
access_token = "your_upstox_access_token_here"
```

#### Step 3: Save and restart
- Save file (Ctrl+X, Y, Enter if using nano)
- Restart Streamlit: `streamlit run app.py`
- ✅ Token will be used automatically!

---

### Option 2: Streamlit Cloud (Secrets settings)

If running on Streamlit Cloud:

#### Step 1: Go to app settings
- Open your deployed Streamlit app
- Click "Settings" (gear icon)
- Select "Secrets"

#### Step 2: Add token
```
[upstox]
api_key      = "your_api_key"
api_secret   = "your_api_secret"
redirect_uri = "https://yourapp.streamlit.app"
access_token = "your_upstox_access_token_here"
```

#### Step 3: Save and reload
- Click "Save"
- Reload the app
- ✅ Token will be used automatically!

---

## 🔑 How to Get Your Access Token

### Method 1: From Upstox Website
1. Go to: https://upstox.com/developer/
2. Login to your account
3. Navigate to "My Apps"
4. Find your access token (should be a long string)
5. Copy it

### Method 2: From Streamlit App OAuth Flow
1. Open Streamlit app
2. Click "CONNECT"
3. Complete Upstox login
4. In sidebar → "🔌 Real-Time Data"
5. Copy the displayed access token
6. Add to secrets file

### Method 3: Get Fresh Token Daily
```bash
# If your token expires, get a new one from:
# https://upstox.com/developer/

# Then update secrets.toml:
nano ~/.streamlit/secrets.toml

# Change the access_token value
access_token = "new_token_here"

# Restart app
```

---

## 🎯 What You Get

### Before (Crap 🤮)
```
1. Run streamlit run app.py
2. Click "CONNECT" 
3. Go through Upstox OAuth
4. Wait for redirect
5. Finally can use app
6. Repeat every 24 hours!
```

### After (Clean ✨)
```
1. Run streamlit run app.py
2. ✅ App starts immediately with baked-in token
3. No manual login needed
4. Use app right away
5. Only update token in secrets when it expires
```

---

## 🔒 Security Notes

- ✅ Secrets file is **local only** (not in git)
- ✅ Secrets file is `.gitignore`d automatically
- ✅ On Streamlit Cloud, encrypted and secure
- ✅ Token in `secrets.toml` never committed to repo
- ✅ Only you can see it

### Never:
- ❌ Commit `secrets.toml` to git
- ❌ Share your `secrets.toml` file
- ❌ Push token to GitHub
- ❌ Hardcode token in `app.py`

**Always** use secrets file or Streamlit Secrets!

---

## 📝 Complete `secrets.toml` Example

```toml
# Upstox Configuration
[upstox]
api_key      = "your_upstox_api_key_here"
api_secret   = "your_upstox_api_secret_here"
redirect_uri = "https://yourapp.streamlit.app"
access_token = "your_upstox_access_token_here"

# Optional: Add more config
[app]
debug = true
update_interval = 5
```

---

## ✅ Verification

After setup, when you run the app:

✅ **Should see**: 
```
✅ Using baked-in access token from secrets
```

❌ **Should NOT see**:
```
CONNECT →
One click per trading day
```

If you still see the login button, check:
1. Did you add `access_token` to `[upstox]` section?
2. Did you restart Streamlit?
3. Is the file format correct (TOML, not JSON)?

---

## 🔄 Token Expiry

Upstox tokens expire after **24 hours**.

### When expired:
- App will show login button again
- Get fresh token from Upstox
- Update `secrets.toml`
- Restart app

### Or automate it:
Get a new token daily with cron job:
```bash
# crontab -e
0 9 * * * curl https://api.upstox.com/auth/token -X POST ... | jq .token
```

---

## 🚀 Quick Setup (Copy-Paste)

### Step 1: Create file
```bash
mkdir -p ~/.streamlit
cat > ~/.streamlit/secrets.toml << 'EOF'
[upstox]
api_key      = "YOUR_API_KEY"
api_secret   = "YOUR_API_SECRET"
redirect_uri = "https://yourapp.streamlit.app"
access_token = "YOUR_ACCESS_TOKEN"
EOF
```

### Step 2: Update with your values
```bash
nano ~/.streamlit/secrets.toml
```

### Step 3: Restart app
```bash
pkill -f streamlit
streamlit run app.py
```

### Step 4: Verify
- App should start without "CONNECT" button
- Should see: "✅ Using baked-in access token from secrets"

---

## 📞 Troubleshooting

### "Still asking to connect"
- Check if `[upstox]` section has `access_token`
- Check file location: `~/.streamlit/secrets.toml`
- Restart Streamlit: `pkill -f streamlit && streamlit run app.py`

### "Token not recognized"
- Get fresh token from Upstox
- Check for extra spaces or quotes in `secrets.toml`
- Use proper TOML format:
  ```toml
  access_token = "actual_token_here"  ✅
  access_token = actual_token_here    ❌ (missing quotes)
  ```

### "WebSocket still showing 0 messages"
- Token is baked in ✅
- Now WebSocket debugging should work
- Check "📋 Live Debug Logs" in debug panel
- Follow WEBSOCKET_DEBUG_GUIDE.md

---

## 🎉 Next Steps

1. **Add token to secrets** (above)
2. **Restart app** 
3. **Check WebSocket logs**
4. **Enjoy automatic tick collection!** 🚀

---

**Status**: ✅ Baked-in token ready  
**Manual work**: ❌ ZERO (except updating token every 24h)  
**Setup time**: ~2 minutes  
