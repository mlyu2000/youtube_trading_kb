#!/bin/bash
set -e

COOKIES_JSON="/home/ml/nb_cookies.json"
AUTH_SCRIPT="/home/ml/.hermes/hermes-agent/venv/lib/python3.11/site-packages/notebooklm/import_browser_cookies.py"
STORAGE_STATE="/home/ml/.notebooklm/profiles/default/storage_state.json"

# Ensure storage dir exists
mkdir -p "$(dirname "$STORAGE_STATE")"

if [[ ! -f "$COOKIES_JSON" ]]; then
    echo "❌ Cookie export not found: $COOKIES_JSON"
    echo "   Please export from Chrome and copy here, then re-run."
    exit 1
fi

# Convert using notebooklm-py's helper
echo "🔄 Converting cookies..."
python3 "$AUTH_SCRIPT" "$COOKIES_JSON" --out "$STORAGE_STATE"

# Verify
echo "✅ Verifying..."
notebooklm auth check --test

echo ".hostname" > "$STORAGE_STATE.meta"
