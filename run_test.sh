#!/bin/bash

cd $(dirname $0)
base_dir=$(pwd)

fess_name=$1
search_engine_name=$2
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

echo "Fess:   ${fess_name}"
echo "Search: ${search_engine_name}"
docker compose ${docker_compose_files} up --abort-on-container-exit --exit-code-from test01
