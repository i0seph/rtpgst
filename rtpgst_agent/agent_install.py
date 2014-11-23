import pgdb
import agent_config


def do_install():
	statdb = pgdb.DaemonConnection("host=%s port=%s dbname=%s user=%s password=%s" % ( \
                agent_config.agent_dbhost, \
                agent_config.agent_dbport, \
                agent_config.agent_dbname, \
                agent_config.agent_dbuser, \
                agent_config.agent_dbpass), True);
	statdb.connect();
	cur = statdb.cursor();
	cur.execute("set application_name = 'pg_stat_pusher'");
	cur.execute("select client_addr from pg_stat_activity where pid  = pg_backend_pid()");
	dbhost = cur.fetchone()[0];
	cur.execute("select * from agent_config where dbhost = '%s' and dbport = '%s' and dbname = '%s'" % (dbhost, agent_config.local_dbport, agent_config.local_dbname));
	agentconfig = cur.fetchone();
	if agentconfig == None:
		cur.execute("insert into agent_config (dbhost, dbport, dbname) values ('%s','%s','%s') returning *" % (dbhost,agent_config.local_dbport, agent_config.local_dbname));
		agentconfig = cur.fetchone();
	cur.close();
	# check whether already installed
	statdb.close();
	return agentconfig;

if __name__ == '__main__':
	agentconfig = do_install();
	print agentconfig;
