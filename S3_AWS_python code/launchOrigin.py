import sys, os, subprocess, socket, time, zlib
import urllib, urllib2, json
#import fbcli as fb
#from fbenv import _process, _run
#from fbenv._configuration import environment
#import fbcli.base
import ConfigParser

def start_origin(user, password, port):
	if port > 0:
		print("Starting Origin for user %s on port %d" % (user, port))
	else:
		print("Starting Origin for user %s on default port" % user)
	
	access_token = get_origin_access_token(user, password)
	print("  Access token: " + str(access_token))

	args = ["C:\Program Files (x86)\Origin\Origin.exe", "-Origin_MultipleInstances", "/authToken:%s" % access_token]
	if port > 0:
		args.append("/LsxPort:%d" % port)
	
	p = subprocess.Popen(args)
	if p.pid == 0:
		print_error("Failed to start origin")
		sys.exit(12)

def get_origin_access_token(username, password):
	# Production environment
		#auth_url = "https://accounts.ea.com"
		#client_secret =  'UIY8dwqhi786T78ya8Kna78akjcp0s'

	# Integration environment
	auth_url = "https://accounts.int.ea.com"
	client_secret = 'ORIGIN_PC_SECRET'

	params = {
		'grant_type': 'password',
		'username': username,
		'password': password,
		'client_id': 'ORIGIN_PC',
		'client_secret': client_secret,
		'scope': 'signin basic.identity openid'
	}

	req = urllib2.Request('{0}/connect/token'.format(auth_url), urllib.urlencode(params))
	resp = urllib2.urlopen(req)

	
start_origin("anthgst0001@gos.ea.com","Loadtest1234",3216)	
