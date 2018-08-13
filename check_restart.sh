#!/bin/bash
if test `find "/var/www/ggsite/fetcher.log" -mmin +6`
then
    # kill hanging process
    pkill -f "manage.py fetcher"
    # write in log
    echo "`date +'%Y-%m-%d %H:%M:%S'` ERROR    Proccess killed by supervisor!" >> /var/www/ggsite/fetcher.log
    # restart new in tmux session
    tmux new-session -d -s gg
    tmux send-keys -t gg "cd /var/www/ggsite" C-m
    tmux send-keys -t gg "source /var/www/venv/bin/activate" C-m
    tmux send-keys -t gg "python manage.py fetcher" C-m
fi

