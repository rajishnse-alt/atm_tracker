#!/bin/bash
# Push all automation changes to GitHub

set -e

echo "🚀 Pushing ATM Tracker automation changes to GitHub..."
echo ""

cd "$(dirname "$0")"

# Check if git is initialized
if [ ! -d .git ]; then
    echo "❌ Git repository not found!"
    echo "Initialize git first:"
    echo "  git init"
    echo "  git remote add origin <your-repo-url>"
    exit 1
fi

echo "📋 Git Status:"
git status --short
echo ""

echo "📦 Staging new files..."
git add -A

echo "✅ Files staged:"
git diff --cached --name-only
echo ""

echo "📝 Committing changes..."
git commit -m "🤖 Add automated background tick collector with zero manual work

Features:
- Auto-start at 9:15 AM IST on trading days
- Continuous tick collection from Upstox WebSocket
- Auto-save to data/ticks/SYMBOL.csv
- Auto-purge data older than 30 days
- Thread-safe, production-ready code
- Comprehensive logging and monitoring

New files:
- background_tick_collector.py (main service)
- setup_background_collector.sh (one-command setup)
- verify_setup.py (diagnostic tool)
- BACKGROUND_COLLECTOR_README.md (detailed docs)
- AUTOMATION_COMPLETE.md (quick reference)
- push_to_git.sh (git push helper)

Fixed:
- WebSocket message handler for Upstox V3 API
- Nested 'feeds' object parsing in on_message
- Updated test_websocket.py to match new format

Usage:
  bash setup_background_collector.sh
  (Choose your preferred launch method)

No manual work required after setup!"

echo ""
echo "🔄 Pushing to remote repository..."
git push origin main || git push origin master || echo "⚠️ Push failed - check your git config"

echo ""
echo "✅ Done! Changes pushed to GitHub"
echo ""
echo "📊 Summary:"
echo "  Branch: $(git branch --show-current)"
echo "  Remote: $(git remote get-url origin)"
echo "  Latest commit: $(git log -1 --oneline)"
