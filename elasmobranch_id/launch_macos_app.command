#!/usr/bin/env bash
# Double-clickable macOS launcher for Elasmobranch Species Identification
cd "$(dirname "$0")"

echo "=========================================================="
echo "  🦈 Launching Elasmobranch Species Identification System"
echo "  Opening in your default browser (Safari / Chrome)..."
echo "=========================================================="

./.venv/bin/streamlit run inference/streamlit_app.py --server.headless=false
