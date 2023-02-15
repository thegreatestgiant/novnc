#!/bin/sh
act workflow_dispatch \
    -P foobar=jonico/actions-runner:latest  \
    -e events-nektos.json -W .github/workflows/visualize-matrix-build-nektos.yml  \
    -s REDIS_PASSWORD=$REDIS_PASSWORD -b

