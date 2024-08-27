#!/bin/bash

# Variables
NETWORK_NAME="tp0_testing_net"
ECHO_SERVER_CONTAINER="server"
NETCAT_IMAGE="alpine:latest"
MESSAGE="HelloEchoServer"
PORT=12345

docker network ls | grep -q "$NETWORK_NAME" || docker network create "$NETWORK_NAME"

RESULT=$(docker run --rm --network "$NETWORK_NAME" "$NETCAT_IMAGE" sh -c "echo '$MESSAGE' | nc $ECHO_SERVER_CONTAINER $PORT")

if [ "$RESULT" == "$MESSAGE" ]; then
  echo "action: test_echo_server | result: success"
else
  echo "action: test_echo_server | result: fail"
fi
