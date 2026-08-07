#!/bin/bash
set -e
echo "Running all tests"
cd aegisos/backend && python -m pytest --tb=short -q && echo "Backend OK"
cd ../frontend && npm run build && echo "Frontend OK"
echo "All tests passed!"
