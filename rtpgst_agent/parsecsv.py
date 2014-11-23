import os,sys,csv,time,signal,threading
import timer
import webclient
import cStringIO
import logging
# setting timestamp for this program log
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG);

# for pglog parser
import pglogparser
import json;

# for sqlite
from pysqlite2 import dbapi2 as sqlite

from SocketServer import ThreadingUDPServer, BaseRequestHandler
import pushserver;

maxInt = sys.maxsize / 20
decrement = True 
while decrement:
	# decrease the maxInt value by factor 10 
	#as long as the OverflowError occurs.
	decrement = False
	try:
		csv.field_size_limit(maxInt)
	except OverflowError:
		maxInt = int(maxInt/10)
		decrement = True


# for signal
is_stop = False;

def closefile(sig, func=None):
        '''
        close fifo file handle && set stop value for escaping main loop
        '''
        global fd
        logging.error("break by kill");
        fd.close();
        is_stop = True;

# set signal
signal.signal(signal.SIGTERM, closefile);

globalque = {}



class parsecsv(threading.Thread):
        def __init__(self, fifofile, globalque):
                self.fifofile = fifofile;
                self.globalque = globalque;
                threading.Thread.__init__(self);
        def run(self):
                global fd, is_stop;
		aLine = cStringIO.StringIO();
		n = 1;
                try:
                        while True:
                        # main loop because multiful server stop, start
                                if is_stop == False:
                                        #get file handle
                                        fd = os.fdopen(os.open(self.fifofile, os.O_RDONLY));
                                        # parse csv (just one!)
                                        oldtime = int(time.time());
					while True:
						for chunk in iter(lambda: fd.read(n), ''):
							if chunk != '':
								aLine.write(chunk);
							if chunk == '\n':
								try:
									if aLine.getvalue() == "\n":
										aLine.truncate(0);
										continue;
									csviter = csv.reader([aLine.getvalue()]);
									for row in csviter:
										sqlite_conn = sqlite.connect(os.path.dirname(self.fifofile) + '/postgresql.log.sqlite');
										sqlite_cursor = sqlite_conn.cursor();
										current_time = int(time.time());
										pglogparser.parse(self.globalque, current_time, oldtime, row, sqlite_cursor);
										oldtime = current_time;
										sqlite_cursor.close();
										sqlite_conn.commit();
										sqlite_conn.close();
									aLine.truncate(0);
								except csv.Error, e:
									if e.message == "newline inside string":
										continue;
									else:
										logging.error("%s" % aLine.getvalue());
										logging.error("%s" % (e));
					fd.close()
                                else:
                                        fd.close()
                                        break;
                except(KeyboardInterrupt, IOError):
                        # signal exception
                        closefile(2);


class pushlog_server(threading.Thread):
        def __init__(self, port, log_dirname):
                self.port = port;
                self.log_dirname = log_dirname;
                threading.Thread.__init__(self);
        def run(self):
                logserver = pushserver.myudpserver(('',self.port), pushserver.RequestHandler, self.log_dirname)
                logserver.max_packet_size = 8192*2;
                logserver.serve_forever();


check_interval = 1;
checker_timer = timer.timer(check_interval);
checker_timer.daemon = True;
checker_timer.start();
old_timestamp = 0L;

log_dirname = os.path.dirname(sys.argv[1]);

checklog = parsecsv(sys.argv[1], globalque);
checklog.daemon = True;
checklog.start();

push_log_server_port = 8082;
pushlog_svr = pushlog_server(push_log_server_port, os.path.dirname(sys.argv[1]));
pushlog_svr.daemon = True;
pushlog_svr.start();

while 1:
        try:
                if is_stop == True:
                        break;
                next_timestamp = checker_timer.next_timestamp - check_interval;
                if next_timestamp != old_timestamp:
                        if globalque.has_key(old_timestamp):
                                tmparr = globalque.pop(old_timestamp);
                                if tmparr['ERROR'] == {}:
                                        tmparr.pop('ERROR');
                                if tmparr['FATAL'] == {}:
                                        tmparr.pop('FATAL');
                                if sum(tmparr['duration']) == 0:
                                        tmparr.pop('duration');
#                               print(old_timestamp, json.dumps(tmparr));
                                str_timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(old_timestamp));
                                webclient.senddata(3,str_timestamp, json.dumps(tmparr));
                                sys.stdout.flush();
                        old_timestamp = next_timestamp;
                time.sleep(0.01);
        except(KeyboardInterrupt, IOError):
                # signal exception
                closefile(2);

