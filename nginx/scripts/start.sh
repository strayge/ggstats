#!/bin/sh

if [ "$LETSENCRYPT" != "true" ]; then
    exec /scripts/genkeys.sh
fi

exec /entrypoint.sh
