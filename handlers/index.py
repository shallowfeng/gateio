#!/usr/bin/env python
#coding:utf-8
from __future__ import division #是运算采用浮点除法，即2/3=0.6666。
import tornado.web
import tornado.gen 
import urllib2
from base import BaseHandler
import jinja2
from jinja2 import Environment, FileSystemLoader
from gateAPI import GateIO
import re  
import json
import threading
import time
from bs4 import BeautifulSoup 
from methods import readdb as mrd
import numpy as np
import matplotlib.pyplot as plt
## 填写 apiKey APISECRET
apiKey = 'BE42D7F2-DA9C-4283-ACFA-742A52871E8A'
secretKey = 'e8da6133d189f5d65c54bfaeac8d0124b8a599718d77f8c272f6770e5c8cd88c'
## address
btcAddress = 'your btc address'
## Provide constants
API_QUERY_URL = 'data.gateio.co'
API_TRADE_URL = 'api.gateio.co'
## Create a gate class instance
gate_query = GateIO(API_QUERY_URL, apiKey, secretKey)
gate_trade = GateIO(API_TRADE_URL, apiKey, secretKey)
#状态切换（0-kdj状态 1-macd状态）
STATUS=0
#断点日志(单独开启一个线程)
def progress_log(curr,des):
	t=threading.Thread(target=Loop_progress_log,args=(curr,des))
	t.start()
	t.join()	
def Loop_progress_log(curr,des):
	query="insert into progress_log (curr,des) values ('%s','%s')"%(curr,des)
	mrd.db_do(query)
#等级日志(单独开启一个线程)
def level_log(curr,level_obj,level_conditions,conditions_obj):
	t=threading.Thread(target=Loop_level_log,args=(curr,level_obj,level_conditions,conditions_obj))
	t.start()
	t.join()
def Loop_level_log(curr,level_obj,level_conditions,conditions_obj):
	query="insert into level_log (curr,level_obj,level_conditions,conditions_obj) values ('%s','%s','%s','%s')"%(curr,level_obj,level_conditions,conditions_obj)
	mrd.db_do(query)
#获取交易行情(单独开启一个线程)
def get_ticker(curr):
	t=threading.Thread(target=gate_query.ticker,args=(curr))
	t.start()
	t.join()
#获取当前价格(单独开启一个线程)
def get_price15(curr,t):
	n=0
	info=''
	while n<5:
		n=n+1
		try:
			info=gate_query.ticker(curr)
			n=5
		except:
			time.sleep(2)
			pass
	if info!='':
		name='price'+str(t)
		query="select * from %s where curr='%s'"%(name,curr)
		result=mrd.db_matchone(query)
		if result['count']>0:
			pricelist=json.loads(result['result']['pricelist'])
			if len(pricelist)==48:
				pricelist1=pricelist[1:]
				pricelist1.append(float(info['last']))					
				query="update %s set pricelist='%s' where curr='%s'"%(name,json.dumps(pricelist1),curr)
				mrd.db_do(query)
			else:
				pricelist.append(float(info['last']))
				query="update %s set pricelist='%s' where curr='%s'"%(name,json.dumps(pricelist),curr)
				mrd.db_do(query)
		else:
			pricelist=[info['last']]
			query="insert into %s (curr,pricelist) values ('%s','%s')"%(name,curr,json.dumps(pricelist))
			mrd.db_do(query)
	else:
		name='price'+str(t)
		query="select * from %s where curr='%s'"%(name,curr)
		result=mrd.db_matchone(query)
		if result['count']>0:
			pricelist=json.loads(result['result']['pricelist'])
			if len(pricelist)==48:
				pricelist1=pricelist[1:]
				pricelist1.append(pricelist[len(pricelist)-1])					
				query="update %s set pricelist='%s' where curr='%s'"%(name,json.dumps(pricelist1),curr)
				mrd.db_do(query)
			else:
				pricelist.append(pricelist[len(pricelist)-1])
				query="update %s set pricelist='%s' where curr='%s'"%(name,json.dumps(pricelist),curr)
				mrd.db_do(query)
		else:
			pricelist=[info['last']]
			query="insert into %s (curr,pricelist) values ('%s','%s')"%(name,curr,json.dumps(pricelist))
			mrd.db_do(query)
#求列表元素均值
def get_av(list_name):
	number=len(list_name)
	if number>0:
		sum=0
		for one in list_name:
			sum+=float(one)
		return round(sum/number,4)
	else:
		return 0
#求n次方
def get_N(x,n):
	sum=1
	if n==0:
		return sum
	else:
		for one in range(n):
			sum=sum*x
		return sum
#卖出
def sell(curr,price,amount):
	return gate_trade.sell(curr,price,amount)
#购买
def buy(curr,price,amount):
	gate_trade.buy(curr,price,amount)
#从交易所更新币种列表
def update_all_coin():
	coin_list=[]
	result=gate_trade.balances()
	coindict=result['available']
	for key in coindict:
		if float(coindict[key])>10 and key!="SWH":
			coin_list.append({"name":key,"balances":float(coindict[key])})
		elif key=="BTC":
			coin_list.append({"name":key,"balances":float(coindict[key])})
		elif key=="ETH":
			coin_list.append({"name":key,"balances":float(coindict[key])})
		elif key=="USDT":
			coin_list.append({"name":key,"balances":float(coindict[key])})
	query="select coin_list from coin_balances where id=1"
	result=mrd.db_matchone(query)
	if result['count']>0:
		query="update coin_balances set coin_list='%s' where id=1"%(json.dumps(coin_list))
		mrd.db_do(query)
	else:
		query="insert into coin_balances (coin_list) values ('%s')"%(json.dumps(coin_list))
		mrd.db_do(query)
#从数据库获取币种余额列表
def get_all_coin():
	coin_list=[]
	query="select coin_list from coin_balances where id=1"
	result=mrd.db_matchone(query)
	if result['count']>0:
		coin_list=json.loads(result['result']['coin_list'])
	return coin_list
#根据交易更新数据库币种余额列表
def update_all_coin1(status,num1,coin_obj):#(num1-usdt)
	query="select coin_list from coin_balances where id=1"
	result=mrd.db_matchone(query)
	if result['count']>0:
		coin_list=json.loads(result['result']['coin_list'])
		for one in coin_list:
			if one['name']=='USDT':
				if status=='buy':
					one['balances']=one['balances']-num1
				else:
					one['balances']=one['balances']+num1
			if one['name'] == coin_obj['name']:
				if status=='buy':
					one['balances']=one['balances']+coin_obj['balances']
				else:
					one['balances']=one['balances']-coin_obj['balances']
		query = "update coin_balances set coin_list='%s' where id=1"%(json.dumps(coin_list))
		mrd.db_do(query)
#获取某个币的余额
def get_one_balance(curr):
	coin_name=curr.split('_')[0].upper()
	coin_list=get_all_coin()
	for one in coin_list:
		if one['name']==coin_name:
			return float(one['balances'])
	return 0
#获取币种最小下单量


def get_min(curr):
	for one in gate_query.marketinfo()['pairs']:
		for key in one:
			if key==curr:
				return float(one[key]['min_amount'])
#抛售所有币种
def sell_all():
	coin_list=get_all_coin()
	data={"error":0,"data":"USDT"}
	for one in coin_list:
		if one['name']!='USDT':
			curr=one['name'].lower()+"_usdt"
			info=gate_query.ticker(curr)
			last_price=float(info['last'])#最新价格
			sell_price=last_price*0.8 #抛售价格
			result=sell(curr,sell_price,one['balances'])
			if result['result']=="true":
				if float(result['leftAmount'])<1:
					sell_amount=one['balances']
					order_number=result['orderNumber']
	#				result1=gate_trade.mytradeHistory(curr, order_number)
	#				totle=0
	#				if result1['message']=="Success":
	#					for one in result1['trades']:
	#						totle+=one['rate']*one['amount']
	#					data={"error":0}
	#				else:
	#					data={"error":1,"message":result1['message']}
	#				sell_money=totle
					data={"error":0,"data":result}
				else:
					data={"error":1,"message":"未完成出售"}
			else:
				data={"error":0,"data":result['message']}
	return data
