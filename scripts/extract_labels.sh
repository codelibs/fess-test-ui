#!/usr/bin/env bash
# Extract fess_label_*.properties + fess_message_*.properties from a Fess
# Docker image into ./labels/. Used by run_test.sh and for local single-
# module runs.
#
# Usage:  ./scripts/extract_labels.sh [image-tag]
#         (default: ghcr.io/codelibs/fess:snapshot)

set -euo pipefail

IMAGE="${1:-ghcr.io/codelibs/fess:snapshot}"
DEST="${LABEL_DIR:-./labels}"

echo "Extracting labels from ${IMAGE} into ${DEST}/"

docker pull "${IMAGE}" >/dev/null

rm -rf "${DEST}"
mkdir -p "${DEST}/_tmp"

CID=$(docker create "${IMAGE}")
trap 'docker rm "${CID}" >/dev/null 2>&1 || true' EXIT
docker cp "${CID}:/usr/share/fess/app/WEB-INF/classes/." "${DEST}/_tmp/"

shopt -s nullglob
moved=0
for f in "${DEST}/_tmp"/fess_label*.properties "${DEST}/_tmp"/fess_message*.properties; do
    mv "$f" "${DEST}/"
    moved=$((moved + 1))
done
shopt -u nullglob
rm -rf "${DEST}/_tmp"

# Guard both families. The glob above runs under `shopt -s nullglob`, so a Fess
# image that stopped shipping either one would expand to nothing and this script
# would still exit 0 -- the failure would only surface later, as a
# FileNotFoundError pointing at /labels rather than at extraction. Both are
# load-bearing: i18n.init() constructs LabelStrings and MessageStrings
# unconditionally, so a missing file of either kind kills the whole run before a
# single test module executes.
for required in fess_label.properties fess_message.properties; do
    if [ ! -f "${DEST}/${required}" ]; then
        echo "ERROR: ${required} not found in ${IMAGE}" >&2
        exit 1
    fi
done

echo "Extracted ${moved} files. Sample:"
ls -1 "${DEST}" | head -5
