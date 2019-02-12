#!/bin/bash

# System initialization and start up script for the Docker container,
# used for building the container.

ROOT_DIR=/deps_server_app

FLASK=/usr/local/bin/flask
WAITRESS=/usr/local/bin/waitress-serve

PORT=8080
export FLASK_APP=deps_server

cd $ROOT_DIR

# start the server
$WAITRESS --port $PORT --call $FLASK_APP:create_app
