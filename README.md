### installaton

1. prepare dirs  
`mkdir ggstats`  
`cd ggstats`

2. copy files

3. set executable bit  
`chmod +x web/src/start.sh`  
`chmod +x ./*.sh`

4.  `docker-compose build`  

5. ~~manual self-signed cert~~  
automatic creating during build  
`docker-compose run nginx /bin/sh /scripts/genkeys.sh`

6. `docker-compose up web`

7. in new db generate scheme  
`rm -rf web/src/ggchat/migrations`  
`./manage.sh makemigrations ggchat`  
`./manage.sh migrate`  

8. `docker-compose up`  

### additional

for enable debug in django need to create file  
`web/src/.debug`

db backup  
`./db_backup.sh`

db restore  
`./db_restore.sh "backups/db_20180813_183443.sql.gz"`