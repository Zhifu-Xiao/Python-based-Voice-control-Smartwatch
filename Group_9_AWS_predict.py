from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import json
import urlparse
import subprocess
import sklearn
import numpy as np
import scipy
import sys
import pandas as pd
from sklearn import svm
from sklearn.preprocessing import LabelEncoder
from sklearn.externals import joblib

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import simplejson
import random

df = pd.DataFrame(columns=["X", "Y", "type"])
for arg in sys.argv:
    print arg
try:
	model_name = sys.argv[1]
	le_name = sys.argv[2]
except (RuntimeError, TypeError, NameError):
	print("error")
	pass

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
		global df, model_name, le_name
		self._set_headers()
		print "in post method"
		self.data_string = self.rfile.read(int(self.headers['Content-Length']))
		self.send_response(200)
		self.end_headers()
		data = simplejson.loads(self.data_string)
		df = df.append(data, ignore_index= True)
		new_X = pd.DataFrame(df.X.values.tolist(), columns= ['X%d' % i for i in xrange(1, 101)])
		new_Y = pd.DataFrame(df.Y.values.tolist(), columns= ['Y%d' % i for i in xrange(1, 101)])
		#new_type =  pd.DataFrame(df.type.values.tolist())
		predict_X = pd.concat([new_X, new_Y], axis=1)
		clf = joblib.load(model_name)
		le = joblib.load(le_name) 
		results = le.inverse_transform(clf.predict(predict_X))
		print(results)
		flat_results = "".join(results)
		results = {"response": str(flat_results)}
		self.send_response(code = 200, message = results)
		self.end_headers()
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