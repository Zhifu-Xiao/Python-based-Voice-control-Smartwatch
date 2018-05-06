import sys
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
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import simplejson
import random
from pymongo import MongoClient
import pprint
from bson.objectid import ObjectId
import pymongo
client = MongoClient()
db = client.test_database
posts = db.posts
collection = db.test_collection
df = pd.DataFrame()
for post in posts.find():
	df = df.append(post, ignore_index = True)
print(df)
new_X = pd.DataFrame(df.X.values.tolist(), columns= ['X%d' % i for i in xrange(1, 101)])
new_Y = pd.DataFrame(df.Y.values.tolist(), columns= ['Y%d' % i for i in xrange(1, 101)])
new_type =  pd.DataFrame(df.type.values.tolist())
new_df = pd.concat([new_X, new_Y, new_type], axis=1)
train_X = new_df.drop([0],axis = 1)
train_Y = new_df[0]
#	train_X = df.drop([0],axis = 1)
#	train_Y = df[0]
	
clf = svm.LinearSVC()
le = LabelEncoder()
train_Y_trans = le.fit_transform(train_Y)
clf.fit(train_X, train_Y_trans)
print(clf)
joblib.dump(clf, 'model.pkl')
joblib.dump(le, 'model_le.pkl')