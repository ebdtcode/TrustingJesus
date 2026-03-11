#!/usr/bin/env bash
#
# Set up the sermon monitor on a local VM (Ubuntu/Debian).
#
# Prerequisites:
#   - Git repo cloned to /home/devos/prayer_trusting_Jesus
#   - Python 3.10+ installed
#   - Internet access
#
# Usage:
#   chmod +x tools/setup_vm.sh
#   sudo ./tools/setup_vm.sh
#

set -euo pipefail

DEPLOY_DIR="/home/devos/prayer_trusting_Jesus"
TOOLS_DIR="$DEPLOY_DIR/tools"
USER="devos"

echo "=== Sermon Monitor VM Setup ==="

# --- 1. Install system dependencies ---
echo ""
echo ">>> Installing system packages..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv ffmpeg curl git

# --- 2. Install yt-dlp ---
echo ""
echo ">>> Installing yt-dlp..."
if ! command -v yt-dlp &>/dev/null; then
    pip3 install --break-system-packages yt-dlp 2>/dev/null || pip3 install yt-dlp
    echo "    yt-dlp installed: $(yt-dlp --version)"
else
    echo "    yt-dlp already installed: $(yt-dlp --version)"
    echo "    Updating..."
    pip3 install --upgrade --break-system-packages yt-dlp 2>/dev/null || pip3 install --upgrade yt-dlp
fi

# --- 3. Install Python dependencies ---
echo ""
echo ">>> Installing Python packages..."
pip3 install --break-system-packages requests azure-storage-blob 2>/dev/null \
    || pip3 install requests azure-storage-blob

# --- 4. Create log directory ---
echo ""
echo ">>> Creating log directory..."
mkdir -p /var/log/sermon-monitor
chown "$USER:$USER" /var/log/sermon-monitor

# --- 5. Create env file from template if missing ---
if [ ! -f "$TOOLS_DIR/sermon_monitor.env" ]; then
    echo ""
    echo ">>> Creating sermon_monitor.env from template..."
    cp "$TOOLS_DIR/sermon_monitor.env.template" "$TOOLS_DIR/sermon_monitor.env"
    chown "$USER:$USER" "$TOOLS_DIR/sermon_monitor.env"
    chmod 600 "$TOOLS_DIR/sermon_monitor.env"
    echo "    IMPORTANT: Edit $TOOLS_DIR/sermon_monitor.env with your credentials!"
fi

# --- 6. Install systemd units ---
echo ""
echo ">>> Installing systemd service and timer..."
cp "$TOOLS_DIR/systemd/sermon-monitor.service" /etc/systemd/system/
cp "$TOOLS_DIR/systemd/sermon-monitor.timer" /etc/systemd/system/
systemctl daemon-reload

# --- 7. Enable and start timer ---
echo ""
echo ">>> Enabling sermon-monitor timer..."
systemctl enable sermon-monitor.timer
systemctl start sermon-monitor.timer

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Status:"
systemctl list-timers sermon-monitor.timer --no-pager
echo ""
echo "Next steps:"
echo "  1. Edit credentials:  nano $TOOLS_DIR/sermon_monitor.env"
echo "  2. Export YouTube cookies (see below)"
echo "  3. Test manually:     sudo -u $USER python3 $TOOLS_DIR/sermon_monitor.py --dry-run"
echo "  4. Run once:          sudo -u $USER python3 $TOOLS_DIR/sermon_monitor.py"
echo "  5. Check logs:        journalctl -u sermon-monitor -f"
echo ""
echo "=== Cookie Setup ==="
echo ""
echo "Option A — Export cookies from your Mac (recommended for headless VM):"
echo "  On your Mac:"
echo "    yt-dlp --cookies-from-browser chrome \\"
echo "      --cookies /tmp/youtube_cookies.txt \\"
echo "      --skip-download 'https://youtube.com'"
echo "    scp /tmp/youtube_cookies.txt $USER@<vm-ip>:$TOOLS_DIR/cookies.txt"
echo ""
echo "  Then in sermon_monitor.env set:"
echo "    YTDLP_COOKIES_FILE=$TOOLS_DIR/cookies.txt"
echo ""
echo "Option B — If the VM has a browser with YouTube logged in:"
echo "  In sermon_monitor.env set:"
echo "    YTDLP_COOKIES_BROWSER=chrome"
echo ""
echo "NOTE: YouTube cookies expire periodically. Re-export when downloads fail."
