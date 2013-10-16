# coding=utf8

'''
Tweet More
Copyright (C) 2013 Destan Sarpkaya destan@dorukdestan.com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/gpl-3.0.html>.
'''

from mongokit import *
import datetime
import os

try:
  connection = Connection(host=os.environ['MONGO_URI'])
  print 'Connected mongodb on Remote Mongo'
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