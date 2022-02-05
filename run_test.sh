#!/bin/bash

cd $(dirname $0)
base_dir=$(pwd)

fess_name=$1
search_engine_name=$2
docker_compose_files="-f ${base_dir}/docker-compose.yml"

if [[ "$fess_name" = "" ]] ; then
    fess_name=fess13
elif [[ ! -f "$base_dir/docker-compose-${fess_name}.yml" ]] ; then
    echo "${fess_name} is not found."
    exit 1
fi
docker_compose_files="${docker_compose_files} -f ${base_dir}/docker-compose-${fess_name}.yml"

if [[ "$search_engine_name" = "" ]] ; then
    search_engine_name=elasticsearch7
elif [[ ! -f "$base_dir/docker-compose-${search_engine_name}.yml" ]] ; then
    echo "${search_engine_name} is not found."
    exit 1
fi
docker_compose_files="${docker_compose_files} -f ${base_dir}/docker-compose-${search_engine_name}.yml"

echo "Fess:   ${fess_name}"
echo "Search: ${search_engine_name}"
docker-compose ${docker_compose_files} up --abort-on-container-exit --exit-code-from test01
