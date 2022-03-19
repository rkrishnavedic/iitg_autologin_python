import getpass;
print("Enter your Username:", end=" ");USERNAME = input();
print("Enter your Password:", end=" ");PASSWORD = getpass.getpass();

BASE_URL = "agnigarh.iitg.ac.in:1442";
LOGIN_URL = "/login?";
LOGOUT_URL = "/logout?";

ERROR_FAILS = [r"Firewall authentication failed", r"concurrent authentication"]
ERROR_MSG = ["Your password and username is not correct!", "You are logged in somewhere else too! [Concurrent Limit Reached]"]

import http.client
import re
import urllib
import time

# Get Tokens
connection = http.client.HTTPSConnection(BASE_URL);
keep_alive_link = None

#----------------------------Function Definitions---------------------------
def get_tokens():
	response_string = ''
	try:
		connection.request("GET", LOGIN_URL);
		response = connection.getresponse();
		response_string = str(response.read().decode());
		# print('from get tokens')
		print(response.status, response.reason)
	except ConnectionError:
		raise Exception('Issue while generating tokens! [Review: get_tokens()]')
	# Init tokens list
	tokens = ["0"]*2;
	regex = r"\"4Tredir.*?value=\"(.*?)\".*?\"magic.*?value=\"(.*?)\""
	matches = re.finditer(regex, response_string, re.MULTILINE)

	# From https://regex101.com/codegen
	for matchNum, match in enumerate(matches, start=1):
	    # print ("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum = matchNum, start = match.start(), end = match.end(), match = match.group()));
	    for groupNum in range(0, len(match.groups())):
	        groupNum = groupNum + 1
	        tokens[groupNum-1]=match.group(groupNum);
	        # print ("Group {groupNum} found at {start}-{end}: {group}".format(groupNum = groupNum, start = match.start(groupNum), end = match.end(groupNum), group = match.group(groupNum)));
	if tokens[0]=="0":
		return None;
	return tokens;	        


# Establish Connection and Get KeepAlive Tokens
def login(tokens):
	headers = {'Content-type':'application/x-www-form-urlencoded'}
	post_data = {
		"username":USERNAME,
		"password":PASSWORD,
		"4Tredir":str(tokens[0]),
		"magic":str(tokens[1])
	};
	encoded_data = urllib.parse.urlencode(post_data);
	response_string = ''
	try:
		connection.request("POST", '/', encoded_data, headers);
		response = connection.getresponse();
		response_string = str(response.read().decode())
		# print('from login ')
		print(response.status, response.reason)
		if response.status!=303:
			for err_idx in range(len(ERROR_FAILS)):
				err_msg = ERROR_FAILS[err_idx]
				search_res = re.findall(err_msg, response_string);
				if len(search_res)>0:
					raise Exception(ERROR_MSG[err_idx])

	except ConnectionError:
		raise Exception('Issue while logging in! [Review: login()]')

	#KeepAlive link
	regex = r"\"(https:\/\/.*?keepalive.*?)\""
	matches = re.finditer(regex, response_string, re.MULTILINE)
	keep_alive_link = None;
	for matchNum, match in enumerate(matches, start=1):
	    # print ("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum = matchNum, start = match.start(), end = match.end(), match = match.group()))
	    for groupNum in range(0, len(match.groups())):
	        groupNum = groupNum + 1
	        keep_alive_link = match.group(groupNum)
	        break;
	        # print ("Group {groupNum} found at {start}-{end}: {group}".format(groupNum = groupNum, start = match.start(groupNum), end = match.end(groupNum), group = match.group(groupNum)))
	return keep_alive_link

def logout():
	try:
		connection.request('GET', LOGOUT_URL);
		response = connection.getresponse();
		response_string = str(response.read().decode());
	except ConnectionError:
		raise Exception("Issue while logging out! [Review: logout()]")

#------------------------Background Process------------------------------
def connect():
	global keep_alive_link;
	try:
		logout();
		tokens = get_tokens();
		keep_alive_link = login(tokens);
	except Exception as err:
		print('Please make sure if you have plugged in LAN Cable or not!');
		print("Error Reason:"+str(err));

def background_process():
	global keep_alive_link;
	if keep_alive_link==None:
		connect();
	try:
		connection.request('GET', keep_alive_link);
		response = connection.getresponse();
		response_string = str(response.read().decode())
		print(response.status, response.reason)
	except ConnectionError:
		print('Connection Error while using keep_alive_link! Refreshing the link...')
		connect();
	# print(response_string);

#--------------------------Runtime Schedules---------------------------
while True:
	#Using time sleep to minimize CPU utilisation
	background_process();
	time.sleep(5);
