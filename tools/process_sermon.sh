#!/usr/bin/env bash
#
# Process a YouTube sermon: download locally, upload to Azure, trigger processing.
#
# Usage:
#   ./tools/process_sermon.sh <youtube-url> [speaker] [category]
#
# Examples:
#   ./tools/process_sermon.sh "https://www.youtube.com/watch?v=TF6pHCEnjf4"
#   ./tools/process_sermon.sh "https://youtu.be/TF6pHCEnjf4" "Bishop Johnson" "sermon"
#
# Requirements: yt-dlp, python3, az (Azure CLI, logged in)
#

set -euo pipefail

URL="${1:?Usage: $0 <youtube-url> [speaker] [category]}"
SPEAKER="${2:-}"
CATEGORY="${3:-sermon}"

STORAGE_ACCOUNT="sttrstjesus"
CONTAINER="sermon-audio"
FUNC_URL="https://func-trusting-jesus.azurewebsites.net"
RESOURCE_GROUP="rg-trusting-jesus"
FUNC_NAME="func-trusting-jesus"

TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

echo "==> Downloading audio from YouTube..."
yt-dlp \
  --cookies-from-browser chrome \
  --format "bestaudio/best" \
  --extract-audio \
  --audio-format mp3 \
  --audio-quality 32K \
  --postprocessor-args "ffmpeg:-ac 1" \
  --output "$TMP_DIR/%(id)s.%(ext)s" \
  --print-json \
  --no-simulate \
  "$URL" > "$TMP_DIR/metadata.json"

VIDEO_ID=$(python3 -c "import json; d=json.load(open('$TMP_DIR/metadata.json')); print(d.get('id',''))")
VIDEO_TITLE=$(python3 -c "import json; d=json.load(open('$TMP_DIR/metadata.json')); print(d.get('title',''))")
UPLOADER=$(python3 -c "import json; d=json.load(open('$TMP_DIR/metadata.json')); print(d.get('uploader',''))")
UPLOAD_DATE=$(python3 -c "import json; d=json.load(open('$TMP_DIR/metadata.json')); print(d.get('upload_date',''))")

AUDIO_FILE=$(find "$TMP_DIR" -name "*.mp3" | head -1)
if [ -z "$AUDIO_FILE" ]; then
  echo "ERROR: No audio file found"
  exit 1
fi

SIZE_MB=$(du -m "$AUDIO_FILE" | cut -f1)
echo "==> Downloaded: $VIDEO_TITLE ($SIZE_MB MB)"

BLOB_NAME="${VIDEO_ID}.mp3"
echo "==> Uploading to Azure Blob Storage..."
CONN_STR=$(az storage account show-connection-string --name $STORAGE_ACCOUNT --resource-group $RESOURCE_GROUP --query connectionString -o tsv)
az storage blob upload \
  --container-name "$CONTAINER" \
  --name "$BLOB_NAME" \
  --file "$AUDIO_FILE" \
  --connection-string "$CONN_STR" \
  --overwrite \
  --only-show-errors
echo "    Uploaded: $BLOB_NAME"

echo "==> Calling Azure Function to process..."
FUNC_KEY=$(az functionapp keys list --name $FUNC_NAME --resource-group $RESOURCE_GROUP --query "functionKeys.default" -o tsv)

PAYLOAD=$(python3 << PYEOF
import json, os
meta = json.load(open('$TMP_DIR/metadata.json'))
speaker = '${SPEAKER:-}' or meta.get('uploader', '')
print(json.dumps({
    'url': '$URL',
    'speaker': speaker,
    'category': '$CATEGORY',
    'audio_blob': '$BLOB_NAME',
    'title': meta.get('title', ''),
    'upload_date': meta.get('upload_date', ''),
}))
PYEOF
)

RESPONSE=$(curl -s -w "\n%{http_code}" \
  --max-time 540 \
  -X POST "${FUNC_URL}/api/process?code=${FUNC_KEY}" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo ""
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"

echo "==> Cleaning up blob storage..."
az storage blob delete \
  --container-name "$CONTAINER" \
  --name "$BLOB_NAME" \
  --connection-string "$CONN_STR" \
  --only-show-errors 2>/dev/null || echo "    (blob already cleaned by Azure Function)"

if [ "$HTTP_CODE" -ne 200 ]; then
  echo "ERROR: Azure Function returned HTTP $HTTP_CODE"
  exit 1
fi

echo ""
echo "==> Done! Content generated and committed to GitHub."
echo "    Cloudflare Pages will auto-deploy shortly."
