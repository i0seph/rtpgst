import agent_config;
import time;
import calcgrade;
import sys;
import signal;
from pysqlite2 import dbapi2 as sqlite


def parse(globalque, time_current, time_old, logarr, sqlite_cursor = None):
        '''
        csv pg log parser
        table columns
        --------------------------------------------------
        [0] log_time timestamp(3) with time zone,
        [1] user_name text,
        [2] database_name text,
        [3] process_id integer,
        [4] connection_from text,
        [5] session_id text,
        [6] session_line_num bigint,
        [7] command_tag text,
        [8] session_start_time timestamp with time zone,
        [9] virtual_transaction_id text,
        [10] transaction_id bigint,
        [11] error_severity text,
        [12] sql_state_code text,
        [13] message text,
        [14] detail text,
        [15] hint text,
        [16] internal_query text,
        [17] internal_query_pos integer,
        [18] context text,
        [19] query text,
        [20] query_pos integer,
        [21] location text,
        [22] application_name text,
        '''
	try:
	        (log_time, user_name, database_name, process_id, connection_from, session_id, session_line_num, command_tag, session_start_time, virtual_transaction_id, transaction_id, error_severity, sql_state_code, message, detail, hint, internal_query, internal_query_pos, context, query, query_pos, location, application_name) = logarr;

		# duration collector
		# grade per 50ms (0 ~ 1250ms) 25 grades array[0..24]
		# grade per 200ms (1000ms ~ 6050ms)  24 grade array[25..48]
		#  > 6050 , max (array[49])
		if not globalque.has_key(time_current):
			globalque[time_current] = {};
			globalque[time_current]['duration'] = [0] * 50;
			globalque[time_current]['ERROR'] = {};
			globalque[time_current]['FATAL'] = {};

		if error_severity == 'LOG' and message.find("duration: ") == 0:
			exec_duration = int(round(float(message[10:10 + message[10:].find(' ')])))

			if message.find('statement: ') > 0:
				query = message[message.find('statement: ') + 11:]
				globalque[time_current]['duration'][calcgrade.getgrade(exec_duration)] += 1;
				# save log to sqlite
				if exec_duration >= agent_config.log_min_duration_statement:
					if(sqlite_cursor):
						try:
							res = sqlite_cursor.execute("insert into duration_log (log_time, user_name, database_name, process_id, connection_from, session_id, session_line_num, command_tag, session_start_time, virtual_transaction_id, transaction_id, error_severity, sql_state_code, message, detail, hint, internal_query, internal_query_pos, context, query, query_pos, location, application_name, ctime) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(log_time, unicode(user_name,'utf-8'), unicode(database_name,'utf-8'), process_id, unicode(connection_from,'utf-8'), unicode(session_id,'utf-8'), session_line_num, unicode(command_tag,'utf-8'), session_start_time, unicode(virtual_transaction_id,'utf-8'), transaction_id, unicode(error_severity,'utf-8'), unicode(sql_state_code,'utf-8'), unicode(message,'utf-8'), unicode(detail,'utf-8'), unicode(hint,'utf-8'), unicode(internal_query,'utf-8'), internal_query_pos, unicode(context,'utf-8'), unicode(query,'utf-8'), exec_duration, unicode(location,'utf-8'), unicode(application_name,'utf-8'),time_current));
						except sqlite.IntegrityError as err:
							print(err);
					else:  # sqlite_cursor
						print(logarr);
						sys.stdout.flush();
			elif message.find(' plan:') > 0:
				message = message[message.find('\n') + 1:];
				if(sqlite_cursor):
					try:
						res = sqlite_cursor.execute("insert into explain_log (log_time, user_name, database_name, process_id, connection_from, session_id, session_line_num, command_tag, session_start_time, virtual_transaction_id, transaction_id, error_severity, sql_state_code, message, detail, hint, internal_query, internal_query_pos, context, query, query_pos, location, application_name, ctime) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(log_time, unicode(user_name,'utf-8'), unicode(database_name,'utf-8'), process_id, unicode(connection_from,'utf-8'), unicode(session_id,'utf-8'), session_line_num, unicode(command_tag,'utf-8'), session_start_time, unicode(virtual_transaction_id,'utf-8'), transaction_id, unicode(error_severity,'utf-8'), unicode(sql_state_code,'utf-8'), unicode(message,'utf-8'), unicode(detail,'utf-8'), unicode(hint,'utf-8'), unicode(internal_query,'utf-8'), internal_query_pos, unicode(context,'utf-8'), unicode(query,'utf-8'), exec_duration, unicode(location,'utf-8'), unicode(application_name,'utf-8'),time_current));
					except sqlite.IntegrityError as err:
						print(err);
				else:
					print(logarr);
					sys.stdout.flush();
		elif error_severity == "ERROR" or error_severity == "FATAL":
			data_arr = globalque[time_current][error_severity];
			if not globalque[time_current][error_severity].has_key(sql_state_code):
				globalque[time_current][error_severity][sql_state_code] = 1;
			else:
				globalque[time_current][error_severity][sql_state_code] += 1;
			if(sqlite_cursor):
				try:
					res = sqlite_cursor.execute("insert into %s_log (log_time, user_name, database_name, process_id, connection_from, session_id, session_line_num, command_tag, session_start_time, virtual_transaction_id, transaction_id, error_severity, sql_state_code, message, detail, hint, internal_query, internal_query_pos, context, query, query_pos, location, application_name, ctime) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)" % (error_severity.lower()),(log_time, unicode(user_name,'utf-8'), unicode(database_name,'utf-8'), process_id, unicode(connection_from,'utf-8'), unicode(session_id,'utf-8'), session_line_num, unicode(command_tag,'utf-8'), session_start_time, unicode(virtual_transaction_id,'utf-8'), transaction_id, unicode(error_severity,'utf-8'), unicode(sql_state_code,'utf-8'), unicode(message,'utf-8'), unicode(detail,'utf-8'), unicode(hint,'utf-8'), unicode(internal_query,'utf-8'), internal_query_pos, unicode(context,'utf-8'), unicode(query,'utf-8'), query_pos, unicode(location,'utf-8'), unicode(application_name,'utf-8'),time_current));
				except sqlite.IntegrityError as err:
					print(err);
			else:
				print(logarr);
				sys.stdout.flush();
		else:
			print(logarr);
			sys.stdout.flush();

	except ValueError as err:
		print(err);
		print(logarr)