#以比例卖出某个币
def sell_by_percent(curr,proportion):
	progress_log(curr,"in to sell1")
	get_money=0
	number=0
	coin_list=get_all_coin()
	progress_log(curr,json.dumps(coin_list))
	for one in coin_list:
		if one['name'].lower()+"_usdt"==curr:
			coin_name=one['name']
			if float(one['balances'])>0:
				selllist=get_selltype(curr,float(one['balances']*proportion))
				progress_log(curr,json.dumps(selllist))
				for one in selllist:
					sell(curr,one[0],one[1])
					get_money+=float(one[0]*one[1])
					number+=float(one[1])
				query="insert into buy_sell_log (curr,status,price,number,money,b_level,sell_type) values ('%s','%s',%f,%f,%f,%d,%d)"%(curr,'sell',get_money/number,number,round(float(get_money),2),0,1)
				mrd.db_do(query)
				coin_obj={}
				coin_obj['name']=coin_name
				coin_obj['balances']=number
				update_all_coin1('sell',get_money*0.998,coin_obj)
			else:
				progress_log(curr,"币种余额不足")
			break
#以比例挂单卖出某个币
def sell_by_percent2(curr,proportion):
	progress_log(curr,"in to sell2")
	get_money=0
	number=0
	coin_list=get_all_coin()
	progress_log(curr,json.dumps(coin_list))
	for one in coin_list:
		if one['name'].lower()+"_usdt"==curr:
			if float(one['balances'])>0:
				number=float(one['balances']*proportion)
				progress_log(curr,"获取卖家列表")
				selllist=get_selllist(curr)
				progress_log(curr,"得到卖家列表")
				get_money=number*float(selllist[len(selllist)-1][0])
				progress_log(curr,"进入挂单卖出")
				sell(curr,selllist[len(selllist)-1][0],number)
				query="insert into buy_sell_log (curr,status,price,number,money,b_level,sell_type) values ('%s','%s',%f,%f,%f,%d,%d)"%(curr,'sell',float(selllist[len(selllist)-1][0]),number,round(float(get_money),2),0,2)
				mrd.db_do(query)
				coin_obj={}
				coin_obj['name']=one['name']
				coin_obj['balances']=number
				update_all_coin1('sell',get_money*0.998,coin_obj)
			else:
				progress_log(curr,"币种余额不足")
			break
#卖出某个数量的币
def sell_by_number(curr,number):
	progress_log(curr,"in to sell3")
	get_money=0
	if float(number)>0:
		progress_log(curr,"获取卖家列表")
		selllist=get_selltype(curr,float(number))
		for one in selllist:
			sell(curr,one[0],one[1])
			get_money+=float(one[0]*one[1])
		query="insert into buy_sell_log (curr,status,price,number,money,b_level,sell_type) values ('%s','%s',%f,%f,%f,%d,%d)"%(curr,'sell',get_money/number,number,round(float(get_money),2),0,3)
		mrd.db_do(query)
		coin_obj={}
		coin_obj['name']=curr.split('_')[0].upper()
		coin_obj['balances']=number
		update_all_coin1('sell',get_money*0.998,coin_obj)
	else:
		progress_log(curr,"卖出币种数量不能为0")
#砸盘卖出某个数量的币
def sell_by_number1(curr,last_price,number):
	progress_log(curr,"in to sell4")
	if float(number)>0:
		sell(curr,last_price*0.8,number)
		query="insert into buy_sell_log (curr,status,price,number,money,b_level,is_Stoploss,sell_type) values ('%s','%s',%f,%f,%f,%d,%d,%d)"%(curr,'sell',last_price*0.8,number,0,0,1,4)
		mrd.db_do(query)
		update_all_coin()
	else:
		progress_log(curr,"卖出币种数量不能为0")
#以比例阶梯挂单卖出某个币
def sell_by_percent3(curr,b_level):
	progress_log(curr,"in to sell5")
	if b_level==1:
		proportion=0.2
	if b_level==2:
		proportion=0.375
	if b_level==2:
		proportion=0.75
	get_money=0
	number=0
	coin_list=get_all_coin()
	progress_log(curr,json.dumps(coin_list))
	for one in coin_list:
		if one['name'].lower()+"_usdt"==curr:
			if float(one['balances'])>0:
				number=float(one['balances']*proportion)
				progress_log(curr,"获取卖家列表")
				selllist=get_selllist(curr)
				progress_log(curr,"得到卖家列表")
				get_money=number*float(selllist[len(selllist)-1][0])
				progress_log(curr,"进入挂单卖出")
				if get_money*((1-proportion)/proportion)<1:
					number=float(one['balances'])
					get_money=number*float(selllist[len(selllist)-1][0])
					sell(curr,selllist[len(selllist)-1][0],number)
				else:
					sell(curr,selllist[len(selllist)-1][0],number)
				query="insert into buy_sell_log (curr,status,price,number,money,b_level,sell_type) values ('%s','%s',%f,%f,%f,%d,%d)"%(curr,'sell',float(selllist[len(selllist)-1][0]),number,round(float(get_money),2),b_level,5)
				mrd.db_do(query)
				coin_obj={}
				coin_obj['name']=one['name']
				coin_obj['balances']=number
				update_all_coin1('sell',get_money*0.998,coin_obj)
			else:
				progress_log(curr,"币种余额不足")
			break
#以比例买入某个币
def buy_by_percent(curr,proportion):
	progress_log(curr,'in to buy1')
	cost_money=0
	coin_list=get_all_coin()
	has_usdt=0
	number=0
	for one in coin_list:
		if one['name']=="USDT":
			has_usdt=float(one['balances'])
	use_usdt=has_usdt*proportion
	progress_log(curr,'可用usdt='+str(use_usdt))
	if use_usdt>1:
		buylist=get_buytype(curr,use_usdt)
		for one in buylist:
			buy(curr,one[0],one[1])
			cost_money+=float(one[0]*one[1])
			number=+float(one[1])
		query="insert into buy_sell_log (curr,status,price,number,money,b_level) values ('%s','%s',%f,%f,%f,%d)"%(curr,'buy',cost_money/number,number*0.998,round(float(cost_money),2),0)
		mrd.db_do(query)
		coin_obj={}
		coin_obj['name']=curr.split('_')[0].upper()
		coin_obj['balances']=number*0.998
		update_all_coin1('buy',cost_money,coin_obj)
	else:
		progress_log(curr,"USDT余额不足")
#以比列挂单买入某个币
def buy_by_percent2(curr,level_last):
	progress_log(curr,'in to buy2')
	cost_money=0
	coin_list=get_all_coin()
	has_usdt=0
	number=0
	for one in coin_list:
		if one['name']=="USDT":
			has_usdt=float(one['balances'])
	if level_last==0:
		use_usdt=has_usdt*2/5
	else:
		use_usdt=has_usdt
	level=level_last+1
	if use_usdt>1:
		buylist=get_buylist(curr)
		cost_money=use_usdt
		number=use_usdt/float(buylist[0][0])
		buy(curr,float(buylist[0][0]),number)
		query="insert into buy_sell_log (curr,status,price,number,money,b_level) values ('%s','%s',%f,%f,%f,%d)"%(curr,'buy',cost_money/number,number*0.998,round(float(cost_money),2),level)
		mrd.db_do(query)
		coin_obj={}
		coin_obj['name']=curr.split('_')[0].upper()
		coin_obj['balances']=number*0.998
		update_all_coin1('buy',cost_money,coin_obj)
	else:
		progress_log(curr,"USDT余额不足")
#以比列阶梯挂单买入某个币
def buy_by_percent3(curr,level_last,is_second):
	progress_log(curr,'in to buy3')
	cost_money=0
	coin_list=get_all_coin()
	has_usdt=0
	number=0
	for one in coin_list:
		if one['name']=="USDT":
			has_usdt=float(one['balances'])
	if level_last==1:
		use_usdt=has_usdt*0.1
	if level_last==2:
		if is_second==0:
			use_usdt=has_usdt*0.3
		else:
			use_usdt=has_usdt*0.22
	if level_last==3:
		if is_second==0:
			use_usdt=has_usdt*0.6
		else:
			use_usdt=has_usdt*0.42
	if level_last==4:
		if is_second==0:
			use_usdt=has_usdt*1
		else:
			use_usdt=has_usdt*1
	level=level_last
	if use_usdt>1:
		buylist=get_buylist(curr)
		cost_money=use_usdt
		number=use_usdt/float(buylist[0][0])
		buy(curr,float(buylist[0][0]),number)
		query="insert into buy_sell_log (curr,status,price,number,money,b_level,sell_type) values ('%s','%s',%f,%f,%f,%d,%d)"%(curr,'buy',cost_money/number,number*0.998,round(float(cost_money),2),level,3)
		mrd.db_do(query)
		coin_obj={}
		coin_obj['name']=curr.split('_')[0].upper()
		coin_obj['balances']=number*0.998
		update_all_coin1('buy',cost_money,coin_obj)
	else:
		progress_log(curr,"USDT余额不足")
