#!/usr/bin/env bash
# One command for the whole challenge: server up, ingest, query.
set -e
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:$PATH"

pip show mosaicolabs >/dev/null 2>&1 || pip install --user mosaicolabs
docker compose up -d
echo "Waiting for mosaicod on :6726..."
for i in $(seq 1 60); do (echo >/dev/tcp/localhost/6726) 2>/dev/null && break; sleep 2; done

mosaicolabs.ros_injector spot_yb42.mcap --name spot_yb42 --metadata sequence_metadata.json || \
  echo "(ingest failed or already done, going on with the query)"

python freefall_query.py
