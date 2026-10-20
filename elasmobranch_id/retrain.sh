#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "Using virtual environment: $DIR/.venv"
"$DIR/.venv/bin/python" "$DIR/retrain.py"