#以比列挂单买入某个币
def buy_by_percent4(curr,proportion):
	progress_log(curr,'in to buy4')
	cost_money=0
	coin_list=get_all_coin()
	has_usdt=0
	number=0
	for one in coin_list:
		if one['name']=="USDT":
			has_usdt=float(one['balances'])
	use_usdt=has_usdt*proportion
	if use_usdt>1:
		buylist=get_buylist(curr)
		cost_money=use_usdt
		number=use_usdt/float(buylist[0][0])
		buy(curr,float(buylist[0][0]),number)
		query="insert into buy_sell_log (curr,status,price,number,money,b_level) values ('%s','%s',%f,%f,%f,%d)"%(curr,'buy',cost_money/number,number*0.998,round(float(cost_money),2),0)
		mrd.db_do(query)
		coin_obj={}
		coin_obj['name']=curr.split('_')[0].upper()
		coin_obj['balances']=number*0.998
		update_all_coin1('buy',cost_money,coin_obj)
	else:
		progress_log(curr,"USDT余额不足")
#获取卖单深度列表
def get_selltype(curr,balances):
	balances=balances
	selllist=[]
	info=gate_query.orderBook(curr)
	bids_list=info['bids']
	for one in bids_list:
		if float(one[1])>=balances:
			selllist.append([float(one[0]),balances])
			break
		else:
			selllist.append([float(one[0]),float(one[1])])
			balances=float(balances-float(one[1]))
			continue
	return selllist
#获取买单深度列表
def get_buytype(curr,use_usdt):
	use_usdt=use_usdt
	buylist=[]
	info=gate_query.orderBook(curr)
	asks_list=sorted(info['asks'])
	for one in asks_list:
		if float(one[0])*float(one[1])>=use_usdt:
			buylist.append([float(one[0]),use_usdt/float(one[0])])
			break
		else:
			buylist.append([float(one[0]),float(one[1])])
			use_usdt=float(use_usdt-one[0]*one[1])
			continue
	return buylist
#获取买家列表
def get_buylist(curr):
	info=gate_query.orderBook(curr)
	bids_list=info['bids']
	return bids_list
#获取卖家列表
def get_selllist(curr):
	info=gate_query.orderBook(curr)
	asks_list=info['asks']
	return asks_list
#判断溢价
def is_overprice(curr,price):
	query="select * from ma where curr='%s'"%(curr)
	result=mrd.db_matchone(query)
	if result['count']>0:
		ma5list=json.loads(result['result']['ma5list'])
		ma5=ma5list[len(ma5list)-1]
		progress_log(curr,"ma5="+str(ma5)+":"+"price="+str(price))
		over_obj={"status":3} #未溢价
		if price>ma5: 
			if (price-ma5)/ma5>0.008:
				over_obj={"status":1,"level":1} #高位溢价(一级)
			if (price-ma5)/ma5>0.01:
				over_obj={"status":1,"level":2} #高位溢价(二级)
			if (price-ma5)/ma5>0.015:
				over_obj={"status":1,"level":3} #高位溢价(三级)
			if (price-ma5)/ma5>0.05:
				over_obj={"status":1,"level":4} #高位溢价(四级)
		elif price<ma5:
			if (ma5-price)/ma5>0.01:
				over_obj={"status":2,"level":1} #低位溢价(一级)
			if (ma5-price)/ma5>0.02:
				over_obj={"status":2,"level":2} #低位溢价(二级)
			if (ma5-price)/ma5>0.03:
				over_obj={"status":2,"level":3} #低位溢价(三级)
			if (ma5-price)/ma5>0.05:
				over_obj={"status":2,"level":4} #低位溢价(四级)
		return over_obj
#止损线
def stop_loss_line(curr,last_price):
	stop_loss_line_obj={}
	stop_loss_line_obj['status']=0
	query="select * from buy_sell_log where curr='%s'"%(curr)
	result=mrd.db_matchall(query)
	if result['count']>0:
		cost_money=0
		coin_value=0
		number=0
		last=result['result'][len(result['result'])-1]
		status=last['status']
		if status=='buy':
			money_1=float(last['money'])
			number_1=float(last['number'])
			cost_money=money_1
			coin_value=last_price*number_1
			number=number_1
			if (cost_money-coin_value)/cost_money>0.015:
				stop_loss_line_obj['status']=1
				stop_loss_line_obj['number']=number #到达止损线
			else:
				stop_loss_line_obj['status']=0
		else:
			balance=get_one_balance(curr)
			if balance>0.001:
				query="select * from buy_sell_log where curr='%s' and status='buy'"%(curr)
				result=mrd.db_matchall(query)
				if result['count']>0:
					last_buy=result['result'][len(result['result'])-1]
					last_buy_price=last_buy['price']
					if (last_buy_price-last_price)/last_buy_price>0.015:
						stop_loss_line_obj['status']=1
						stop_loss_line_obj['number']=balance #到达止损线
					else:
						stop_loss_line_obj['status']=0
				else:
					stop_loss_line_obj['status']=0
			else:
				stop_loss_line_obj['status']=0
	else:
		stop_loss_line_obj['status']=0
	return stop_loss_line_obj
#获取收益率
def get_earnings(curr,last_price):
	earnings=0
	query="select * from buy_sell_log where curr='%s'"%(curr)
	result=mrd.db_matchall(query)
	if result['count']>0:
		cost_money=0
		coin_value=0
		last=result['result'][len(result['result'])-1]
		status=last['status']
		if status=='buy':
			money_1=float(last['money'])
			number_1=float(last['number'])
			last_b_level=last['b_level']
			if last_b_level==0:
				cost_money=money_1
				coin_value=last_price*number_1
			if last_b_level==2:
				money_2=result['result'][len(result['result'])-2]['money']
				number_2=result['result'][len(result['result'])-2]['number']
				cost_money=money_1+money_2
				coin_value=last_price*(number_1+number_2)
			else:
				cost_money=money_1
				coin_value=last_price*number_1
			earnings=(coin_value-cost_money)/cost_money
	return earnings
#判断交叉
def overlap(line,line1):
	line_1=line[::-1] #倒序
	line1_1=line1[::-1]
	if line_1[0]>=line1_1[0] and line_1[1]<line1_1[1]:
		return 1 #line上穿line1
	elif line_1[0]<=line1_1[0] and line_1[1]>line1_1[1]:
		return 2 #line下穿line1
	else:
		return 0
#三点法预测交叉
def pre_overlap(line,line1):
	status=0
	trend_three_line=trend_three(line)
	trend_three_line1=trend_three(line1)
	if line[len(line)-1]>line1[len(line1)-1]:
		if (trend_three_line==4 or trend_three_line==6) and (trend_three_line1==2 or trend_three_line1==6):
			status=2 #line即将下穿line1
	else:
		if (trend_three_line1==5 or trend_three_line1==4) and (trend_three_line==1 or trend_three_line==2 or trend_three_line==5):
			status=1 #line即将上穿line1
	return status
#小时交叉
def overlap_oneHour(line,line1):
	line_1=line[len(line)-4:]
	line1_1=line1[len(line)-4:]
	for one in range(0,3):
		if line_1[one]<line1_1[one] and line_1[one+1]>=line1_1[one+1]:
			return 1 #line小时上穿line1
		elif line_1[one]>line1_1[one] and line_1[one+1]<=line1_1[one+1]:
			return 2 #line小时下穿line1
		else:
			continue
	return 0
#求斜率列表
def slope(line):
	slopelist=[]
	for one in range(len(line)-1):
		if line[one]>line[one+1]:
			slopelist.append(float(line[one]-line[one+1]))
		else:
			slopelist.append(float(line[one+1]-line[one]))
	return slopelist
#判断单弧状态(0-不是单弧 1-速降 2-缓降 3-速升 4-缓升)(line至少3个点)
def arc(line):
	line1=sorted(line) #从小到大
	line2=sorted(line).reverse() #从大到小
	line_slope=slope(line)
	if line==line1 or line==line2:
		if line==line2:
			if line_slope[0]<line_slope[len(line_slope)-1]:
				return 1
			else:
				return 2
		else:
			if line_slope[0]<line_slope[len(line_slope)-1]:
				return 3
			else:
				return 4
	else:
		return 0
#判断双弧状态(0-不是双弧 1-凸狐 2-凹狐)
def arcBouth(line):
	line1=line[len(line)-8:]
	line2=sorted(line1) #从小到大
	a=line1[0]
	b=line1[len(line1)-1]
	line_min=line2[0]
	line_max=line2[len(line2)-1]
	if a<line_max and b<line_max:
		return 2
	elif a>line_min and b>line_min:
		return 1
	else:
		return 0
