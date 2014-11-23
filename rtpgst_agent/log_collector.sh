#!/bin/sh

cd /home/postgres/rtpgst_agent
exec python parsecsv.py /var/db/dsn/data/pg_log/postgresql.fifo.csv > /var/db/dsn/data/pg_log/after.log 2>&1 &
