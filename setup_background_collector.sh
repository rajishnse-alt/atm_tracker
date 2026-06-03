#!/bin/bash
# Setup and launch the background tick collector
# This script handles everything automatically

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COLLECTOR_SCRIPT="$PROJECT_DIR/background_tick_collector.py"
ENV_FILE="$PROJECT_DIR/.env"
VENV_DIR="$PROJECT_DIR/venv"
LOG_DIR="$PROJECT_DIR/logs"
SCREEN_SESSION="atm-collector"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   ATM Tracker - Background Tick Collector Setup${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}\n"

# ─────────────────────────────────────────────
# STEP 1: Check Python
# ─────────────────────────────────────────────
echo -e "${YELLOW}[1/5] Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}\n"

# ─────────────────────────────────────────────
# STEP 2: Create virtual environment
# ─────────────────────────────────────────────
echo -e "${YELLOW}[2/5] Setting up virtual environment...${NC}"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# ─────────────────────────────────────────────
# STEP 3: Install dependencies
# ─────────────────────────────────────────────
echo -e "\n${YELLOW}[3/5] Installing dependencies...${NC}"
pip install -q --upgrade pip setuptools wheel

# Create a minimal requirements file for the collector
cat > "$PROJECT_DIR/requirements-collector.txt" << 'EOF'
requests>=2.31.0
pytz>=2024.1
websocket-client>=1.7.0
python-dotenv>=1.0.0
EOF

pip install -q -r "$PROJECT_DIR/requirements-collector.txt"
echo -e "${GREEN}✅ Dependencies installed${NC}"

# ─────────────────────────────────────────────
# STEP 4: Setup .env file with token
# ─────────────────────────────────────────────
echo -e "\n${YELLOW}[4/5] Setting up configuration...${NC}"

if [ -f "$ENV_FILE" ]; then
    # Check if token is already set
    if grep -q "^UPSTOX_ACCESS_TOKEN=" "$ENV_FILE" && ! grep -q "UPSTOX_ACCESS_TOKEN=YOUR_TOKEN_HERE" "$ENV_FILE"; then
        echo -e "${GREEN}✅ Configuration file already exists with valid token${NC}"
        # Show the token (masked)
        TOKEN=$(grep "^UPSTOX_ACCESS_TOKEN=" "$ENV_FILE" | cut -d'=' -f2)
        TOKEN_PREVIEW="${TOKEN:0:20}...${TOKEN: -10}"
        echo -e "   Token: $TOKEN_PREVIEW"
    else
        echo -e "${YELLOW}⚠️  Configuration file exists but token is missing/placeholder${NC}"
        read -sp "Enter your Upstox access token: " TOKEN
        echo ""
        echo "UPSTOX_ACCESS_TOKEN=$TOKEN" > "$ENV_FILE"
        echo -e "${GREEN}✅ Token saved to .env${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  No .env file found${NC}"
    echo -e "To get your Upstox token:"
    echo -e "  1. Open the ATM Tracker app in Streamlit"
    echo -e "  2. Click 'CONNECT' to login with Upstox"
    echo -e "  3. In the sidebar, expand '🔌 Real-Time Data'"
    echo -e "  4. Copy the access token from the debug panel\n"

    read -sp "Enter your Upstox access token: " TOKEN
    echo ""

    if [ -z "$TOKEN" ]; then
        echo -e "${RED}❌ No token provided. Please run this script again with your token.${NC}"
        exit 1
    fi

    echo "UPSTOX_ACCESS_TOKEN=$TOKEN" > "$ENV_FILE"
    chmod 600 "$ENV_FILE"  # Restrict permissions for security
    echo -e "${GREEN}✅ Configuration saved to .env${NC}"
fi

# ─────────────────────────────────────────────
# STEP 5: Test the collector
# ─────────────────────────────────────────────
echo -e "\n${YELLOW}[5/5] Testing collector...${NC}"
mkdir -p "$LOG_DIR"

# Run setup verification
python3 "$COLLECTOR_SCRIPT" 2>&1 | head -20 || true

echo -e "\n${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}\n"

# ─────────────────────────────────────────────
# STEP 6: Ask about launch method
# ─────────────────────────────────────────────
echo -e "${BLUE}How would you like to run the background collector?${NC}\n"

echo "  1) ${GREEN}screen${NC} (recommended for interactive testing)"
echo "  2) ${GREEN}nohup${NC} (runs in background, survives logout)"
echo "  3) ${GREEN}systemd${NC} (auto-restart on reboot, production)"
echo "  4) Just show me how to run it manually"
echo ""
read -p "Choose (1-4): " CHOICE

