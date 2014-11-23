# -*- coding: UTF-8 -*-
import sys;
import time;
sys.path.append('/home/ioseph/python');
import pgdb;
import json;


class pglog:
	def __init__(self, agent_id, request = None, threadname = None):
		self.agent_id = agent_id;
		self.request = request;
		self.isstop = False;
		self.response = {};
		if threadname:
			self.threadname = threadname;
		else:
			self.threadname = "NonThread";
	def runstat(self):
		localdb = pgdb.DaemonConnection("host=127.0.0.1 dbname=rtpgst  user=statagent", True, "RTPGLOG Thread", self.threadname);
		localdb.connect();
		self.cur = localdb.cursor();
		#self.cur.execute("select row_to_json(a)::text from (select coalesce(page_title,host(dbhost)||':'||dbport||'/'||dbname) as page_title,check_interval * 1000 as check_interval from agent_config where agent_id = %s) a" % (self.agent_id));
		#row = self.cur.fetchone();
		#if self.request:
		#       self.request.ws_stream.send_message("3|0|%s" % (row[0]), binary=False);
		self.cur.execute("listen insert_logdata_%s" % (self.agent_id));
		self.cur.execute("select ctime::abstime::int, data::text from logdata_%s where ctime > (current_timestamp - interval '2 minutes') order by ctime" % (self.agent_id));
		rs = self.cur.fetchall();

		for row in rs:
			self.last_ctime = row[0];
			if self.request:
				#self.request.ws_stream.send_message("0|%s|%s" % (row[0],row[1]), binary=False);
				continue;
			else:
				print row[1];
		if not rs:
			self.last_ctime = int(time.time());
#		if self.request:
#			self.request.ws_stream.send_message("2|row[0]|{}", binary=False);
		while True:
			if self.isstop == True:
				localdb.close();
				break;
			try:
				localdb.poll();
			except pgdb.OperationalError, e:
				localdb.reconnect();
				self.cur = localdb.cursor();
				self.cur.execute("listen insert_logdata_%s" % (self.agent_id));
				localdb.poll();

			while localdb.notifies:
				n = localdb.notifies.pop();
				if n[1] == "insert_logdata_%s" % (self.agent_id):
					self.last_ctime = self.get_lastrow();
			time.sleep(0.01);
	def get_lastrow(self):
		self.cur.execute("select ctime::abstime::int as intctime,data from logdata_%s where ctime > '%s'::int::abstime order by ctime limit 1" % (self.agent_id,self.last_ctime));
		row = self.cur.fetchone();
		if row == None:
			return self.last_ctime;
		else:
			if self.request:
				self.response = {};
				self.response['c'] = 'ld';
				self.response['t'] = row[0];
				self.response['d'] = row[1];
				self.request.ws_stream.send_message(json.dumps(self.response), binary=False);
			else:
				print row[1];
			return row[0];

if __name__ == '__main__':
	a = pglog(sys.argv[1]);
	a.runstat();
