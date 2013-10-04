from mongokit import *
import datetime
import os

try:
  connection = Connection(os.environ['MONGOLAB_URI'])
  print 'Connected mongodb on Mongolab'
except KeyError, e:
  connection = Connection('mongodb://localhost')
  print 'Connected mongodb on localhost'

DB = connection

@connection.register
class User(Document):
  __database__ = 'tweetmore'
  __collection__ = 'user'
  structure = {
    'name': unicode,
    'user_id': unicode,
    'oauth_token': unicode,
    'oauth_secret': unicode,
    'last_login': datetime.datetime,
    'last_seen': datetime.datetime
  }
  required_fields = []
  default_values = {'last_login':datetime.datetime.utcnow, 'last_seen':datetime.datetime.utcnow}

@connection.register
class Tweet(Document):
  __database__ = 'tweetmore'
  __collection__ = 'tweet'
  structure = {
    'tweet_id': int,
    'user_id': unicode,
    'date': datetime.datetime
  }
  required_fields = []
  default_values = {'date':datetime.datetime.utcnow}