case $CHOICE in
    1)
        echo -e "\n${YELLOW}Starting collector in screen session...${NC}"

        # Check if screen is installed
        if ! command -v screen &> /dev/null; then
            echo -e "${YELLOW}⚠️  screen not found. Installing...${NC}"
            sudo apt-get update > /dev/null 2>&1 && sudo apt-get install -y screen > /dev/null 2>&1 || true
        fi

        # Create a screen session
        if screen -list | grep -q "$SCREEN_SESSION"; then
            screen -S "$SCREEN_SESSION" -X quit
        fi

        # Create screen session with the collector
        screen -S "$SCREEN_SESSION" -d -m bash -c "cd '$PROJECT_DIR' && source '$VENV_DIR/bin/activate' && python3 '$COLLECTOR_SCRIPT'; bash"

        sleep 1
        echo -e "${GREEN}✅ Collector started in screen session: ${YELLOW}$SCREEN_SESSION${NC}"
        echo -e "\nTo view the collector output:"
        echo -e "  ${YELLOW}screen -r $SCREEN_SESSION${NC}"
        echo ""
        echo -e "To detach without stopping:"
        echo -e "  Press ${YELLOW}Ctrl+A${NC} then ${YELLOW}D${NC}"
        echo ""
        echo -e "To stop the collector:"
        echo -e "  ${YELLOW}screen -S $SCREEN_SESSION -X quit${NC}\n"
        ;;

    2)
        echo -e "\n${YELLOW}Starting collector with nohup...${NC}"
        nohup bash -c "cd '$PROJECT_DIR' && source '$VENV_DIR/bin/activate' && python3 '$COLLECTOR_SCRIPT'" > "$LOG_DIR/collector.log" 2>&1 &

        PID=$!
        echo -e "${GREEN}✅ Collector started (PID: $PID)${NC}"
        echo ""
        echo -e "To view live logs:"
        echo -e "  ${YELLOW}tail -f $LOG_DIR/collector.log${NC}"
        echo ""
        echo -e "To stop the collector:"
        echo -e "  ${YELLOW}kill $PID${NC}\n"
        ;;

    3)
        echo -e "\n${YELLOW}Setting up systemd service...${NC}"

        SERVICE_FILE="/etc/systemd/user/atm-collector.service"
        SERVICE_CONTENT="[Unit]
Description=ATM Tracker Background Tick Collector
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$VENV_DIR/bin/python3 $COLLECTOR_SCRIPT
Restart=always
RestartSec=10

[Install]
WantedBy=default.target"

        echo "$SERVICE_FILE:"
        echo "$SERVICE_CONTENT" | tee "$PROJECT_DIR/atm-collector.service" > /dev/null

        echo -e "\n${YELLOW}To enable the service, run:${NC}"
        echo -e "  ${YELLOW}mkdir -p ~/.config/systemd/user/${NC}"
        echo -e "  ${YELLOW}cp $PROJECT_DIR/atm-collector.service ~/.config/systemd/user/${NC}"
        echo -e "  ${YELLOW}systemctl --user daemon-reload${NC}"
        echo -e "  ${YELLOW}systemctl --user enable atm-collector${NC}"
        echo -e "  ${YELLOW}systemctl --user start atm-collector${NC}"
        echo ""
        echo -e "${YELLOW}To view logs:${NC}"
        echo -e "  ${YELLOW}journalctl --user -u atm-collector -f${NC}\n"
        ;;

    4)
        echo -e "\n${YELLOW}Manual run command:${NC}"
        echo -e "  ${YELLOW}cd $PROJECT_DIR${NC}"
        echo -e "  ${YELLOW}source $VENV_DIR/bin/activate${NC}"
        echo -e "  ${YELLOW}python3 background_tick_collector.py${NC}\n"
        ;;

    *)
        echo -e "${RED}Invalid choice${NC}\n"
        ;;
esac

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}The collector will:${NC}"
echo -e "  ✅ Start automatically at 9:15 AM IST on trading days (Mon-Fri)"
echo -e "  ✅ Collect all Upstox ticks for NIFTY and BANKNIFTY"
echo -e "  ✅ Save ticks to: $PROJECT_DIR/data/ticks/"
echo -e "  ✅ Auto-purge data older than 30 days"
echo -e "  ✅ Resume collection after token refresh"
echo -e ""
echo -e "${GREEN}Data files:${NC}"
echo -e "  📊 $PROJECT_DIR/data/ticks/NIFTY.csv"
echo -e "  📊 $PROJECT_DIR/data/ticks/BANKNIFTY.csv"
echo -e "  📝 $PROJECT_DIR/background_collector.log"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}\n"