#3点法判断趋势(1-上优折 2-上劣折 3-下优折 4-下劣折 5-凹折 6-凸折)
def trend_three(line):
	status=0
	line=line[len(line)-3:]
	line1=sorted(line)
	a=float(line[0])
	b=float(line[1])
	c=float(line[2])
	line_min=line1[0]
	line_max=line1[len(line1)-1]
	if a==line_min and c==line_max:
		if (b-a)<(c-b):
			status=1
		elif (b-a)>(c-b):
			status=2
	if a==line_max and c==line_min:
		if (a-b)>(b-c):
			status=3
		elif (a-b)<(b-c):
			status=4
	if b==line_min:
		status=5
	if b==line_max:
		status=6
	return status
#判断趋势(1-单优 2-单劣 3-双优 4-双劣 5-多优 6-多劣)
def trend(line):
	status=0
	line=line[len(line)-8:]
	a=line[0]
	b=line[len(line)-1]
	line1=sorted(line) #从小到大
	line2=sorted(line).reverse() #从大到小
	coin_min=line1[0]
	coin_max=line1[len(line1)-1]
	if a>b and a==coin_max:
		if b==coin_min: 
			if line==line2:
				if arc(line)==2:
					status=1
		elif coin_min<b:
			line_1=line[0:line.index(coin_min)+1]
			line_2=line[line.index(coin_min)+1:]
			if len(line_1)>=5:
				if arc(line_1)==2:
					status=3
			else:
				if arc(line_2)==3:
					status=3
		else:
			status=0
	elif a<b and a==coin_min:
		if b==coin_max:
			if line==line1:
				if arc(line)==4:
					status=2
		elif b<coin_max:
			line_1=line[0:line.index(coin_max)+1]
			line_2=line[line.index(coin_max)+1:]
			if len(line_1)>=5:
				if arc(line_1)==4:
					status=4
			else:
				if arc(line_2)==1:
					status=4
		else:
			status=0
	elif a>b and a<coin_max and b>=coin_min:
		index_max=line.index(coin_max)
		index_min=line.index(coin_min)
		if index_max<index_min:
			status=5
	elif a<b and a>coin_min and b<=coin_max:
		index_max=line.index(coin_max)
		index_min=line.index(coin_min)
		if index_max>index_min:
			status=6
	else:
		status=0
	return status
#判断操作(0-买 1-卖 2-观望)
def operation_status(line):
	v_trend=trend(line)
	v_arcBouth=arcBouth(line)
	if v_trend==1 or v_trend==3 or v_trend==5:
		return 0
	elif v_trend==2 or v_trend==4 or v_trend==6:
		return 1
	else:
		if v_arcBouth==1:
			return 1
		elif v_arcBouth==2:
			return 0
		else:
			return 2
#判断高低峰(0-正常 1-高峰 2-低峰)(24个点)
def peak_slack(line):
	line=line[len(line)-24:]
	status=0
	coin_min=sorted(line)[0]
	coin_max=sorted(line)[len(line)-1]
	coin_ave=(coin_max-coin_min)/2
#	now=line[len(line)-1]
	now_overlap=(line[len(line)-2]+line[len(line)-1])/2 #交叉值
	ave=(coin_min+coin_max)/2
	if now_overlap>ave:
		if (now_overlap-ave)/coin_ave>0.6:
			status=1
	else:
		if (ave-now_overlap)/coin_ave>0.6:
			status=2
	return status
#判断高低峰(0-正常 1-高峰 2-低峰)(所有点)
def peak_slack1(line):
	status=0
	coin_min=float(sorted(line)[0])
	coin_max=float(sorted(line)[len(line)-1])
	coin_ave=round((coin_max-coin_min)/2,4)
	now_overlap=float(line[len(line)-1]) #当前值
	ave=round((coin_min+coin_max)/2,4)
	if now_overlap>ave:
		if (now_overlap-ave)/coin_ave>0.6:
			status=1
	else:
		if (ave-now_overlap)/coin_ave>0.8:
			status=2
	return status
#求曲线小时极小值
def extreme(line):
	line=line[len(line)-4:]
	return sorted(line)[0]
#求曲线小时极大值
def extreme_max(line):
	line=line[len(line)-4:]
	line1=sorted(line)
	return line1[len(line1)-1]
#获取曲线买卖等级()
def level(curr,label):
	level=0
	level_conditions={}
	key=''
	status=''
	if label=='kdj':
		key='kdj'
		query="select * from kdj where curr='%s'"%(curr)
		result=mrd.db_matchone(query)
		if result['count']>0:
			klist=json.loads(result['result']['k'])
			dlist=json.loads(result['result']['d'])
			jlist=json.loads(result['result']['j'])
			k_last=klist[len(klist)-2]
			d_last=dlist[len(dlist)-2]
			j_last=jlist[len(jlist)-2]
			k_extreme_min=extreme(klist)
			j_extreme_min=extreme(jlist)
			k_trend_three=trend_three(klist)
			j_trend_three=trend_three(jlist)
			k_extreme_max=extreme_max(klist)
			j_extreme_max=extreme_max(jlist)
			k_d=overlap(klist,dlist)
			j_d=overlap(jlist,dlist)
			k_d_pre=pre_overlap(klist,dlist)
			j_d_pre=pre_overlap(jlist,dlist)
			peak_slack_dlist=peak_slack(dlist)
			trend_dlist=trend(dlist)
			level_conditions['k_last']=k_last
			level_conditions['d_last']=d_last
			level_conditions['j_last']=j_last
			level_conditions['k_trend_three']=k_trend_three
			level_conditions['j_trend_three']=j_trend_three
			level_conditions['k_extreme_min']=k_extreme_min
			level_conditions['j_extreme_min']=j_extreme_min
			level_conditions['k_extreme_max']=k_extreme_max
			level_conditions['j_extreme_max']=j_extreme_max
			level_conditions['k_d']=k_d
			level_conditions['j_d']=j_d
			level_conditions['k_d_pre']=k_d_pre
			level_conditions['j_d_pre']=j_d_pre
			level_conditions['peak_slack_dlist']=peak_slack_dlist
			level_conditions['trend_dlist']=trend_dlist

			if k_last<20 and d_last<20 and j_last<20:
				if k_d==1 and j_d==1:
					level=1
					status='buy'
			elif k_last>90 and d_last>90 and j_last>90:
				if ((k_trend_three==6 or k_trend_three==4) and j_trend_three==4) or (k_d_pre==2 and j_d_pre==2):
					level=1
					status='sell'
			elif k_last<20 and d_last<25 and j_last<20 and j_extreme_min<0:
				if k_d==1 and j_d==1:
					if trend_dlist==1 or trend_dlist==3 or trend_dlist==5:
						level=2
						status='buy'
					elif trend_dlist==0 and peak_slack_dlist==2:
						level=2
						status='buy'
			elif k_last>80 and d_last>80 and j_last>80:
				if ((k_trend_three==6 or k_trend_three==4) and j_trend_three==4) or (k_d_pre==2 and j_d_pre==2):
					if peak_slack_dlist==1:
						level=2
						status='sell'
			elif k_last>70 and d_last>70 and j_last>70:
				if ((k_trend_three==6 or k_trend_three==4) and j_trend_three==4) or (k_d_pre==2 and j_d_pre==2):
					if peak_slack_dlist==1:
						level=3
						status='sell'
			elif k_last>65 and d_last>65 and j_last>65:
				if ((k_trend_three==6 or k_trend_three==4) and j_trend_three==4) or (k_d_pre==2 and j_d_pre==2):
					if peak_slack_dlist==1 and j_extreme_max>100 and k_extreme_max>70:
						level=3
						status='sell'
			elif k_last<35 and d_last<35 and j_last<35:
				if k_d==1 and j_d==1:
					if j_extreme_min<10 and k_extreme_min<20:
						level=3
						status='buy'
			elif k_last<35 and d_last<35 and j_last<35:
				if k_d==1 and j_d==1:
					if j_extreme_min<-10:
						level=3
						status='buy'
			elif k_last<40 and d_last<40 and j_last<40:
				if k_d==1 and j_d==1:
					if j_extreme_min<-20:
						level=3
						status='buy'
	if label=='macd':
		key='macd'
		query="select * from macd where curr='%s'"%(curr)
		result=mrd.db_matchone(query)
		if result['count']>0:
			diflist=json.loads(result['result']['dif'])
			dealist=json.loads(result['result']['dea'])
			dif_last=diflist[len(diflist)-1]
			dea_last=dealist[len(dealist)-1]
			if dif_last<0 and dea_last<0 and overlap(diflist,dealist)==1:
				if extreme(diflist)<dif_last and extreme(diflist)<dif_last[0]:
					level=2
					status='buy'
			if dif_last>0 and dea_last>0 and overlap(diflist,dealist)==2:
				if trend(diflist)==2 or trend(diflist)==4:
					level=2
					status='sell'
	if label=='ma':
		key='ma'
		query="select * from ma where curr='%s'"%(curr)
		result=mrd.db_matchone(query)
		if result['count']>0:
			ma5list=json.loads(result['result']['ma5list'])
			ma10list=json.loads(result['result']['ma10list'])
			ma5_last=ma5list[len(ma5list)-1]
			if overlap(ma5list,ma10list)==1 and extreme(ma5list)<ma5_last:
				level=2
				status='buy'
			if overlap(ma5list,ma10list)==2 and extreme_max(ma5list)>ma5_last:
				level=2
				status='sell'
	return {'key':key,'status':status,'level':level,'level_conditions':json.dumps(level_conditions)}
