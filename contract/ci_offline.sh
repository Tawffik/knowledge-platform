#!/usr/bin/env bash
# Offline CI for the platform contract: lint (if ruff present) + all three suites
# against an ephemeral uvicorn server on a random port with a fresh SQLite file.
# No external services, no network beyond localhost. Exit non-zero on any failure.
set -u
cd "$(dirname "$0")"

PORT=$(python3 - <<'PY'
import socket
s = socket.socket(); s.bind(("127.0.0.1", 0))
print(s.getsockname()[1]); s.close()
PY
)
BASE_URL="http://127.0.0.1:${PORT}"
export BASE_URL
DB_PATH="/tmp/platform-ref-ci.db"
rm -f "$DB_PATH" /tmp/platform-ref.db

FAIL=0

echo "== 1/4 lint =="
if command -v ruff >/dev/null 2>&1; then
  ruff check reference/app.py || FAIL=1
elif python3 -m ruff --version >/dev/null 2>&1; then
  python3 -m ruff check reference/app.py || FAIL=1
else
  echo "SKIP lint: ruff not installed (declared skip, not a pass)"
fi

echo "== 2/4 offline suites (schema + parity) =="
python3 -m pytest test_schema_offline.py test_contract_parity.py -q || FAIL=1

echo "== 3/4 start reference server on ${BASE_URL} =="
( cd reference && nohup python3 -m uvicorn app:app --host 127.0.0.1 --port "${PORT}" > /tmp/kp-ci-uvicorn.log 2>&1 & echo $! > /tmp/kp-ci-uvicorn.pid )
READY=0
for i in $(seq 1 30); do
  if curl -sf "${BASE_URL}/openapi.json" >/dev/null 2>&1; then READY=1; break; fi
  sleep 1
done
if [ "$READY" != "1" ]; then
  echo "FAIL: server did not become ready in 30s"; cat /tmp/kp-ci-uvicorn.log; kill "$(cat /tmp/kp-ci-uvicorn.pid)" 2>/dev/null; exit 1
fi

echo "== 4/4 live negative suite =="
python3 -m pytest test_contract_negative.py -q || FAIL=1

kill "$(cat /tmp/kp-ci-uvicorn.pid)" 2>/dev/null
rm -f /tmp/kp-ci-uvicorn.pid "$DB_PATH" /tmp/platform-ref.db

if [ "$FAIL" = "0" ]; then echo "CI RESULT: PASS (lint see above, 17 offline + 8 live negative)"; else echo "CI RESULT: FAIL"; fi
exit "$FAIL"
