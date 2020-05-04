#!/bin/bash

DIR="./backups"
DATESTAMP=$(date +%Y%m%d_%H%M%S)

source .env

if [ ! -d "$DIR" ]; then
    mkdir "$DIR"
fi

# using docker instead of docker-compose,
# because compose merging stdout & stderr => warning in dump => invalid dump
# https://github.com/dockerwest/compose-pimcore/issues/16

docker exec -i $(docker-compose ps -q db) sh -c "exec mysqldump --all-databases -u${MYSQL_USER} -p${MYSQL_PASSWORD} --single-transaction --quick --lock-tables=false" | gzip > "$DIR/db_$DATESTAMP.sql.gz"
