#!/usr/bin/env bash
#
# Export YouTube cookies from Chrome and push to VM.
# Run this on your Mac when yt-dlp downloads start failing.
#
# Usage:
#   ./tools/refresh_cookies.sh <vm-user@vm-ip>
#
# Examples:
#   ./tools/refresh_cookies.sh devos@192.168.1.50
#   ./tools/refresh_cookies.sh devos@openclaw.local
#

set -euo pipefail

VM_TARGET="${1:?Usage: $0 <user@vm-ip>}"
COOKIES_FILE="/tmp/youtube_cookies.txt"
REMOTE_PATH="prayer_trusting_Jesus/tools/cookies.txt"

echo "==> Exporting YouTube cookies from Chrome..."
yt-dlp --cookies-from-browser chrome \
  --cookies "$COOKIES_FILE" \
  --skip-download "https://youtube.com" 2>/dev/null

if [ ! -f "$COOKIES_FILE" ]; then
  echo "ERROR: Cookie export failed"
  exit 1
fi

LINES=$(wc -l < "$COOKIES_FILE")
echo "    Exported $LINES cookie entries"

echo "==> Pushing cookies to VM ($VM_TARGET)..."
scp "$COOKIES_FILE" "${VM_TARGET}:${REMOTE_PATH}"

echo "==> Cleaning up local temp file..."
rm -f "$COOKIES_FILE"

echo "==> Done! Cookies refreshed on VM."
echo "    Make sure sermon_monitor.env has:"
echo "    YTDLP_COOKIES_FILE=/home/devos/prayer_trusting_Jesus/tools/cookies.txt"
