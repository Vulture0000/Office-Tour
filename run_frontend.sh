#!/usr/bin/env bash
cd "$(dirname "$0")/frontend"
if [ ! -d node_modules ]; then
  npm install --no-audit --no-fund
fi
exec npx vite --port 5173 --host 0.0.0.0
