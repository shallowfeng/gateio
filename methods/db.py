#!/usr/bin/env python
# coding=utf-8 

import pymysql
conn = pymysql.connect(host="192.168.1.116", user="root", password="123456", db="gateio",charset="utf8")
cur = conn.cursor()
