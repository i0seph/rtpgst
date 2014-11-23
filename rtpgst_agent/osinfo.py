#!/usr/bin/python

import re,time

'''
MemTotal:         448776 kB
MemFree:          383552 kB
Buffers:            7144 kB
Cached:            28452 kB
'''

'''
    user: normal processes executing in user mode
    nice: niced processes executing in user mode
    system: processes executing in kernel mode
    idle: twiddling thumbs
    iowait: waiting for I/O to complete
    irq: servicing interrupts
    softirq: servicing softirqs
'''
isstop = False;

def get_cpuinfo():
	f = open('/proc/stat');
	cpus = f.readline();
	f.close();
	cpuinfo = re.split('[ ]+',cpus)[1:8];
	total = 0L;
	for i in range(len(cpuinfo)):
		total = total + int(cpuinfo[i]);
		cpuinfo[i] = int(cpuinfo[i]);
	cpuinfo.append(total);	
	return cpuinfo;

def calc_cpuinfo(stat_row):
	new_arr = get_cpuinfo();
	if stat_row[1] == None:
		return [None, new_arr];
	arr = [];
	for i in range(len(new_arr)):
		arr.append(new_arr[i] - stat_row[1][i]);
	cpuinfo = {};
	if stat_row[1] != None:
		cpuinfo['user'] = round(((arr[0] * 1.0) / arr[7]) * 100,1);
		cpuinfo['nice'] = round(((arr[1] * 1.0) / arr[7]) * 100,1);
		cpuinfo['system'] = round(((arr[2] * 1.0) / arr[7]) * 100,1);
		cpuinfo['idle'] = round(((arr[3] * 1.0) / arr[7]) * 100,1);
		cpuinfo['wait'] = round(((arr[4] * 1.0) / arr[7]) * 100,1);
		cpuinfo['hi'] = round(((arr[5] * 1.0) / arr[7]) * 100,1);
		cpuinfo['si'] = round(((arr[6] * 1.0) / arr[7]) * 100,1);
	return [cpuinfo, new_arr];
	
def get_meminfo():
	f = open('/proc/meminfo');
	all = f.readlines();
	f.close();

	meminfo = {}
	for str in all:
		row = re.split(':',str);
		row[1] = re.findall('[0-9]+', row[1])[0];
		meminfo[row[0]] = int(row[1]);

	mempercent = {};
	mempercent['free'] = round(((meminfo['MemFree'] * 1.0) / meminfo['MemTotal']) * 100, 1);
	mempercent['buffer'] = round(((meminfo['Buffers'] * 1.0) / meminfo['MemTotal']) * 100, 1);
	mempercent['cache'] = round(((meminfo['Cached'] * 1.0) / meminfo['MemTotal']) * 100, 1);
	mempercent['use'] = round((((meminfo['MemTotal'] - (meminfo['MemFree'] + meminfo['Buffers'] + meminfo['Cached'])) * 1.0) / meminfo['MemTotal']) * 100, 1);
	return mempercent;

def get_netinfo(devstr):
	devname = "%6s" % (devstr);
	f = open('/proc/net/dev');
	netstrs = f.readlines();
	f.close();
	arr = [0L,0L];
	for i in netstrs:
		if len(re.findall(devname + ":", i)) > 0:
			row = re.split(':',i);
			row = re.findall('[0-9]+', row[1]);
			arr[0] = long(row[0]);
			arr[1] = long(row[8]);
			break;
	return arr;

def calc_netinfo(stat_row, check_interval, devname):
	new_arr = get_netinfo(devname);
	if stat_row[1] == None:
		return [None, new_arr];
	arr = [];
	for i in range(len(new_arr)):
		if stat_row[1][i] > new_arr[i]:
			arr.append(round(((4294967296L - stat_row[1][i] + new_arr[i]) / 1024.0) / (check_interval * 1.0),0));
		else:
			arr.append(round(((new_arr[i] - stat_row[1][i]) / 1024.0) / (check_interval * 1.0), 0));
	return [arr, new_arr];

def get_diskinfo(devname):
	f = open('/proc/diskstats');
	netstrs = f.readlines();
	f.close();
	arr = [0L,0L];
	for i in netstrs:
		if len(re.findall(" " + devname + " ", i)) > 0:
			row = re.split(" " + devname + " ",i);
			row = re.findall('[0-9]+', row[1]);
			arr[0] = long(row[2]);
			arr[1] = long(row[6]);
			break;
	return arr;

def calc_diskinfo(stat_row, check_interval, devname):
	new_arr = get_diskinfo(devname);
	if stat_row[1] == None:
		return [None, new_arr];
	arr = [];
	for i in range(len(new_arr)):
		if stat_row[1][i] > new_arr[i]:
			arr.append(round(((4294967296L - stat_row[1][i] + new_arr[i]) / 2.0) / (check_interval * 1.0),0));
		else:
			arr.append(round(((new_arr[i] - stat_row[1][i]) / 2.0) / (check_interval * 1.0), 0));
	return [arr, new_arr];

def get_vmstat(interval, request = None):
	is_start = True;
	stat_cpuinfo = [None, None];
	stat_netinfo = [None, None];
	stat_diskinfo = [None, None];
	check_interval = interval;
	while True:
		if isstop:
			break;
		ctime = time.time();
		meminfo = get_meminfo();
		stat_cpuinfo = calc_cpuinfo(stat_cpuinfo);
		stat_netinfo = calc_netinfo(stat_netinfo, check_interval, "eth0");
		stat_diskinfo = calc_diskinfo(stat_diskinfo, check_interval, "sda3");


		if is_start:
			is_start = False;
		else:
			if request == None:
				print "[%s,%s,%s,%s,%s,%s,%s]" % (int(ctime),meminfo['use'],100 - stat_cpuinfo[0]['idle'],stat_netinfo[0][0], stat_netinfo[0][1], stat_diskinfo[0][0], stat_diskinfo[0][1])
			else:
				request.ws_stream.send_message("%s,%s,%s,%s,%s,%s,%s" % (int(ctime),meminfo['use'],100 - cpuinfo['idle'],netinfo[0], netinfo[1], diskinfo[0], diskinfo[1]), binary=False)	
		time.sleep(check_interval - (time.time() - ctime) - 0.0015);

if __name__ == '__main__':
	get_vmstat(2);

