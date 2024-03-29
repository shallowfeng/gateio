#!/usr/bin/env python
# coding=utf-8  shallowfeng  gxfshallow1995
"""
the url structure of website
"""

import importlib,sys
importlib.reload(sys)

import tornado.web
import handlers.index

url = [
    (r'/', handlers.index.IndexHandler),
    (r'/index', handlers.index.IndexHandler),
    (r'/monitoring', handlers.index.MonitoringHandler),
    (r'/autotrading', handlers.index.AutotradingHandler),
    (r'/ma', handlers.index.MaHandler),
    (r'/kdj', handlers.index.KdjHandler),
    (r'/macd', handlers.index.MacdHandler),
	# 下面是全部资源的地址，定义在这里的接口地址不反回数据，而是直接返回文件本身
	(r"/img/(.*)", tornado.web.StaticFileHandler, {"path":"./statics/img"}),
	(r"/(.*.ico)", tornado.web.StaticFileHandler, {"path":"./statics"}),
	(r"/css/(.*)", tornado.web.StaticFileHandler, {"path":"./statics/css"}),
	(r"/js/(.*)", tornado.web.StaticFileHandler, {"path":"./statics/js"}),
	(r"/data/(.*)", tornado.web.StaticFileHandler, {"path":"./statics/data"}),
	(r"/(.*.html)", tornado.web.StaticFileHandler, {"path":"./templates"}),
	(r"/report/(.*.pdf)", tornado.web.StaticFileHandler, {"path":"./files/report"})
]
