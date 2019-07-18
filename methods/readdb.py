#!/usr/bin/env python
# coding=utf-8

import pymysql
# 连接到数据库，返回一个数据库连接对象
def db_conn():
	conn= pymysql.connect(
#		host = "localhost",
		host = "192.168.1.129",
		port = 3306,
		user = "root",
		password = "123456",
		db = "gateio",
		charset = "utf8"
		)
	return conn

# 查询一条数据的方法，对应于只需要返回一条数据的情况，比如根据一个用户id查找该用户
def db_matchone(comm):
	# 调用db_conn来获得数据库连接
	conn = db_conn()
	cursor = conn.cursor() # 这里可以强制规定所有的查询结构都已字典而不是元祖的方式来显示，方便取值和处理
	# 创建一个指针来接受并运行传入的msyql命令，并将返回这条语句所影响的行数
	count = cursor.execute(comm)
	result = ""
	if count>0:
		# 使用fetchone方法，从查询结果中获得1条数据，这条数据就是一个字典，可直接取值
		result = cursor.fetchone()
	# 关闭指针，必须
	cursor.close()
	# 关闭数据库连接，不关闭将占用系统资源
	conn.close()
	# 返回结果，直接返回一个自己定义的字典
	return {"count":count,"result":result}

# 查询多条数据的方法，对应于需要返回多条数据的情况，比如查找所有表格内容
def db_matchall(comm):
	conn = db_conn()
	cursor = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)# 这里可以强制规定所有的查询结构都已字典而不是元祖的方式来显示，方便取值和处理
	count = cursor.execute(comm)
	result = ""
	if count>0:
		# 使用fetchall方法，从查询结果中获得所有数据，注意返回结果是一个list，但是list中的每个元素都是一行，是一个字典。是这样子的[{},{},{}]
		result = list(cursor.fetchall())
	cursor.close()
	conn.close()
	return {"count":count,"result":result}

# 进行不是查询的mysql操作，比如insert和update
def db_do(comm):
	conn = db_conn()
	cursor = conn.cursor()
	count = cursor.execute(comm)
	# 这里cursor.lastrowid返回上一次insert和update操作中所影响到的行的主键，这里一般是id，就算操作多行，也只返回最后一行的id。
	lastid = cursor.lastrowid
	cursor.close()
	conn.commit()
	# 这里conn.insert_id()返回最后一次insert操作是自增的id的值，即使这个操作不是这一次调用中进行的！！！。
	insertid = int(conn.insert_id())
	conn.close()
	return {"count":count,"lastid":lastid,"insertid":insertid}# 这里建议始终调取lastid