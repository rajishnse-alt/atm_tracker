#!/bin/bash
# Copy-paste these commands to push to GitHub

# ═══════════════════════════════════════════════════════════
# OPTION 1: AUTOMATIC (ONE COMMAND) - RECOMMENDED
# ═══════════════════════════════════════════════════════════

cd ~/Documents/Trading/githuh_only_Projects/atm_tracker && bash push_to_git.sh

# ═══════════════════════════════════════════════════════════
# OPTION 2: MANUAL STEPS
# ═══════════════════════════════════════════════════════════

# Step 1: Go to project directory
cd ~/Documents/Trading/githuh_only_Projects/atm_tracker

# Step 2: Check status
git status

# Step 3: Stage files (exclude .env)
git add -A
git reset .env

# Step 4: Verify what's staged
git diff --cached --name-only

# Step 5: Commit
git commit -m "🤖 Add automated background tick collector with zero manual work

Features:
- Auto-start at 9:15 AM IST on trading days
- Continuous WebSocket tick collection
- Auto-save to data/ticks/SYMBOL.csv
- Auto-purge data older than 30 days
- Production-ready with logging

New files:
- background_tick_collector.py (main service)
- setup_background_collector.sh (setup wizard)
- verify_setup.py (diagnostic tool)
- BACKGROUND_COLLECTOR_README.md (full documentation)
- AUTOMATION_COMPLETE.md (overview)
- 00_START_HERE.md (quick start)
- GIT_PUSH_INSTRUCTIONS.md (git guide)

Fixed:
- WebSocket message parser for Upstox V3 API
- Nested 'feeds' object handling
- Updated test_websocket.py"

# Step 6: Push to GitHub
git push origin main

# If above fails, try:
git push origin master

# ═══════════════════════════════════════════════════════════
# OPTION 3: VERIFY AFTER PUSH
# ═══════════════════════════════════════════════════════════

# Show latest commit
git log -1 --oneline

# Show all files in latest commit
git diff-tree --no-commit-id --name-only -r HEAD

# Verify push successful
git status

# ═══════════════════════════════════════════════════════════
# IF SOMETHING GOES WRONG
# ═══════════════════════════════════════════════════════════

# Check your git config
git config --list

# Add remote if missing
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# List remotes
git remote -v

# Check default branch
git branch -a

# See commit history
git log --oneline | head -10

# ═══════════════════════════════════════════════════════════
# IF YOU NEED TO FIX SOMETHING BEFORE PUSH
# ═══════════════════════════════════════════════════════════

# Undo staging
git reset HEAD <filename>

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (lose changes)
git reset --hard HEAD~1

# ═══════════════════════════════════════════════════════════
# RECOMMENDED: JUST RUN THIS
# ═══════════════════════════════════════════════════════════

cd ~/Documents/Trading/githuh_only_Projects/atm_tracker && bash push_to_git.sh
