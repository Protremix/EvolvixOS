#!/bin/bash
set -e
echo "Seeding AegisOS with development data"
BASE_URL="http://localhost:8000/api/v1"
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" -H "Content-Type: application/json" -d '{"email":"admin@verdis.io","password":"admin"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
if [ -z "$TOKEN" ]; then echo "Cannot login. Start backend first."; exit 1; fi
AUTH="Authorization: Bearer $TOKEN"
curl -s -X POST "$BASE_URL/multi-project/projects" -H "$AUTH" -H "Content-Type: application/json" -d '{"name":"Verdis Blockchain","type":"blockchain"}' > /dev/null
curl -s -X POST "$BASE_URL/pipelines" -H "$AUTH" -H "Content-Type: application/json" -d '{"name":"Dev Audit","template":"security_patch"}' > /dev/null
echo "Development data seeded!"
