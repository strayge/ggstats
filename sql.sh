#!/bin/bash

source .env

docker exec -i $(docker-compose ps -q db) mysql -u$MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "$1"