class IndexHandler(BaseHandler):
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def get(self):
		env = Environment(loader=FileSystemLoader("templates"))
		template = env.get_template("01-index.html")
		page = template.render(
		)
		self.write(page)
		self.finish()
	def post(self):
		action = self.get_argument("action")
		if action=="getinfo":
			url=str(self.get_argument("url"))
			header = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36',
			'Content-Type':'application/x-www-form-urlencoded'
			}  
			response = urllib2.urlopen(url) 
			info=response.read()
			data={"error":0,"data":info}
			self.write(data)
		if action=="getinfo1":
			api=str(self.get_argument("api"))
			info=''
			if api=="pairs":#所有交易对
				info=gate_query.pairs()
			if api=="marketinfo":#交易市场订单参数
				info=gate_query.marketinfo()
			if api=="marketlist":#交易市场行情
				info=gate_query.marketlist()
			if api=="tickers":#单项交易行情
				info=gate_query.ticker("btc_usdt")
			if api=="orderBooks":#市场深度
				info=gate_query.orderBook("btc_usdt")
			if api=="balances":#账户余额
				info=gate_trade.balances()
			if api=="tradeHistory":#交易历史
				info=gate_trade.tradeHistory("btc_usdt")
			data={"error":0,"data":info}
			self.write(data)
		if action=="historyprice":
			curr=self.get_argument("curr")
			info=gate_query.ticker(curr)
			t=int(self.get_argument("t"))
			query="select * from history_price where curr='%s'"%(curr)
			result=mrd.db_matchone(query)
			pname='price_s'+str(t)
			sname='status_s'+str(t)
			if result['count']>0:
				price=result['result'][pname]
				if t==10:
					if (price-float(info['last']))/price>0.005:
						sname=result['result'][sname]+1
						query="insert into warnning_log (curr,price,status) values ('%s',%f,'%s')"%(curr,float(info['last']),sname)
						mrd.db_do(query)
					else:
						sname=result['result'][sname]
					query="update history_price set price_s10=%f,status_s10=%d where curr='%s'"%(float(info['last']),sname,curr)
					mrd.db_do(query)	
				if t==30:
					if (price-float(info['last']))/price>0.01:
						sell_all()
						sname=result['result'][sname]+1
						query="insert into warnning_log (curr,price,status) values ('%s',%f,'%s')"%(curr,float(info['last']),sname)
						mrd.db_do(query)
					else:
						sname=result['result'][sname]
					query="update history_price set price_s30=%f,status_s30=%d where curr='%s'"%(float(info['last']),sname,curr)
					mrd.db_do(query)
				if t==60:
					if (price-float(info['last']))/price>0.02:
						sell_all()
						sname=result['result'][sname]+1
						query="insert into warnning_log (curr,price,status) values ('%s',%f,'%s')"%(curr,float(info['last']),sname)
						mrd.db_do(query)
					else:
						sname=result['result'][sname]	
					query="update history_price set price_s60=%f,status_s60=%d where curr='%s'"%(float(info['last']),sname,curr)
					mrd.db_do(query)				
			else:
				query="insert into history_price (curr,price_s10,price_s30,price_s60,status_s10,status_s30,status_s60) values ('%s',%f,%f,%f,%d,%d,%d)"%(curr,float(info['last']),float(info['last']),float(info['last']),0,0,0)
				mrd.db_do(query)
			data={"error":0,"data":info}
			self.write(data)
		if action=="sellall":
			data=sell_all()
			self.write(data)
		if action=="historyprice1":
			curr=self.get_argument("curr")
			t=int(self.get_argument("t"))
			p=threading.Thread(target=get_price15,args=(curr,t))
			p.start()
			p.join()
			data={"error":0}
			self.write(data)
		self.finish()
class MaHandler(BaseHandler):
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self):
		action = self.get_argument("action")
		curr=self.get_argument("curr")
		if action=="getMA":
			t=int(self.get_argument("t"))
			name1='price'+str(t)
			query="select * from %s where curr='%s'"%(name1,curr)
			result=mrd.db_matchone(query)
			if result['count']>0:
				pricelist=json.loads(result['result']['pricelist'])
				if len(pricelist)>20:
					pricelist_5=pricelist[len(pricelist)-5:]
					pricelist_10=pricelist[len(pricelist)-10:]
					pricelist_20=pricelist[len(pricelist)-20:]
					ave_5=get_av(pricelist_5)
					ave_10=get_av(pricelist_10)
					ave_20=get_av(pricelist_20)
					query="select * from ma where curr='%s'"%(curr)
					result1=mrd.db_matchone(query)
					if result1['count']>0:
						ma5list=json.loads(result1['result']['ma5list'])
						ma10list=json.loads(result1['result']['ma10list'])
						ma20list=json.loads(result1['result']['ma20list'])
						if len(ma5list)==96:
							ma5list1=ma5list[1:]
							ma10list1=ma10list[1:]
							ma20list1=ma20list[1:]
							ma5list1.append(ave_5)
							ma10list1.append(ave_10)
							ma20list1.append(ave_20)
							query="update ma set ma5list='%s',ma10list='%s',ma20list='%s' where curr='%s'"%(json.dumps(ma5list1),json.dumps(ma10list1),json.dumps(ma20list1),curr)
							mrd.db_do(query)
						else:
							ma5list.append(ave_5)
							ma10list.append(ave_10)
							ma20list.append(ave_20)
							query="update ma set ma5list='%s',ma10list='%s',ma20list='%s' where curr='%s'"%(json.dumps(ma5list),json.dumps(ma10list),json.dumps(ma20list),curr)
							mrd.db_do(query)
					else:
						ma5list=[ave_5]
						ma10list=[ave_10]
						ma20list=[ave_20]
						query="insert into ma (curr,ma5list,ma10list,ma20list) values ('%s','%s','%s','%s')"%(curr,json.dumps(ma5list),json.dumps(ma10list),json.dumps(ma20list))
						mrd.db_do(query)
			data={"error":0}
			self.write(data)
		if action=="getMA_line":
			query="select * from ma where curr='%s'"%(curr)
			result=mrd.db_matchone(query)
			if result['count']>0:
				ma5list=json.loads(result['result']['ma5list'])
				ma10list=json.loads(result['result']['ma10list'])
				ma20list=json.loads(result['result']['ma20list'])
				#x5=np.arange(0,len(ma5list)*15,15)
				#y5=np.array(ma5list)
				#x10=np.arange(0,len(ma10list)*15,15)
				#y10=np.array(ma10list)
				#x20=np.arange(0,len(ma20list)*15,15)
				#y20=np.array(ma20list)
				#plt.figure(1)
				#plt.title(curr)
				#plt.xlabel('iteration times')
				#plt.ylabel('price')
				#plt.plot(x5,y5,color='#BF9022',label='MA5')
				#plt.plot(x10,y10,color='#47A4BE',label='MA10')
				#plt.plot(x20,y20,color='#E370CE',label='MA20')
				#plt.show()
				data={"error":0,"ma5":ma5list,"ma10":ma10list,"ma20":ma20list}
			else:
				data={"error":-1,"message":'暂无数据'}
			self.write(data)
		self.finish()
