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
# Resolve on the host so $GITHUB_ENV (a host file path) is writable and so
# the container receives an explicit locale rather than 'random'.
export TEST_LANG="${TEST_LANG:-random}"
export TEST_LANG_SEED="${TEST_LANG_SEED:-}"
export BROWSER_LOCALE="${BROWSER_LOCALE:-}"

if ! command -v python3 >/dev/null 2>&1 ; then
    echo "ERROR: python3 is required on the host for language resolution" >&2
    exit 1
fi

TEST_LANG_RESOLVED=$(python3 "${base_dir}/scripts/resolve_lang.py")
export TEST_LANG="${TEST_LANG_RESOLVED}"
export TEST_LANG_RESOLVED

if [[ -n "${GITHUB_ENV:-}" ]] ; then
    echo "TEST_LANG_RESOLVED=${TEST_LANG_RESOLVED}" >> "${GITHUB_ENV}"
fi

echo "Fess:   ${fess_name}"
echo "Search: ${search_engine_name}"
echo "TEST_LANG=${TEST_LANG} (resolved) TEST_LANG_SEED=${TEST_LANG_SEED:-<unset>}"

docker compose ${docker_compose_files} up --abort-on-container-exit --exit-code-from test01
