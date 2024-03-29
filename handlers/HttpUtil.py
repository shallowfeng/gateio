#!/usr/bin/python
# -*- coding: utf-8 -*-


import http.client
import urllib
import json
import hashlib
import hmac


def getSign(params, secretKey):
	bSecretKey = bytes(secretKey)
	sign = ''
	for key in params.keys():
		value = str(params[key])
		sign += key + '=' + value + '&'
	bSign = bytes(sign[:-1])
	mySign = hmac.new(bSecretKey, bSign, hashlib.sha512).hexdigest()
	return mySign
def httpGet(url, resource, params=''):
	conn = http.client.HTTPSConnection(url, timeout=1000)
	conn.request("GET", resource + '/' + params)
	response = conn.getresponse()
	data = response.read().decode('utf-8')
	return json.loads(data)
def httpPost(url, resource, params, apiKey, secretKey):
	headers = {
		"Content-type" : "application/x-www-form-urlencoded",
		"KEY":apiKey,
		"SIGN":getSign(params, secretKey)
	}
	conn = httplib.HTTPSConnection(url, timeout=10)
	if params!='':
		tempParams = urllib.urlencode(params)
	else:
		tempParams=''
	conn.request("POST", resource, tempParams, headers)
	response = conn.getresponse()
	data = response.read().decode('utf-8')
	params.clear()
	conn.close()
	return json.loads(data)