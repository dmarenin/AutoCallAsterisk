# coding:utf8
#from socketserver import ThreadingMixIn
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
#import urllib.request
from urllib.parse import urlparse, parse_qs
#import socket
#import threading
#from datetime import datetime
#from datetime import timedelta
from common import common
#from common.orm import models as orm
#import peewee
#from playhouse.shortcuts import case
#import base64
import sys
#import pymssql
#import uuid
#import time
#import _thread

from common import api_func, path_list

class AmiClient_Exception(Exception):
    pass

class AmiClient_Handler(BaseHTTPRequestHandler):
    callback = None

    def log_message(self, format, *args):
        return

    def smart_response(self, code, message, headers = []):
        self.send_response(code)
        for h, v in headers:
            self.send_header(h, v)

        self.send_header("Content-type", "text/plain; charset=utf-8")

        self.end_headers()
        if (code != 200):
            print(message)
            message = message

        return self.wfile.write(message.encode())

    def do_GET(self):
        path = urlparse(self.path).path
        qs = urlparse(self.path).query
        qs = parse_qs(qs)
        
        res = self.callback(path, qs, self)

class AmiClient():
    server = None
    parser = common.createParser()
    namespace = parser.parse_args(sys.argv[1:])
    
    server_host = namespace.ip
    server_port = int(namespace.port)
        
    handler = AmiClient_Handler

    pathmap = {}
    
    def __init__(self, caller = None):
        self.init_pathmap()
        #self.init_post_proc_func()
        self.handler.callback = self.callback
        #_thread.start_new_thread(self.upd_loop, ())

    def register(self, method, path, function):
        self.pathmap[path] = function    
    def register_post_proc_func(self, method, path, function):
        self.pathmap[path] = function
    
    def callback(self, path, qs, handler):
        while path and path[0] == '/':

            func = self.pathmap.get(path)
            if func is None:
                return handler.smart_response(404, "Не найден метод: "+str(path))
            
            try:
                res = func(qs)
            except KeyError as e:
                return handler.smart_response(500, "Не задано значение параметра: %s" % e)
            except ValueError as e:
                return handler.smart_response(500, "Ошибка в значении параметра: %s" % e)
            except AmiClient_Exception as e:
                return handler.smart_response(500, "%s" % e)
            except Exception as e:
                return handler.smart_response(500, "Неожиданная ошибка: %s" % e)

            content_type = "application/json"

            if not res:
                res = json.dumps([], default=common.json_serial)

            else:
                res = json.dumps(res, default=common.json_serial)

            try:
                handler.smart_response(200, res, [
                    ("Content-type", content_type),
                    ("Access-Control-Allow-Origin", "*"),
                    ("Access-Control-Expose-Headers", "Access-Control-Allow-Origin"),
                    ("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept"),
                ])
            except socket.error as e:
                pass

            return
        else:
            handler.smart_response(401, "Unauthorized call: %s from %s" % (path, client_address))
  
    def init_pathmap(self):
        for x in path_list.get():
            self.register(x['method'], x['func'], x['handler'])

