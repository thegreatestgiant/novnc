#!/bin/bash

if [ -z "$MY_DB_URL" ]; then
    echo "MY_DB_URL not set, using default database"
else
    echo "MY_DB_URL set, using your personal database"
    export DATABASE_URL="$MY_DB_URL"
fi

echo "Pulling needed docker container, this will only take some seconds the first time you run this script ..."
docker pull ghcr.io/ghcr.io/jonico/actions-runner:ps 
echo "Killing and removing any docker containers from previous runs ..."
docker kill $(docker ps -q --filter name=Matrix-Build-Custom-Runner)
docker rm $(docker ps -a -q --filter name=Matrix-Build-Custom-Runner)

act workflow_dispatch \
    -P custom-runner=ghcr.io/ghcr.io/jonico/actions-runner:ps   \
    -e test-parameters.json \
    -a ${GITHUB_USER:0:10} \
    -W .github/workflows/matrix-build-custom-runner-nektos.yml  \
    -s DATABASE_URL=$DATABASE_URL \
    -b
