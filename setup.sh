#!/bin/bash
set -e

cd "$(dirname "$0")"
mkdir -p ./data ./file
touch ./data/filehoster.sqlite3
chmod -R 777 ./data
sudo chown -R 1000:1000 ./file
docker compose up -d --build
