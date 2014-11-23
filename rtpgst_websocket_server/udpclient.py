# -*- coding: UTF-8 -*-
import socket
import json

def getrows(hostaddr, logtype, ctime, interval=0, minduration=0, maxduration=0):
	cmd = {}
	cmd['logtype'] = logtype;
	cmd['ctime'] = [int(ctime), int(interval), int(minduration), int(maxduration)];
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.settimeout(1);
	sock.sendto(json.dumps(cmd), hostaddr)
	s = [];
	try:
		while True:
			data, addr = sock.recvfrom(8192*2);
			if data == 'bye':
				break;
			else:
				try:
					arr = json.loads(data);
					s.append(arr);
				except ValueError:
					pass;
	except socket.timeout:
		pass;
	return s;
