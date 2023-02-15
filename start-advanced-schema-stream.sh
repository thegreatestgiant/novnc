#!/bin/bash

if [ -z "$MY_DB_URL" ]; then
    echo "MY_DB_URL not set, using default database"
else
    echo "MY_DB_URL set, using your personal database"
    export DATABASE_URL="$MY_DB_URL"
fi

echo "Pulling needed docker container, this will only take some seconds the first time you run this script ..."
docker pull jonico/action-runner:ps
echo "Killing and removing any docker containers from previous runs ..."
docker kill $(docker ps -q --filter name=Advanced-Schema-Stream)
docker rm $(docker ps -a -q --filter name=Advanced-Schema-Stream)

act workflow_dispatch \
    -P ps-runner=jonico/action-runner:ps  \
    -e advanced-schema-stream-parameters.json \
    --env environment=${GITHUB_USER:0:10} \
    -W .github/workflows/advanced-schema-stream.yml  \
    -s DATABASE_URL=$DATABASE_URL \
    -b
