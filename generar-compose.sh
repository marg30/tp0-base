#!/bin/bash

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <output_file> <number_clients>"
  exit 1
fi

COMPOSE_FILE=$1
NUM_CLIENTS=$2

if ! [[ "$NUM_CLIENTS" =~ ^[0-9]+$ ]]; then
  echo "Error: The number of clients must be a positive integer."
  exit 1
fi

cat > $COMPOSE_FILE <<EOL
name: tp0
services:
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=DEBUG
    networks:
      - testing_net
EOL

for ((i=1; i<=NUM_CLIENTS; i++))
do
  cat >> $COMPOSE_FILE <<EOL

  client$i:
    container_name: client$i
    image: client:latest
    entrypoint: /client
    environment:
      - CLI_ID=$i
      - CLI_LOG_LEVEL=DEBUG
    networks:
      - testing_net
    depends_on:
      - server
EOL
done

cat >> $COMPOSE_FILE <<EOL

networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
EOL

echo "File $COMPOSE_FILE generated with $NUM_CLIENTS clients."