class KdjHandler(BaseHandler):
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self):
		action = self.get_argument("action")
		curr=self.get_argument("curr")
		if action=="getKdj":
			RSV=0
			t=int(self.get_argument("t"))
			name1='price'+str(t)
			query="select * from %s where curr='%s'"%(name1,curr)
			result=mrd.db_matchone(query)
			if result['count']>0:
				pricelist=json.loads(result['result']['pricelist'])
				if len(pricelist)>9:
					pricelist_9=sorted(pricelist[len(pricelist)-9:])
					high=pricelist_9[len(pricelist_9)-1]
					low=pricelist_9[0]
					last=pricelist[len(pricelist)-1]
					RSV=(last-low)/(high-low)*100
			query="select * from kdj where curr='%s'"%(curr)
			result=mrd.db_matchone(query)
			if result['count']>0:
				klist=json.loads(result['result']['k'])
				dlist=json.loads(result['result']['d'])
				jlist=json.loads(result['result']['j'])
				k_last=klist[len(klist)-1]
				d_last=dlist[len(dlist)-1]
				j_last=jlist[len(jlist)-1]
				k_now=round(2*k_last/3+RSV/3,2)
				d_now=round(2*d_last/3+k_now/3,2)
				j_now=round(3*k_now-2*d_now,2)
				if len(klist)==96:
					klist1=klist[1:]
					dlist1=dlist[1:]
					jlist1=jlist[1:]
					klist1.append(k_now)
					dlist1.append(d_now)
					jlist1.append(j_now)
					query="update kdj set k='%s',d='%s',j='%s' where curr='%s'"%(klist1,dlist1,jlist1,curr)
					mrd.db_do(query)
				else:
					klist.append(k_now)
					dlist.append(d_now)
					jlist.append(j_now)
					query="update kdj set k='%s',d='%s',j='%s' where curr='%s'"%(klist,dlist,jlist,curr)
					mrd.db_do(query)
			else:
				k=[50]
				d=[50]
				j=[50]
				query="insert into kdj (curr,k,d,j) values ('%s','%s','%s','%s')"%(curr,json.dumps(k),json.dumps(d),json.dumps(j))
				mrd.db_do(query)
			data={"error":0}
			self.write(data)
		if action=="getkdj_line":
			query="select * from kdj where curr='%s'"%(curr)
			result=mrd.db_matchone(query)
			if result['count']>0:
				k=json.loads(result['result']['k'])
				d=json.loads(result['result']['d'])
				j=json.loads(result['result']['j'])
				#xk=np.arange(0,len(k)*15,15)
				#yk=np.array(k)
				#xd=np.arange(0,len(d)*15,15)
				#yd=np.array(d)
				#xj=np.arange(0,len(j)*15,15)
				#yj=np.array(j)	
				#plt.figure(2)
				#plt.title(curr)
				#plt.xlabel('iteration times')
				#plt.ylabel('values')
				#plt.plot(xk,yk,color='#BF9022',label='k')
				#plt.plot(xd,yd,color='#47A4BE',label='d')
				#plt.plot(xj,yj,color='#E370CE',label='j')
				#plt.show()
				data={"error":0,"k":k,"d":d,"j":j}
			else:
				data={"error":-1,"message":'暂无数据'}
			self.write(data)
		self.finish()
class MacdHandler(BaseHandler):
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self):
		action = self.get_argument("action")
		curr=self.get_argument("curr")
		if action=="getMACD":
			t=int(self.get_argument("t"))
			query="select * from macd where curr='%s'"%(curr)
			result1=mrd.db_matchone(query)
			if result1['count']>0:
				diflist=json.loads(result1['result']['dif'])
				dealist=json.loads(result1['result']['dea'])
				ema12=float(result1['result']['ema12'])
				ema26=float(result1['result']['ema26'])
				query="select * from price15 where curr='%s'"%(curr)
				info1=mrd.db_matchone(query)
				if info1['count']>0:
					pricelist=json.loads(info1['result']['pricelist'])
					last=pricelist[len(pricelist)-1]
				else:
					info=gate_query.ticker(curr)
					last=float(info['last'])
				ema12_now=ema12*11/13+last*2/13
				ema26_now=ema26*25/27+last*2/27
				DIF=round(float(ema12_now-ema26_now),4)
				if len(diflist)==96:
					diflist1=diflist[1:]
					dealist1=dealist[1:]
					DEA=round(DIF/5+dealist1[len(dealist1)-1]*4/5,4)
					diflist1.append(DIF)
					dealist1.append(DEA)
					query="update macd set dif='%s',dea='%s',ema12=%f,ema26=%f where curr='%s'"%(diflist1,dealist1,ema12_now,ema26_now,curr)
					mrd.db_do(query)
				else:
					DEA=round(DIF/5+diflist[len(diflist)-1]*4/5,4)
					diflist.append(DIF)
					dealist.append(DEA)
					query="update macd set dif='%s',dea='%s',ema12=%f,ema26=%f where curr='%s'"%(diflist,dealist,ema12_now,ema26_now,curr)
					mrd.db_do(query)
			else:
				name1='price'+str(t)
				query="select * from %s where curr='%s'"%(name1,curr)
				result=mrd.db_matchone(query)
				if result['count']>0:
					pricelist=json.loads(result['result']['pricelist'])
					if len(pricelist)>26:
						pricelist_12=pricelist[len(pricelist)-12:][::-1]
						pricelist_26=pricelist[len(pricelist)-26:][::-1]
						a=2/13
						a1=2/27
						sum=0
						sum1=0
						for k,v in enumerate(pricelist_12):
							sum+=get_N((1-a),k)*v
						for k1,v1 in enumerate(pricelist_26):
							sum1+=get_N((1-a1),k1)*v1
						EMA12=round(a*sum,4)
						EMA26=round(a1*sum1,4)
						DIF=round(float(EMA12-EMA26),4)
						dif=[DIF]
						dea=[DIF]
						query="insert into macd (curr,dif,dea,ema12,ema26) values ('%s','%s','%s',%f,%f)"%(curr,json.dumps(dif),json.dumps(dea),EMA12,EMA26)
						mrd.db_do(query)
			data={"error":0}
			self.write(data)
		if action=="getmacd_line":
			query="select * from macd where curr='%s'"%(curr)
			result=mrd.db_matchone(query)
			if result['count']>0:
				dif=json.loads(result['result']['dif'])
				dea=json.loads(result['result']['dea'])
				#xdif=np.arange(0,len(dif)*1,1)
				#ydif=np.array(dif)
				#xdea=np.arange(0,len(dea)*1,1)
				#ydea=np.array(dea)
				#plt.figure(3)
				#plt.title(curr)
				#plt.xlabel('iteration times')
				#plt.ylabel('values')
				#plt.plot(xdif,ydif,color='#BF9022',label='DIF')
				#plt.plot(xdea,ydea,color='#47A4BE',label='DEA')
				#plt.show()
				data={"error":0,"dif":dif,"dea":dea}
			else:
				data={"error":-1,"message":'暂无数据'}
			self.write(data)
		self.finish()

