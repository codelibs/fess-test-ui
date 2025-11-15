#!/bin/bash

cd $(dirname $0)

# Extract OpenSearch URL from Fess URL
SEARCH_ENGINE_URL=${SEARCH_ENGINE_HTTP_URL:-http://searchtest01:9200}

echo "============================================"
echo "Starting Fess E2E Test Readiness Checks"
echo "Fess URL: ${FESS_URL}"
echo "Search Engine URL: ${SEARCH_ENGINE_URL}"
echo "============================================"

# Check OpenSearch readiness first
echo ""
echo "[1/3] Checking OpenSearch availability..."
search_error_count=0
while true ; do
  search_status=$(curl -w '%{http_code}\n' -s -o /dev/null "${SEARCH_ENGINE_URL}")
  if [[ x"${search_status}" = x200 ]] ; then
    echo "✓ OpenSearch is ready!"
    break
  else
    search_error_count=$((search_error_count + 1))
    if [[ $((search_error_count % 10)) -eq 0 ]] ; then
      echo "  Still waiting for OpenSearch... (${search_error_count}s elapsed)"
    fi
  fi
  if [[ ${search_error_count} -ge 120 ]] ; then
    echo "✗ OpenSearch not available after 120 seconds."
    exit 1
  fi
  sleep 1
done

# Check Fess base server readiness
echo ""
echo "[2/3] Waiting for Fess server to be ready..."
error_count=0
while true ; do
  status=$(curl -w '%{http_code}\n' -s -o /dev/null "${FESS_URL}")
  if [[ x"${status}" = x200 ]] ; then
    echo "✓ Fess base URL is responding!"
    break
  else
    error_count=$((error_count + 1))
    if [[ $((error_count % 10)) -eq 0 ]] ; then
      echo "  Still waiting for Fess server... (${error_count}s elapsed)"
    fi
  fi
  if [[ ${error_count} -ge 180 ]] ; then
    echo "✗ Fess is not available after 180 seconds."
    exit 1
  fi
  sleep 1
done

# Check admin interface readiness
echo ""
echo "[3/3] Checking admin interface availability..."
admin_error_count=0
while true ; do
  admin_status=$(curl -w '%{http_code}\n' -s -o /dev/null "${FESS_URL}/admin/")
  if [[ x"${admin_status}" = x200 ]] ; then
    echo "✓ Admin interface is ready!"
    break
  else
    admin_error_count=$((admin_error_count + 1))
    if [[ $((admin_error_count % 15)) -eq 0 ]] ; then
      echo "  Still waiting for admin interface... (${admin_error_count}s elapsed)"
    fi
  fi
  if [[ ${admin_error_count} -ge 300 ]] ; then
    echo "✗ Admin interface not ready after 300 seconds."
    echo ""
    echo "Debugging information:"
    echo "  - OpenSearch status: $(curl -w '%{http_code}' -s -o /dev/null ${SEARCH_ENGINE_URL})"
    echo "  - Fess base status: $(curl -w '%{http_code}' -s -o /dev/null ${FESS_URL})"
    echo "  - Admin status: $(curl -w '%{http_code}' -s -o /dev/null ${FESS_URL}/admin/)"
    exit 1
  fi
  sleep 1
done

# Final initialization buffer
echo ""
echo "All services are ready! Waiting additional 15 seconds for full initialization..."
sleep 15

echo ""
echo "============================================"
echo "Starting Automation Tests..."
echo "============================================"
python3 main.py
