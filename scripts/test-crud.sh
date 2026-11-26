#!/usr/bin/env bash
# Uji health dan 4 endpoint CRUD.
# Pemakaian: bash scripts/test-crud.sh [BASE_URL]   (default http://localhost:8000)
# Simpan output: bash scripts/test-crud.sh | tee crud-test.txt
BASE="${1:-http://localhost:8000}"
JSON='Content-Type: application/json'
jget() { python3 -c "import sys,json; print(json.load(sys.stdin)['$1'])"; }

echo "== GET /health"
curl -s -w '  [HTTP %{http_code}]\n' "$BASE/health"

echo "== CREATE  POST /equipment"
OUT=$(curl -s -w '\n%{http_code}' -X POST "$BASE/equipment" -H "$JSON" -d '{"name":"Proyektor Epson","category":"Elektronik"}')
CODE=${OUT##*$'\n'}
RES=${OUT%$'\n'*}
echo "$RES  [HTTP $CODE]"
ID=$(echo "$RES" | jget id)

echo "== READ    GET /equipment/$ID"
curl -s -w '  [HTTP %{http_code}]\n' "$BASE/equipment/$ID"

echo "== UPDATE  PUT /equipment/$ID"
curl -s -w '  [HTTP %{http_code}]\n' -X PUT "$BASE/equipment/$ID" -H "$JSON" -d '{"status":"borrowed","borrower":"Farand"}'

echo "== LIST    GET /equipment"
curl -s -w '  [HTTP %{http_code}]\n' "$BASE/equipment"

echo "== DELETE  DELETE /equipment/$ID"
curl -s -w '  [HTTP %{http_code}]\n' -X DELETE "$BASE/equipment/$ID"

echo "== READ setelah DELETE (harus 404)"
curl -s -w '  [HTTP %{http_code}]\n' "$BASE/equipment/$ID"
