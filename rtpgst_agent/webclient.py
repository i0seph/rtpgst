#!/usr/bin/python
# -*- coding: utf-8 -*-


import httplib;
import urllib;
import agent_config;
import sys;
import json;

def getAgentInfo():
        pemweb = httplib.HTTPConnection(agent_config.agent_dbhost, 80);
        pemweb.connect();
        pemweb.request('get', '/agentinfo.php?dbname=' + agent_config.local_dbname + '&dbport=' + agent_config.local_dbport);
        res = pemweb.getresponse();
        agent_info = json.loads(res.read());
        pemweb.close();
        return agent_info;

def senddata(agent_id, ctime, jsondata):
        try:
                pemweb = httplib.HTTPConnection(agent_config.agent_dbhost, 80);
                pemweb.connect();
                pemweb.request('get', '/gather_log.php?agent_id=' + urllib.quote_plus(`agent_id`) + '&ctime=' + urllib.quote_plus(ctime) + '&data=' + urllib.quote_plus(jsondata));
                res = pemweb.getresponse();
#               print res.read();
                pemweb.close();
        except Exception, exc:
                print exc;

if __name__ == '__main__':
        a = getAgentInfo();
        print a;