class MonitoringHandler(BaseHandler):
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self):
		global STATUS
		action = self.get_argument("action")
		curr=self.get_argument("curr")
		if action=="monitoring_overprice":
			status=''
			info=gate_query.ticker(curr)
			last_price=float(info['last'])#最新价格
			over_obj=is_overprice(curr,last_price)
			stop_loss_line_obj=stop_loss_line(curr,last_price)
			stop_loss_line_status=stop_loss_line_obj['status']
			conditions_obj={}
			conditions_obj['coin_value']=last_price
			query="select * from buy_sell_log where curr='%s'"%(curr)
			result=mrd.db_matchall(query)
			if result['count']>0:
				last=result['result'][len(result['result'])-1]
				status=last['status']
				level_last=last['b_level']
				price_last=last['price']
				is_Stoploss=last['is_Stoploss']
				sell_type=last['sell_type']
				status1=result['result'][len(result['result'])-2]['status']
				if is_Stoploss==1:
					STATUS=1
				else:
					STATUS=0
			if stop_loss_line_status==0:
				if over_obj['status']==1:
					progress_log(curr,"高位溢价")
					query="select * from kdj where curr='%s'"%(curr)
					result=mrd.db_matchone(query)
					if result['count']>0:
						klist=json.loads(result['result']['k'])
						jlist=json.loads(result['result']['j'])
						dlist=json.loads(result['result']['d'])
						trend_three_klist=trend_three(klist)
						trend_three_jlist=trend_three(jlist)
						j_last=jlist[len(jlist)-1]
						peak_slack_dlist=peak_slack(dlist)
						earnings=get_earnings(curr,last_price)
						conditions_obj={}
						conditions_obj['trend_three_klist']=trend_three_klist
						conditions_obj['trend_three_jlist']=trend_three_jlist
						conditions_obj['j_last']=j_last
						conditions_obj['peak_slack_dlist']=peak_slack_dlist
						conditions_obj['earnings']=earnings
						level_log(curr,'高位溢价',json.dumps({"level":over_obj['level']}),json.dumps(conditions_obj))
						is_twist=0
						if ((trend_three_jlist==2 or trend_three_jlist==6) and (trend_three_klist==2 or trend_three_klist==6)) or j_last>115 and peak_slack_dlist==1:
							is_twist=1
						else:
							is_twist=0
						if over_obj['level']==1:
							if earnings>0.01:#收益率达到1%
								if status=='buy':
									progress_log(curr,'一级高价溢位,收益率达到1%,且还未首次出售,采用挂单方式卖出三分之一')
									sell_by_percent2(curr,0.3)
								if is_twist==1:
									progress_log(curr,'一级高价溢位,收益率达到1%,且达到转折点,全部卖出')
									if status=='sell':
										if status1!='sell':
											sell_by_percent(curr,1)
							else:
								if is_twist==1:
									if status=='buy':
										progress_log(curr,'一级高价溢位,收益率未到1%,但达到转折点,且一次还未出售,采用挂单方式卖出二分之一')
										sell_by_percent2(curr,0.5)
								if trend_three_jlist==6 and j_last>85 and earnings>0.005:
									if status=='buy':
										progress_log(curr,'一级高价溢位,收益率未到1%,但预测到达最高价,保本卖出')
										sell_by_percent2(curr,0.5)
						if over_obj['level']==2:
							if earnings>0.02:#收益率达到2%
								if status=='buy':
									progress_log(curr,'二级高价溢位,收益率达到2%,且还未首次出售,采用挂单方式卖出三分之二')
									sell_by_percent2(curr,0.6)
								if status=='sell' and status1!='sell':
									progress_log(curr,'二级高价溢位,收益率达到2%,已出售一次,采用挂单方式卖出二分之一')
									sell_by_percent2(curr,0.5)
								if is_twist==1:
									progress_log(curr,'二级高价溢位,收益率达到2%,全部卖出')
									sell_by_percent(curr,1)
							else:
								if is_twist==1:
									progress_log(curr,'二级高价溢位,收益率未到2%,但达到转折点,且已出售过一次,采用挂单方式卖出二分之一')
									if status=='sell':
										if status1!='sell':
											sell_by_percent2(curr,0.5)
						if over_obj['level']==3:
							progress_log(curr,'三级高价溢位,采用阶梯方式卖出')
							if sell_type==5:
								sell_by_percent3(curr,level_last+1)
							else:
								sell_by_percent3(curr,1)
							if is_twist==1:
								progress_log(curr,'三级高价溢位,达到转折点,全部卖出')
								sell_by_percent(curr,1)
						if over_obj['level']==4:
							progress_log(curr,'爆拉状态,观望')
				elif over_obj['status']==2:
					progress_log(curr,"低位溢价")
					query="select * from kdj where curr='%s'"%(curr)
					result=mrd.db_matchone(query)
					if result['count']>0:
						klist=json.loads(result['result']['k'])
						jlist=json.loads(result['result']['j'])
						dlist=json.loads(result['result']['d'])
						trend_three_klist=trend_three(klist)
						trend_three_jlist=trend_three(jlist)
						d_last=dlist[len(dlist)-1]
						peak_slack_dlist=peak_slack(dlist)
						conditions_obj={}
						conditions_obj['trend_three_klist']=trend_three_klist
						conditions_obj['trend_three_jlist']=trend_three_jlist
						conditions_obj['d_last']=d_last
						conditions_obj['peak_slack_dlist']=peak_slack_dlist
						level_log(curr,'低位溢价',json.dumps({"level":over_obj['level']}),json.dumps(conditions_obj))
						if STATUS==0:
							if over_obj['level']==1:
								if (trend_three_klist==5 or trend_three_klist==3) and trend_three_jlist==5 and (d_last<20 or peak_slack_dlist==2):
									if status=='sell':
										buy_by_percent3(curr,1,0)
										progress_log(curr,'一级低价溢位,达到转折点,首次购入')
							if over_obj['level']==2:
								if (trend_three_klist==5 or trend_three_klist==3) and trend_three_jlist==5 and (d_last<20 or peak_slack_dlist==2):
									if status=='sell':
										buy_by_percent3(curr,2,0)
										progress_log(curr,'二级低价溢位,达到转折点,首次购入')
									if status=='buy' and sell_type==3 and level_last==1:
										buy_by_percent3(curr,2,1)
										progress_log(curr,'二级低价溢位,达到转折点,二次补入')
								if (price_last-last_price)/last_price>0.01:
									if status=='buy' and sell_type==3 and level_last==1:
										buy_by_percent3(curr,2,1)
										progress_log(curr,'二级低价溢位,未到转折点,但价格低于上次购买价格1%,二次补入')
							if over_obj['level']==3:
								if (trend_three_klist==5 or trend_three_klist==3) and trend_three_jlist==5 and (d_last<20 or peak_slack_dlist==2):
									if status=='sell':
										buy_by_percent3(curr,3,0)
										progress_log(curr,'三级低价溢位,达到转折点,首次购入')
									if status=='buy' and sell_type==3 and level_last==2:
										buy_by_percent3(curr,3,1)
										progress_log(curr,'三级低价溢位,达到转折点,,三次补入')
								if (price_last-last_price)/last_price>0.01:
									if status=='buy' and sell_type==3 and level_last==2:
										buy_by_percent3(curr,3,1)
										progress_log(curr,'三级低价溢位,未到转折点,但价格低于上次购买价格1%,三次补入')
							if over_obj['level']==4:
								if (trend_three_klist==5 or trend_three_klist==3) and trend_three_jlist==5 and (d_last<20 or peak_slack_dlist==2):
									if status=='sell':
										buy_by_percent3(curr,4,0)
										progress_log(curr,'四级低价溢位,达到转折点,首次购入')
									if status=='buy' and sell_type==3 and level_last==3:
										buy_by_percent3(curr,4,1)
										progress_log(curr,'四级低价溢位,达到转折点,四次补入')
								if (price_last-last_price)/last_price>0.01:
									if status=='buy' and sell_type==3 and level_last==3:
										buy_by_percent3(curr,4,1)
										progress_log(curr,'四级低价溢位,未到转折点,但价格低于上次购买价格1%,四次补入')
						else:
							progress_log(curr,"切换状态为2")
							query="select * from macd where curr='%s'"%(curr)
							result=mrd.db_matchone(query)
							if result['count']>0:
								dif_list=result['result']['dif']
								dea_list=result['result']['dea']
								if overlap(dif_list,dea_list)==1:
									buy_by_percent(curr,1)
									progress_log(curr,"切换状态为1")
									STATUS=0
					query="select * from over_price where curr='%s'"%(curr)
					result=mrd.db_matchone(query)
					if result['count']>0:
						overprice=json.loads(result['result']['overprice'])
						if len(overprice)<360:
							overprice.append(over_obj['status'])
							query="update over_price set overprice='%s' where curr='%s'"%(json.dumps(overprice),curr)
							mrd.db_do(query)
						else:
							overprice1=overprice[1:]
							overprice1.append(over_obj['status'])
							query="update over_price set overprice='%s' where curr='%s'"%(json.dumps(overprice1),curr)
							mrd.db_do(query)
					else:
						overprice=[over_obj['status']]
						query="insert into over_price (curr,overprice) values ('%s','%s')"%(curr,json.dumps(overprice))
						mrd.db_do(query)
				else:
					if get_earnings(curr,last_price)>0.01:#收益率达到1%,采用挂单方式卖出一半
						sell_by_percent2(curr,0.5)
					progress_log(curr,"未溢价")
			else:
				stop_loss_line_number=stop_loss_line_obj['number']
				sell_by_number1(curr,last_price,stop_loss_line_number)
				level_log(curr,'到达止损线','',json.dumps(conditions_obj))
			data={"error":0}
			self.write(data)
		self.finish()
