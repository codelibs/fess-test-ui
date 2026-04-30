#!/bin/bash

set -euo pipefail

cd $(dirname $0)
base_dir=$(pwd)

fess_name="${1:-}"
search_engine_name="${2:-}"
docker_compose_files="-f ${base_dir}/compose.yaml"

if [[ "$fess_name" = "" ]] ; then
    fess_name=fess14
elif [[ ! -f "$base_dir/compose-${fess_name}.yaml" ]] ; then
    echo "${fess_name} is not found."
    exit 1
fi
docker_compose_files="${docker_compose_files} -f ${base_dir}/compose-${fess_name}.yaml"

if [[ "$search_engine_name" = "" ]] ; then
    search_engine_name=elasticsearch7
elif [[ "$search_engine_name" = "opensearch1" || "$search_engine_name" = "opensearch2" || "$search_engine_name" = "opensearch3" ]] ; then
    docker_compose_files="--env-file .env.opensearch ${docker_compose_files}"
elif [[ ! -f "$base_dir/compose-${search_engine_name}.yaml" ]] ; then
    echo "${search_engine_name} is not found."
    exit 1
fi
docker_compose_files="${docker_compose_files} -f ${base_dir}/compose-${search_engine_name}.yaml"

# ----- Extract Fess labels for i18n test support --------------------------
# Resolve the Fess image referenced by the chosen compose file and copy
# fess_label_*.properties / fess_message_*.properties into ./labels/
# (mounted into test01 by compose.yaml as /labels:ro).
if ! command -v yq >/dev/null 2>&1 ; then
    echo "ERROR: yq is required (brew install yq)" >&2
    exit 1
fi

FESS_IMAGE=$(yq -r '.services.fesstest01.image' "${base_dir}/compose-${fess_name}.yaml")
if [[ "${FESS_IMAGE}" == "null" || -z "${FESS_IMAGE}" ]] ; then
    echo "ERROR: could not resolve fesstest01.image from compose-${fess_name}.yaml" >&2
    exit 1
fi

"${base_dir}/scripts/extract_labels.sh" "${FESS_IMAGE}"
[ -f "${base_dir}/labels/fess_label.properties" ] || {
    echo "ERROR: label extraction failed" >&2; exit 1; }

# ----- Resolve language settings ------------------------------------------
export TEST_LANG="${TEST_LANG:-random}"
export TEST_LANG_SEED="${TEST_LANG_SEED:-}"
export BROWSER_LOCALE="${BROWSER_LOCALE:-}"

echo "Fess:   ${fess_name}"
echo "Search: ${search_engine_name}"
echo "TEST_LANG=${TEST_LANG} TEST_LANG_SEED=${TEST_LANG_SEED:-<unset>}"

docker compose ${docker_compose_files} up --abort-on-container-exit --exit-code-from test01
