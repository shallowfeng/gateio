#! /usr/bin/env python
# coding=utf-8


import tornado.web

class BaseHandler(tornado.web.RequestHandler):
    print(1)