class AutotradingHandler(BaseHandler):
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self):
		global STATUS
		curr=self.get_argument("curr")
		level_obj=level(curr,'kdj')
		level_number=0
		buy_sell_status=''
		dif_peak_slack1=0
		dea_peak_slack1=0
		dif_dea_overlap=0
		dif_dea_overlap_pre=0
		query="select * from buy_sell_log where curr='%s'"%(curr)
		result=mrd.db_matchall(query)
		if result['count']>0:
			last=result['result'][len(result['result'])-1]
			buy_sell_status=last['status']
			buy_price=last['price']
			last_2=result['result'][len(result['result'])-2]
		query="select * from macd where curr='%s'"%(curr)
		result_macd=mrd.db_matchone(query)
		if result_macd['count']>0:
			diflist=json.loads(result_macd['result']['dif'])
			dealist=json.loads(result_macd['result']['dea'])
			dif_peak_slack1=peak_slack1(diflist)
			dea_peak_slack1=peak_slack1(dealist)
			dif_dea_overlap=overlap(diflist,dealist)
			dif_dea_overlap_pre=pre_overlap(diflist,dealist)
		if level_obj['key']=='kdj':
			level_number=level_obj['level']
			status=level_obj['status']
			level_conditions=level_obj['level_conditions']
			level_obj1={"key":level_obj['key'],"status":status,"level":level_number}
			if level_number==0:
				level_log(curr,json.dumps(level_obj1),level_conditions,'')
			if level_number==1:
				level_log(curr,json.dumps(level_obj1),level_conditions,'')
				if status=='buy' and buy_sell_status!='buy':
					if STATUS==0:
						if dif_dea_overlap==1 or dif_dea_overlap_pre==1:
							progress_log(curr,"dif即将上穿dea或者已经上穿")
							if dif_peak_slack1==2 and dea_peak_slack1==2:#看涨趋势 全仓买入
								buy_by_percent(curr,1)
							else:
								buy_by_percent(curr,0.5)
					else:
						progress_log(curr,"切换状态为2")
						query="select * from macd where curr='%s'"%(curr)
						result=mrd.db_matchone(query)
						if result['count']>0:
							dif_list=result['result']['dif']
							dea_list=result['result']['dea']
							if overlap(dif_list,dea_list)==1:
								buy_by_percent(curr,1)
								progress_log(curr,"切换状态为1")
								STATUS=0
				else:
					progress_log(curr,"上次已经购买")
					try:
						progress_log(curr,"尝试获取当前价格")
						info=gate_query.ticker(curr)
						last_price=float(info['last'])#最新价格
						progress_log(curr,"上次购买价格='%s' 当前价格='%s'"%(str(buy_price),str(last_price)))
						if last_price<buy_price:
							buy_by_percent4(curr,0.5)
							progress_log(curr,"当前价格小于上次购买价格，小额补入")
					except:
						progress_log(curr,"获取当前价格失败，跳过")
						pass
				if status=='sell':
					if dif_peak_slack1==1 and dea_peak_slack1==1:#看跌趋势 全仓卖出
						sell_by_percent(curr,1)
					else:
						sell_by_percent(curr,0.5)
			if level_number==2:
				if status=='buy' and buy_sell_status!='buy':
					if STATUS==0:
						level_macd=level(curr,'macd')
						level_ma=level(curr,'ma')
						level_over=0
						query="select * from over_price where curr='%s'"%(curr)
						result=mrd.db_matchone(query)
						if result['count']>0:
							overpricelist=json.loads(result['result']['overprice'])
							if 2 in overpricelist:
								level_over=2
							else:
								level_over=0
						else:
							level_over=0
						conditions_obj={}
						conditions_obj['level_macd']=level_macd
						conditions_obj['level_ma']=level_ma
						conditions_obj['level_over']=level_over
						level_log(curr,json.dumps(level_obj1),level_conditions,json.dumps(conditions_obj))
						if (level_macd['level']==2 and level_macd['status']=='buy') or (level_ma['level']==2 and level_ma['status']=='buy') or level_over==2:
							progress_log(curr,"满足购入条件，准备买入")
							if dif_peak_slack1==2 and dea_peak_slack1==2:#看涨趋势 全仓买入
								buy_by_percent(curr,1)
							else:
								buy_by_percent(curr,0.5)
					else:
						progress_log(curr,"切换状态为2")
						query="select * from macd where curr='%s'"%(curr)
						result=mrd.db_matchone(query)
						if result['count']>0:
							dif_list=result['result']['dif']
							dea_list=result['result']['dea']
							if overlap(dif_list,dea_list)==1:
								buy_by_percent(curr,0.5)
								progress_log(curr,"切换状态为1")
								STATUS=0
				if	status=='sell':
					query="select * from macd where curr='%s'"%(curr)
					result=mrd.db_matchone(query)
					diflist=json.loads(result['result']['dif'])
					dealist=json.loads(result['result']['dea'])
					query="select * from ma where curr='%s'"%(curr)
					result1=mrd.db_matchone(query)
					ma5list=json.loads(result1['result']['ma5list'])
					diflist_operation=operation_status(diflist)
					dealist_operation=operation_status(dealist)
					ma5list_operation=operation_status(ma5list)
					conditions_obj={}
					conditions_obj['diflist_operation']=diflist_operation
					conditions_obj['dealist_operation']=dealist_operation
					conditions_obj['ma5list_operation']=ma5list_operation
					level_log(curr,json.dumps(level_obj1),level_conditions,json.dumps(conditions_obj))
					if (diflist_operation==1 or diflist_operation==2) or (ma5list_operation==1 or ma5list_operation==2):
						progress_log(curr,"满足出售条件，准备出售")
						if dif_peak_slack1==1 and dea_peak_slack1==1:#看跌趋势 全部卖出
							sell_by_percent(curr,1)
						else:
							sell_by_percent(curr,0.5)
			if level_number==3:
				if status=='buy' and buy_sell_status!='buy':
					if STATUS==0:
						query="select * from macd where curr='%s'"%(curr)
						result=mrd.db_matchone(query)
						diflist=json.loads(result['result']['dif'])
						dealist=json.loads(result['result']['dea'])
						#diflist_trend=trend(diflist)
						dif_operation_status=operation_status(diflist)
						dea_peak_slack=peak_slack(dealist)
						query="select * from ma where curr='%s'"%(curr)
						result1=mrd.db_matchone(query)
						ma5list=json.loads(result1['result']['ma5list'])
						#ma5list_trend=trend(ma5list)
						ma5list_operation_status=operation_status(ma5list)
						query="select * from kdj where curr='%s'"%(curr)
						result2=mrd.db_matchone(query)
						dlist=json.loads(result2['result']['d'])
						d_last=dlist[len(dlist)-1]
						d_peak_slack=peak_slack(dlist)
						conditions_obj={}
						conditions_obj['dea_peak_slack']=dea_peak_slack
						conditions_obj['d_peak_slack']=d_peak_slack
						conditions_obj['dif_operation_status']=dif_operation_status
						conditions_obj['ma5list_operation_status']=ma5list_operation_status
						level_log(curr,json.dumps(level_obj1),level_conditions,json.dumps(conditions_obj))
						if dea_peak_slack==2 and (d_peak_slack==2 or d_last<25)  and (dif_operation_status==0) and (ma5list_operation_status==0):
							progress_log(curr,"满足购入条件，准备买入")
							buy_by_percent(curr,0.5)
					else:
						progress_log(curr,"切换状态为2")
						query="select * from macd where curr='%s'"%(curr)
						result=mrd.db_matchone(query)
						if result['count']>0:
							dif_list=result['result']['dif']
							dea_list=result['result']['dea']
							if overlap(dif_list,dea_list)==1:
								buy_by_percent(curr,0.5)
								progress_log(curr,"切换状态为1")
								STATUS=0
				if status=='sell':
					query="select * from macd where curr='%s'"%(curr)
					result=mrd.db_matchone(query)
					diflist=json.loads(result['result']['dif'])
					dealist=json.loads(result['result']['dea'])
					query="select * from ma where curr='%s'"%(curr)
					result1=mrd.db_matchone(query)
					ma5list=json.loads(result1['result']['ma5list'])
					ma10list=json.loads(result1['result']['ma10list'])
					diflist_operation=operation_status(diflist)
					dealist_operation=operation_status(dealist)
					ma5list_operation=operation_status(ma5list)
					overlap_oneHour_macd=overlap_oneHour(diflist,dealist)
					overlap_oneHour_ma=overlap_oneHour(ma5list,ma10list)
					conditions_obj={}
					conditions_obj['diflist_operation']=diflist_operation
					conditions_obj['dealist_operation']=dealist_operation
					conditions_obj['ma5list_operation']=ma5list_operation
					conditions_obj['overlap_oneHour_macd']=overlap_oneHour_macd
					conditions_obj['overlap_oneHour_ma']=overlap_oneHour_ma
					level_log(curr,json.dumps(level_obj1),level_conditions,json.dumps(conditions_obj))
					if (diflist_operation==1 or diflist_operation==2) or (ma5list_operation==1 or ma5list_operation==2) or overlap_oneHour_macd==2 or overlap_oneHour_ma==2:
						progress_log(curr,"满足出售条件，准备出售")
						if dif_peak_slack1==1 and dea_peak_slack1==1:#看跌趋势 全部卖出
							sell_by_percent2(curr,1)
						else:
							if buy_sell_status=='sell' and last_2['status']=='sell':
								sell_by_percent2(curr,1)
							else:
								sell_by_percent2(curr,0.5)
			update_all_coin()
			data={"error":0}
			self.write(data)
		self.finish()


class ErrorHandler(BaseHandler):    #增加了一个专门用来显示错误的页面
	def get(self):
		self.render("error.html")
		self.finish()
