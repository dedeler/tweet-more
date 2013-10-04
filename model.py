from mongokit import *
import datetime

connection = Connection()
DB = connection.prod.tweetmore

@connection.register
class User(Document):
  structure = {
    'name': unicode,
    'user_id': unicode,
    'oauth_token': unicode,
    'oauth_secret': unicode,
    'last_login': datetime.datetime
  }
  required_fields = []
  default_values = {'last_login':datetime.datetime.utcnow}