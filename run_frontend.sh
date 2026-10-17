#!/usr/bin/env bash
cd "$(dirname "$0")/frontend"
npm ci --silent
exec npm run dev
