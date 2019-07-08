#!/usr/bin/env python
# coding=utf-8

import MySQLdb
conn = MySQLdb.connect(host="localhost", user="root", passwd="123456", db="gateio",charset="utf8")
cur = conn.cursor()
