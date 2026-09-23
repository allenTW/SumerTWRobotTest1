#!/bin/sh
# Start the uploader in the foreground. Extra args pass through to server.py
# (e.g. ./run.sh --port 9000 --root /somewhere/else).
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
exec /usr/bin/python3 "$DIR/server.py" "$@"
