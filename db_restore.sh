#!/bin/bash

source .env

if [ -f "$1" ]; then
    # https://github.com/docker/compose/issues/3352
    # so using docker instead docker-compose

    if [ "$(command -v pv)" ]; then
        pv "$1" | gunzip |  docker exec -i $(docker-compose ps -q db) mysql -u$MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE
    else
        echo "pv not installed, so can\'t show progress"
        cat "$1" | gunzip |  docker exec -i $(docker-compose ps -q db) mysql -u$MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE
    fi
else
    echo "Dump not found"
fi

# zcat backups/db_backup_201808131229.sql.gz | mysql -uroot -p ggsite