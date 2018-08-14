#!/bin/sh

docker-compose exec web /bin/bash -c "cd /src && python3 manage.py $1 $2 $3 $4"