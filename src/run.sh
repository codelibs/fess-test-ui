#!/bin/bash

cd $(dirname $0)

while true ; do
  status=$(curl -w '%{http_code}\n' -s -o /dev/null "${FESS_URL}")
  if [[ x"${status}" = x200 ]] ; then
    break
  else
    error_count=$((error_count + 1))
  fi
  if [[ ${error_count} -ge 60 ]] ; then
    echo "Fess is not available."
    exit 1
  fi
  sleep 1
done

echo "Starting Automation Test..."
python main.py
