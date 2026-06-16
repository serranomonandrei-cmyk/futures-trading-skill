#!/bin/bash
# setup.sh — Futures Trading System Setup
# Run once: bash ~/.config/opencode/skills/futures-trading/setup.sh

set -e

echo "=== Futures Trading System Setup ==="
echo ""

# 1. Install ccxt
echo "[1/4] Installing ccxt..."
pip install ccxt python-dotenv 2>/dev/null || pip3 install ccxt python-dotenv

# 2. Create journal directory
echo "[2/4] Creating journal directory..."
mkdir -p ~/trading-journal

# 3. API key configuration
echo "[3/4] API Key Configuration"
ENV_FILE="$HOME/.config/opencode/skills/futures-trading/.env"

if [ -f "$ENV_FILE" ] && grep -q "YOUR_API_KEY_HERE" "$ENV_FILE" 2>/dev/null; then
    echo "Enter your Binance API key and secret:"
    read -p "API Key: " API_KEY
    read -sp "API Secret: " API_SECRET
    echo ""

    cat > "$ENV_FILE" << EOF
BINANCE_API_KEY=${API_KEY}
BINANCE_API_SECRET=${API_SECRET}
EOF

    chmod 600 "$ENV_FILE"
    echo "API keys saved."
elif [ -f "$ENV_FILE" ]; then
    echo "API keys already configured. Skipping."
else
    echo "Creating .env template..."
    cat > "$ENV_FILE" << 'EOF'
BINANCE_API_KEY=YOUR_API_KEY_HERE
BINANCE_API_SECRET=YOUR_API_SECRET_HERE
EOF
    chmod 600 "$ENV_FILE"
    echo "Please edit $ENV_FILE with your API keys."
fi

# 4. Verify installation
echo "[4/4] Verifying installation..."
python3 -c "import ccxt; print(f'ccxt version: {ccxt.__version__}')" 2>/dev/null || \
    python -c "import ccxt; print(f'ccxt version: {ccxt.__version__}')"

echo ""
echo "=== Setup Complete ==="
echo "Restart opencode to activate the trading system."
