#!/usr/bin/env python
# coding=utf-8

import MySQLdb
conn = MySQLdb.connect(host="localhost", user="root", passwd="", db="gateio",charset="utf8")
cur = conn.cursor()
