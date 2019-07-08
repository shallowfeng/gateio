#!/usr/bin/env python
#coding=utf8
 
import sys
import urllib2
import re
def query_magnet(key):
	try:
		rq_body=''
		timeout='20'
		headers={'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'}
		response = urllib2.urlopen('http://www.btants.cc/q?kw=%s'%(key),headers,rq_body,timeout)
		restr=re.compile(r'''<a(\s*)(.*?)(\s*)href(\s*)=(\s*)([\"\s]*)([^\"\']+?)([\"\s]+)(.*?)>''')
		html=response.read()
		href_list=re.findall(restr,html)
		for href_tup in href_list:
			for href in href_tup:
				if href.find("magnet:?")!=-1:
					print href
	except Exception as e:
		print e
if __name__=="__main__":
	query_magnet('200gana1738')