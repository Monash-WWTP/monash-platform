#!/usr/bin/env bash
# Convenience launcher for CitizenFlood.
#
# Usage:
#   1. Copy env.example.json -> env.json and fill in your Supabase values.
#   2. ./scripts/run.sh                 # run on the default device
#      ./scripts/run.sh -d <device-id>  # extra args are forwarded to `flutter run`
#
# env.json is git-ignored, so your keys never get committed.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f env.json ]; then
  echo "✗ env.json not found."
  echo "  Copy the template and add your Supabase credentials:"
  echo "    cp env.example.json env.json"
  exit 1
fi

exec flutter run --dart-define-from-file=env.json "$@"
