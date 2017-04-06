#!/usr/bin/python

import urllib2
import httplib
import json
import socket
import os
import sys
from urlparse import urlsplit

DOCKER_UNIX_SOCKET = 'unix://var/run/docker.sock'
DEFAULT_SOCKET_TIMEOUT = 5


class UnixHTTPConnection(httplib.HTTPConnection):

    socket_timeout = DEFAULT_SOCKET_TIMEOUT

    def __init__(self, unix_socket):
        self._unix_socket = unix_socket

    def connect(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self._unix_socket)
        sock.settimeout(self.socket_timeout)
        self.sock = sock

    def __call__(self, *args, **kwargs):
        httplib.HTTPConnection.__init__(self, *args, **kwargs)
        return self

# monkeypatch UNIX socket support into urllib2
class UnixSocketHandler(urllib2.AbstractHTTPHandler):
    def unix_open(self, req):
        full_path = "%s%s" % urlsplit(req.get_full_url())[1:3]
        path = os.path.sep
        for part in full_path.split('/'):
            path = os.path.join(path, part)
            if not os.path.exists(path):
                break
            unix_socket = path
        # urllib2 needs an actual hostname or it complains
        url = req.get_full_url().replace(unix_socket, '/localhost')
        unix_req = urllib2.Request(url, req.get_data(), dict(req.header_items()))
        unix_req.timeout = req.timeout
        return self.do_open(UnixHTTPConnection(unix_socket), unix_req)

    unix_request = urllib2.AbstractHTTPHandler.do_request_

try:
	uri = "%s/nodes" % DOCKER_UNIX_SOCKET
	req = urllib2.Request(uri)
	opener = urllib2.build_opener(UnixSocketHandler())
	request = opener.open(req)
	result = json.loads(request.read())
	print "<<<docker_swarm>>>"
	for  node in result:
		print "{:s}\t{:s}\t{:s}\t{:s}\t{:s}".format( node['Description']['Hostname'], node['Spec']['Availability'], node['ManagerStatus']['Reachability'], node['Status']['State'], node['Spec']['Role'] )

except urllib2.URLError as e:
	sys.exit(1)
