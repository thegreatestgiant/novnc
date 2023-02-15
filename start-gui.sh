#!/bin/bash

# cd to the directory of the script
cd "$(dirname "$0")"

if [ -z "$MY_DB_URL" ]; then
    echo "MY_DB_URL not set, using default database"
else
    echo "MY_DB_URL set, using your personal database"
    export DATABASE_URL="$MY_DB_URL"
fi

python3 gui.py --sleep-interval=100 --environment="${GITHUB_USER:0:10}"