#!/usr/bin/python

import sys;
import datetime;
import time;
import pgdb;
import json;
import math;

def std_dev(arr):
        stdsum = 0;
        avg = float(sum(arr)) / len(arr);
        for v in arr:
                stdsum += (v - avg) ** 2;
        return math.sqrt(stdsum / len(arr));

localdb = pgdb.DaemonConnection("host=127.0.0.1 dbname=rtpgst  user=statagent", True, "RTPGST DW");
localdb.connect();
# clean raw data
cur = localdb.cursor();
cur.execute("select f_clean_statdata()");
row = cur.fetchone();
cur.close();
#print row;
# clean idle web session
cur = localdb.cursor();
cur.execute("select pg_terminate_backend(pid) from pg_stat_activity where application_name = 'RTPGST Thread' and state = 'idle' and state_change < current_timestamp - cast('5 minutes' as interval)");
row = cur.fetchall();
cur.close();
#print row;
# one minute dataware housing
to_time = datetime.datetime.now().replace(second=0, microsecond=0);
from_time = to_time - datetime.timedelta(minutes=1);

cur = localdb.cursor();
cur.execute("select agent_id from agent_config");
agent_ids = [];
for result in cur.fetchall():
        agent_ids.append(result[0]);
cur.close();

for agent_id in agent_ids:
        #agent_id = 13;
        cur = localdb.cursor();
        cur.execute("select data from statdata_%d where ctime >= '%s' and ctime < '%s'" % (agent_id, from_time, to_time));
        arr = {};
        rowcnt = 0;
        for result in cur.fetchall():
                for subkey in result[0].keys():
                        if rowcnt == 0:
                                arr[subkey] = [];
                        for i in range(0,len(result[0][subkey])):
                                if rowcnt == 0:
                                        arr[subkey].append([]);
                                arr[subkey][i].append(float(result[0][subkey][i]));
                rowcnt += 1;
        cur.close();

        if rowcnt > 0:
                arr2 = {};
                for subkey in arr.keys():
                        arr2[subkey] = [];
                        for i in range(0,len(arr[subkey])):
                                arr2[subkey].append([ min(arr[subkey][i]), max(arr[subkey][i]), round(float(sum(arr[subkey][i])) / len(arr[subkey][i]),2), round(std_dev(arr[subkey][i]),2), round(0,2)]);
                cur = localdb.cursor();
                stattable = "dw1min.statdata_%d" % (agent_id);
                cur.execute("insert into %s (ctime, data) values ('%s', '%s')" % (stattable, to_time,  json.dumps(arr2)));
                cur.close();

if (to_time.minute % 15) == 0:
        from_time = to_time - datetime.timedelta(minutes=15);

        for agent_id in agent_ids:
                #agent_id = 13;
                cur = localdb.cursor();
                cur.execute("select data from dw1min.statdata_%d where ctime > '%s' and ctime <= '%s'" % (agent_id, from_time, to_time));
                arr = {};
                rowcnt = 0;
                for result in cur.fetchall():
                        for subkey in result[0].keys():
                                if rowcnt == 0:
                                        arr[subkey] = [];
                                for i in range(0,len(result[0][subkey])):
                                        if rowcnt == 0:
                                                arr[subkey].append([[],[],[],[],[]]);
                                        for j in range(0,5):
                                                if j == 4:
                                                        arr[subkey][i][j].append(0);
                                                else:
                                                        arr[subkey][i][j].append(result[0][subkey][i][j]);
                        rowcnt += 1;
                cur.close();

                if rowcnt > 0:
                        arr2 = {};
                        for subkey in arr.keys():
                                arr2[subkey] = [];
                                for i in range(0,len(arr[subkey])):
                                        arr2[subkey].append([ min(arr[subkey][i][0]), max(arr[subkey][i][1]), round(float(sum(arr[subkey][i][2])) / len(arr[subkey][i][2]),2), round(std_dev(arr[subkey][i][2]),2), round(sum(arr[subkey][i][4]),2)]);
                        cur = localdb.cursor();
                        stattable = "dw15min.statdata_%d" % (agent_id);
                        cur.execute("insert into %s (ctime, data) values ('%s', '%s')" % (stattable, to_time,  json.dumps(arr2)));
                        cur.close();
localdb.close();
