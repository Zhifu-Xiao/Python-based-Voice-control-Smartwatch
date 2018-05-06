from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import json
import urlparse
import subprocess
import sklearn
import numpy as np
import scipy
import pandas as pd
from sklearn import svm
from sklearn.preprocessing import LabelEncoder
from sklearn.externals import joblib
from pymongo import MongoClient
import pprint
from bson.objectid import ObjectId
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import simplejson
import random
import pymongo
client = MongoClient()
db = client.test_database
posts = db.posts
collection = db.test_collection

df = pd.DataFrame(columns=["X", "Y", "type"])

class S(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        f = open("index.html", "r")
        self.wfile.write(f.read())

    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
		global df
		global client, db, posts, collection
		temp_df = pd.DataFrame(columns=["X", "Y", "type"])
		self._set_headers()
		print "in post method"
		self.data_string = self.rfile.read(int(self.headers['Content-Length']))
		self.send_response(200)
		self.end_headers()
		data = simplejson.loads(self.data_string)
		df = df.append(data, ignore_index= True)
		temp_df = temp_df.append(data, ignore_index= True)
#		result = posts.insert_one(json.loads(temp_df.to_json(orient = 'records'))[0])
		result = posts.insert_one(data)
		print(result)
		print(temp_df)
		df.to_json('training.json')
		return


def run(server_class=HTTPServer, handler_class=S, port=80):
    
    server_address = ('', port)
#    server_address = ('209.2.224.189', port)
    httpd = server_class(server_address, handler_class)
    print 'Starting httpd...'
    print(server_address)
    httpd.serve_forever()

if __name__ == "__main__":
    from sys import argv

if len(argv) == 2:
    run(port=int(argv[1]))
else:
    run()