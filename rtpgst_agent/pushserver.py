# -*- coding: utf-8 -*-
import os,sys,socket
from SocketServer import ThreadingUDPServer, BaseRequestHandler
import json
from pysqlite2 import dbapi2 as sqlite



PORT = 8082

class myudpserver(ThreadingUDPServer):
	def __init__(self, server_addr, reqhandler, log_dirname):
		ThreadingUDPServer.__init__(self, server_addr, reqhandler);
		self.log_dirname = log_dirname;


class RequestHandler(BaseRequestHandler):
    def handle(self):
        if self.request[0].strip():
            try:
                data = json.loads(self.request[0].strip())
            except ValueError:
                return;
            socket = self.request[1]
            socket.settimeout(1);
            if data.has_key('ctime') and data.has_key('logtype'):
                #print 'connection from', self.client_address,
                #print data['logtype'], data['ctime'];
                sqlitedbfile = self.server.log_dirname + "/postgresql.log.sqlite"
                conn = sqlite.connect(sqlitedbfile);
                cur = conn.cursor();
                if data['logtype'] != "duration":
                    res = cur.execute("select * from %s_log where ctime = ?" % (data['logtype']), [data['ctime'][0]]);
                else: #duration
                    if data['ctime'][1] > 0:
                        wherectime = "ctime >= %d and ctime <= (%d + %d)" % (data['ctime'][0], data['ctime'][0], data['ctime'][1]);
                    else:
                        wherectime = "ctime = %d" % (data['ctime'][0]);
                    if data['ctime'][2] == data['ctime'][3]:
                        wherectime += " and query_pos = %d" % (data['ctime'][2]);
                    else:
                        if data['ctime'][3] < 0:
                            wherectime += " and query_pos >= %d" % (data['ctime'][2]);
                        else:
                            wherectime += " and query_pos >= %d and query_pos <= %d" % (data['ctime'][2], data['ctime'][3]);
                    res = cur.execute("select * from %s_log where %s" % (data['logtype'], wherectime));
                rows = res.fetchall();
                del res;
                cur.close();
                conn.close();
                try:
                    for row in rows:
                        socket.sendto(json.dumps(row), self.client_address)
                    socket.sendto('bye', self.client_address)
                except:
                    print 'except!'
                    pass;

if __name__ == '__main__':
    server = myudpserver(('',PORT), RequestHandler, os.path.dirname(sys.argv[1]))
    server.max_packet_size = 8192*2;
    server.serve_forever()
