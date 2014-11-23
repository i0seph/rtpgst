# -*- coding: UTF-8 -*-
import time;
import datetime;
import threading;
import sys;
import json
import logging


sys.path.append('/home/ioseph/python');
import pgstat;
import pglog;
import udpclient;

_GOODBYE_MESSAGE = u'Goodbye'

wsclients = {};
wsthreads = {};

class pgstat_thread(threading.Thread):
    def __init__(self,request, agent_id):
        self.request = request;
        self.agent_id = agent_id;
        threading.Thread.__init__(self);
    def run(self):
        self.v_pgstat = pgstat.pgstat(self.agent_id, self.request, self.name);
        self.v_pgstat.runstat();
    def safe_exit(self):
        logging.info("exit call %s" % self.name);
        self.v_pgstat.isstop = True;

class pglog_thread(threading.Thread):
    def __init__(self,request, agent_id):
        self.request = request;
        self.agent_id = agent_id;
        threading.Thread.__init__(self);
    def run(self):
        self.v_pgstat = pglog.pglog(self.agent_id, self.request, self.name);
        self.v_pgstat.runstat();
    def safe_exit(self):
        logging.info("exit call %s" % self.name);
        self.v_pgstat.isstop = True;

class udpclient_thread(threading.Thread):
    def __init__(self,request, agent_id, logtype, ctime):
        self.request = request;
        self.agent_id = agent_id;
        self.logtype = logtype;
        self.ctime = ctime;
        threading.Thread.__init__(self);
    def run(self):
        hostaddr = ('127.0.0.1',8082);
        if(self.logtype == "duration"):
            arr = udpclient.getrows(hostaddr, self.logtype, self.ctime[0],self.ctime[1],self.ctime[2],self.ctime[3])
        else:
            arr = udpclient.getrows(hostaddr, self.logtype, self.ctime[0])
        rs = {}
	rs['c'] = 'll'
	rs['t'] = self.ctime[0];
	rs['logtype'] = self.logtype;
	rs['d'] = arr;
        self.request.ws_stream.send_message(json.dumps(rs), binary=False);
    def safe_exit(self):
        logging.info("exit call %s" % self.name);




def web_socket_do_extra_handshake(request):
    pass

def web_socket_transfer_data(request):
    while True:
        line = request.ws_stream.receive_message()
        if line is None:
            return
        if isinstance(line, unicode):
	    logging.info("%s:%d: %s" % (request.connection.remote_addr[0],request.connection.remote_addr[1],line));
	    try:
                req_cmd = json.loads(line);
            except ValueError:
                logging.error("request fail: %s" % (line));
                continue;
            if req_cmd['cmd'] == 'startchart':
                stthread = pgstat_thread(request, req_cmd['agent_id']);
                stthread.isDaemon = True;
                stthread.start();
		wsclients["%s:%d" % (request.connection.remote_addr[0], request.connection.remote_addr[1])] = stthread.name;
		wsthreads[stthread.name] = stthread;
		logging.info("Remain %d threads" % len(wsthreads));
            elif req_cmd['cmd'] == "stopchart":
		endthread = wsthreads.pop(wsclients["%s:%d" % (request.connection.remote_addr[0], request.connection.remote_addr[1])]);
		logging.info("%s: closing" % (endthread.name));
		endthread.safe_exit();
		logging.info("Remain %d threads" % len(wsthreads));
                #pgstat.isstop = True;
            elif req_cmd['cmd'] == "getDuration":
                stthread = pglog_thread(request, req_cmd['agent_id']);
                stthread.isDaemon = True;
                stthread.start();
		wsclients["%s:%d" % (request.connection.remote_addr[0], request.connection.remote_addr[1])] = stthread.name;
		wsthreads[stthread.name] = stthread;
		logging.info("Remain %d threads" % len(wsthreads));
            elif req_cmd['cmd'] == "showLogs":
                stthread = udpclient_thread(request, req_cmd['agent_id'], req_cmd['logtype'], req_cmd['t']);
                stthread.isDaemon = True;
                stthread.start();
#		wsclients["%s:%d" % (request.connection.remote_addr[0], request.connection.remote_addr[1])] = stthread.name;
#		wsthreads[stthread.name] = stthread;
		logging.info("Remain %d threads" % len(wsthreads));
            elif line == _GOODBYE_MESSAGE:
		logging.info("Goodbye: %s" % (line));
                return
        else:
            request.ws_stream.send_message(line, binary=True)
