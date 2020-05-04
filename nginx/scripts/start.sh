#!/bin/sh

if [ "$LETSENCRYPT" != "true" ]; then
    /scripts/genkeys.sh
fi

exec /entrypoint.sh
