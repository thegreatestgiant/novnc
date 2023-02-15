#!/usr/bin/env bash

act workflow_dispatch   -W .github/workflows/connect-to-gcp.yaml  -s CLUSTER_NAME=$CLUSTER_NAME -s CLUSTER_LOCATION=$CLUSTER_LOCATION -s PROJECT_ID -s GCP_SA_KEY="$GCP_SA_KEY" -b -r 
