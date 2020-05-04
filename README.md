### installaton

1. clone

2. set params in `.env`

3.  `docker-compose build`  
self-signed certs created during build (if `$LETSENCRYPT` is not set)  

4. `docker-compose up web`

5. create db schema  
`./manage.sh migrate`  

6. copy static files  
`./manage.sh collectstatic`  

7. `docker-compose up`  

### additional

##### for enable debug in django need to create file  
`touch web/src/.debug`

##### db backup  
`./db_backup.sh`

##### db restore  
`./db_restore.sh "backups/db_20180813_183443.sql.gz"`
