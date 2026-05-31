#!/bin/bash

cd $(dirname $0)

# Wait for Fess to become ready. Probe both the v1 and v2 health endpoints
# and accept the first 200, so the same runner works against v1-only
# (released) and v2 (snapshot) Fess images.
error_count=0
while true ; do
  status_v1=$(curl -w '%{http_code}\n' -s -o /dev/null "${FESS_URL}/api/v1/health")
  status_v2=$(curl -w '%{http_code}\n' -s -o /dev/null "${FESS_URL}/api/v2/health")
  if [[ x"${status_v1}" = x200 || x"${status_v2}" = x200 ]] ; then
    break
  else
    error_count=$((error_count + 1))
  fi
  if [[ ${error_count} -ge 180 ]] ; then
    echo "Fess is not available."
    exit 1
  fi
  sleep 1
done

echo "Starting Automation Test..."
python3 main.py
