#!/bin/bash

cd $(dirname $0)

echo "Waiting for Fess server to be ready..."
while true ; do
  status=$(curl -w '%{http_code}\n' -s -o /dev/null "${FESS_URL}")
  if [[ x"${status}" = x200 ]] ; then
    break
  else
    error_count=$((error_count + 1))
  fi
  if [[ ${error_count} -ge 120 ]] ; then
    echo "Fess is not available after 120 seconds."
    exit 1
  fi
  sleep 1
done

echo "Fess base URL is responding, checking admin interface..."
# Wait for admin dashboard to be fully ready
admin_error_count=0
while true ; do
  admin_status=$(curl -w '%{http_code}\n' -s -o /dev/null "${FESS_URL}/admin/")
  if [[ x"${admin_status}" = x200 ]] ; then
    echo "Admin interface is ready!"
    break
  else
    admin_error_count=$((admin_error_count + 1))
  fi
  if [[ ${admin_error_count} -ge 180 ]] ; then
    echo "Admin interface not ready after 180 seconds."
    exit 1
  fi
  sleep 1
done

# Give the application a bit more time to fully initialize
echo "Waiting additional 15 seconds for application to fully initialize..."
sleep 15

echo "Starting Automation Test..."
python3 main.py
