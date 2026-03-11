#!/usr/bin/env bash
#
# Set up the pure local sermon pipeline on Ubuntu 22.04 VM.
#
# No Azure dependency — uses local faster-whisper + Claude API.
#
# Usage:
#   chmod +x tools/setup_local_vm.sh
#   sudo ./tools/setup_local_vm.sh
#

set -euo pipefail

DEPLOY_DIR="/home/devos/prayer_trusting_Jesus"
TOOLS_DIR="$DEPLOY_DIR/tools"
VENV_DIR="$TOOLS_DIR/venv"
USER="devos"

echo "=== Pure Local Sermon Pipeline — Ubuntu 22.04 Setup ==="

# --- 1. System packages ---
echo ""
echo ">>> Installing system packages..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv ffmpeg curl git

# --- 2. yt-dlp ---
echo ""
echo ">>> Installing yt-dlp..."
pip3 install --break-system-packages yt-dlp 2>/dev/null || pip3 install yt-dlp
echo "    yt-dlp: $(yt-dlp --version)"

# --- 3. Python venv with all dependencies ---
echo ""
echo ">>> Creating Python virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -q \
    faster-whisper \
    anthropic \
    PyGithub \
    requests

# Check for CUDA (optional — falls back to CPU)
if command -v nvidia-smi &>/dev/null; then
    echo "    NVIDIA GPU detected — Whisper will use CUDA"
    "$VENV_DIR/bin/pip" install -q ctranslate2
else
    echo "    No GPU detected — Whisper will use CPU (int8)"
fi

chown -R "$USER:$USER" "$VENV_DIR"

# --- 4. Log directory ---
echo ""
echo ">>> Creating log directory..."
mkdir -p /var/log/sermon-monitor
chown "$USER:$USER" /var/log/sermon-monitor

# --- 5. Env file ---
if [ ! -f "$TOOLS_DIR/sermon_local.env" ]; then
    echo ""
    echo ">>> Creating sermon_local.env from template..."
    cp "$TOOLS_DIR/sermon_local.env.template" "$TOOLS_DIR/sermon_local.env"
    chown "$USER:$USER" "$TOOLS_DIR/sermon_local.env"
    chmod 600 "$TOOLS_DIR/sermon_local.env"
fi

# --- 6. Make scripts executable ---
chmod +x "$TOOLS_DIR/sermon_local.py"
chmod +x "$TOOLS_DIR/refresh_cookies.sh" 2>/dev/null || true

# --- 7. Systemd units ---
echo ""
echo ">>> Installing systemd service and timer..."
cp "$TOOLS_DIR/systemd/sermon-local.service" /etc/systemd/system/
cp "$TOOLS_DIR/systemd/sermon-local.timer" /etc/systemd/system/
systemctl daemon-reload
systemctl enable sermon-local.timer
systemctl start sermon-local.timer

# --- 8. Gitignore entries ---
GITIGNORE="$DEPLOY_DIR/.gitignore"
for entry in "tools/sermon_local.env" "tools/venv/" "tools/.sermon_local_state.json"; do
    if ! grep -qF "$entry" "$GITIGNORE" 2>/dev/null; then
        echo "$entry" >> "$GITIGNORE"
    fi
done

echo ""
echo "=== Setup Complete ==="
echo ""
systemctl list-timers sermon-local.timer --no-pager
echo ""
echo "Next steps:"
echo "  1. Edit credentials:  nano $TOOLS_DIR/sermon_local.env"
echo "     - Set ANTHROPIC_API_KEY"
echo "     - Set GITHUB_TOKEN (fine-grained PAT with contents:write)"
echo "     - Set GITHUB_REPO"
echo ""
echo "  2. Export YouTube cookies from your Mac:"
echo "     ./tools/refresh_cookies.sh $USER@<vm-ip>"
echo ""
echo "  3. Test:"
echo "     sudo -u $USER $VENV_DIR/bin/python3 $TOOLS_DIR/sermon_local.py --dry-run"
echo "     sudo -u $USER $VENV_DIR/bin/python3 $TOOLS_DIR/sermon_local.py --url 'https://youtu.be/TF6pHCEnjf4'"
echo ""
echo "  4. Watch logs:"
echo "     journalctl -u sermon-local -f"
echo ""
echo "Architecture:"
echo "  yt-dlp (local) → faster-whisper (local) → Claude API → GitHub API → Cloudflare Pages"
echo "  No Azure, no blob storage, no cloud functions."
