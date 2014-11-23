#!/bin/sh

cd /home/ioseph/python
exec python /usr/lib/python2.7/dist-packages/mod_pywebsocket/standalone.py -p 8080 > websocket.log  2>&1 &
