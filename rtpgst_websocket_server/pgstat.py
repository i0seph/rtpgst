# -*- coding: UTF-8 -*-

import sys;
import time;
sys.path.append('/home/ioseph/python');
import pgdb;
import json;
import logging;


class pgstat:
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
		localdb = pgdb.DaemonConnection("host=127.0.0.1 dbname=rtpgst  user=statagent", True, "RTPGST Thread", self.threadname);
		localdb.connect();
		self.cur = localdb.cursor();
		# send agent info
		self.cur.execute("select coalesce(page_title,host(dbhost)||':'||dbport||'/'||dbname) as page_title,check_interval * 1000 as check_interval from agent_config where agent_id = %s",[int(self.agent_id)]);
		row = self.cur.fetchone();
		if row == None:
			if self.request:
				self.response = {};
				self.response['c'] = 'er';
				self.response['d'] = u'This agent does not exists.';
				self.request.ws_stream.send_message(json.dumps(self.response), binary=False);
			else:
				print("do not exists agent : %s" % (self.agent_id));
			return;

		if self.request:
			self.response = {};
			self.response['c'] = 'ai';
			self.response['d'] = row;
			self.request.ws_stream.send_message(json.dumps(self.response), binary=False);

		self.cur.execute("listen insert_statdata_%s" % (self.agent_id));

		# send last 5 minutes data 
		logging.info("%s: prepare preload data" % (self.threadname));
		self.cur.execute("select (case when b.ctime is null then a.endtime else b.ctime end)::abstime::int as intctime, coalesce(b.data, '{\"osinfo\": [null, null, null, null, null, null], \"session\": [null, null], \"bgwriter\": [null, null, null, null, null, null, null, null, null, null], \"database\": [null, null, null, null, null, null, null, null, null, null, null, null, null, null, null]}'::json) as data from (select generate_series(to_timestamp(current_timestamp::abstime::int)::timestamp without time zone - interval '2 seconds' * 599, to_timestamp(current_timestamp::abstime::int)::timestamp without time zone , interval '2 seconds') as endtime, generate_series((to_timestamp(current_timestamp::abstime::int)::timestamp without time zone - interval '2 seconds') - interval '2 seconds' * 599, to_timestamp(current_timestamp::abstime::int)::timestamp without time zone - interval '2 seconds' , interval '2 seconds') as begintime) a left outer join (select * from statdata_%s order by ctime desc limit 600) b on (b.ctime > a.begintime and b.ctime <= a.endtime) order by a.endtime" % (self.agent_id));
		rs = self.cur.fetchall();
		logging.info("%s: start preload data" % (self.threadname));
		for row in rs:
			self.last_ctime = row[0];
			if self.request:
				self.response = {};
				self.response['c'] = 'sp';
				self.response['t'] = row[0];
				self.response['d'] = row[1];
				self.request.ws_stream.send_message(json.dumps(self.response), binary=False);
			else:
				print row[1];
		logging.info("%s: end preload data" % (self.threadname));
		# send preload data sending end;
		if self.request:
			self.response = {};
			self.response['c'] = 'ep';
			self.request.ws_stream.send_message(json.dumps(self.response), binary=False);

		# main loop listen and send one row;
		while True:
			if self.isstop == True:
				localdb.close();
				break;
			localdb.poll();
			while localdb.notifies:
				n = localdb.notifies.pop();
				if n[1] == "insert_statdata_%s" % (self.agent_id):
					self.last_ctime = self.get_lastrow();
			time.sleep(0.01);

	def get_lastrow(self):
		self.cur.execute("select ctime::abstime::int as intctime,data from statdata_%s where ctime > '%s'::int::abstime order by intctime limit 1" % (self.agent_id,self.last_ctime));
		row = self.cur.fetchone();
		if row == None:
			return self.last_ctime;
		else:
			if self.request:
				self.response = {};
				self.response['c'] = 'cd';
				self.response['t'] = row[0];
				self.response['d'] = row[1];
				self.request.ws_stream.send_message(json.dumps(self.response), binary=False);
			else:
				print row[1];
			return row[0];

if __name__ == '__main__':
	a = pgstat(sys.argv[1]);
	a.runstat();
