#!/usr/bin/python

import sys;
import signal;
import time;
import datetime;
import pgdb;
import timer;
import osinfo;
import json;
import agent_config;
import agent_install;

import logging
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG);


is_stop = False;

def cleandb(sig, func=None):
    global is_stop
    logging.error("break by kill");
    is_stop = True;

signal.signal(signal.SIGTERM, cleandb);

agentconfig = agent_install.do_install();
'''
Table "public.agent_config"
      Column       |          Type         
-------------------+-----------------------
 agent_id          | integer               
 dbhost            | inet                  
 check_interval    | integer               
 datakeep_interval | interval              
 page_title        | character varying(128)
 dbport            | integer               
 dbname            | name                  
'''
stattable = "statdata_%d" % (agentconfig[0]);
check_interval = agentconfig[2];
datakeep_interval = agentconfig[3];

# check_interval = divisor of 60, ex: 1,2,3,4,5,6,10,12,15,20,30,60 (120, 180, ...)
#check_interval = int(sys.argv[1]);
next_timestamp = int(time.time()) + check_interval - (time.localtime(time.time())[5] % check_interval);

localdb = pgdb.DaemonConnection("host=%s port=%s dbname=%s user=%s password=%s" % ( \
		agent_config.local_dbhost, \
		agent_config.local_dbport, \
		agent_config.local_dbname, \
		agent_config.local_dbuser, \
		agent_config.local_dbpass), True);
localdb.connect();

statdb = pgdb.DaemonConnection("host=%s port=%s dbname=%s user=%s password=%s" % ( \
		agent_config.agent_dbhost, \
		agent_config.agent_dbport, \
		agent_config.agent_dbname, \
		agent_config.agent_dbuser, \
		agent_config.agent_dbpass), True);
statdb.connect();
cur = statdb.cursor();
cur.execute("set application_name = 'pg_stat_pusher'");
cur.close();

# init
cur = localdb.cursor();
# set application_name
cur.execute("set application_name = 'pg_stat_collector'");
# get database oid
cur.execute("select datid from pg_stat_activity where pid = pg_backend_pid()");
current_datid = cur.fetchone()[0];
cur.close();
# prepare query
q_bgwriter = "select * from pg_stat_bgwriter";
q_session = "select coalesce(b.acnt::bigint,0::bigint) as acnt, coalesce(b.tcnt::bigint,0::bigint) as tcnt from (select 1 as dummy ) a left outer join (select 1 as dummy, case when st = 'A' then cnt else '0'::bigint end as acnt, tcnt from (select case when state like 'idle%%' then 'I' else 'A' end as st, count(*) as cnt, sum(count(*)) over() as tcnt from pg_stat_activity  where datid = %d and pid <> pg_backend_pid() group by st order by 1 limit 1) a) b on (a.dummy = b.dummy)" % (current_datid);
q_database = "select xact_commit,xact_rollback,blks_read,blks_hit,tup_returned,tup_fetched,tup_inserted,tup_updated,tup_deleted,conflicts,temp_files,temp_bytes,deadlocks,round(blk_read_time),round(blk_write_time) from pg_stat_database where datname = current_database()";

def get_stat_bgwriter(conn, stat_row):
    cur = conn.cursor();
    cur.execute(q_bgwriter);
    rs = cur.fetchone();
    cur.close();
    if rs == None:
        return [None,None];
    calc_row = [];
    if stat_row[1] != None:
        for i in range(10):
            calc_row.append(rs[i] - stat_row[1][i]);
        stat_row[0] = calc_row;
    stat_row[1] = rs;
    return stat_row;

def get_stat_session_cnt(conn, current_datid):
    cur = conn.cursor();
    cur.execute(q_session);
    row = cur.fetchone();
    cur.close();
    return [row[0], row[1]];


def get_stat_database(conn, stat_row):
    cur = conn.cursor();
    cur.execute(q_database);
    rs = cur.fetchone();
    cur.close();
    if rs == None:
        return [None,None];
    calc_row = [];
    if stat_row[1] != None:
        for i in range(15):
            calc_row.append(rs[i] - stat_row[1][i]);
        stat_row[0] = calc_row;
    stat_row[1] = rs;
    return stat_row;


stat_bgwriter = [None,None];
stat_cpuinfo = [None, None];
stat_netinfo = [None, None];
stat_diskinfo = [None, None];
stat_database = [None,None];

checker_timer = timer.timer(check_interval);
checker_timer.daemon = True;
checker_timer.start();
old_timestamp = 0L;

while 1:
    if is_stop == True:
        break;
    next_timestamp = checker_timer.next_timestamp - check_interval;
    if next_timestamp != old_timestamp:
        current_timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(next_timestamp));
        # os stat
        meminfo = osinfo.get_meminfo();
        stat_cpuinfo = osinfo.calc_cpuinfo(stat_cpuinfo);
        stat_netinfo = osinfo.calc_netinfo(stat_netinfo, check_interval, agent_config.local_net_device);
        stat_diskinfo = osinfo.calc_diskinfo(stat_diskinfo, check_interval, agent_config.local_disk_device);
        # db stat
        stat_bgwriter =  get_stat_bgwriter(localdb, stat_bgwriter);
        stat_session = get_stat_session_cnt(localdb, current_datid);
        stat_database = get_stat_database(localdb, stat_database);
        
        if stat_bgwriter[0] != None:
            data = {"bgwriter":stat_bgwriter[0], \
                    "osinfo":[meminfo['use'],round(100 - stat_cpuinfo[0]['idle'],1),stat_netinfo[0][0], stat_netinfo[0][1], stat_diskinfo[0][0], stat_diskinfo[0][1]], \
                    "session": stat_session, \
                    "database": stat_database[0]};
            cur = statdb.cursor();
            cur.execute("insert into %s (ctime, data) values ('%s', '%s')" % (stattable, current_timestamp,  json.dumps(data)));
            cur.execute("notify insert_%s" % (stattable));
            cur.close();
        old_timestamp = next_timestamp;
    time.sleep(0.01);

localdb.close();
statdb.close();
