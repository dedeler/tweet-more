# coding=utf8

'''
Tweet More
Copyright (C) 2013 Destan Sarpkaya destan@dorukdestan.com
Copyright (C) 2013 Yasa Akbulut yasakbulut@gmail.com

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

from flask import Flask, request, redirect, url_for, session, flash, g, render_template, send_file, jsonify

from flask.ext.babel import gettext, ngettext

from twython import Twython, TwythonError

from tweetmore.image import ImageGenerator
from tweetmore.model import User, DB
from tweetmore import app
from tweetmore.views.utils import *

from mongokit import *

import os, datetime

class Tw333tException(Exception):
  pass

#initialize Twython
APP_KEY = app.config['APP_KEY']
APP_SECRET = app.config['APP_SECRET']
twitter = Twython(APP_KEY, APP_SECRET)

image_generator = ImageGenerator(watermark_text=app.config['WATERMARK_TEXT'])

@app.before_request
def before_request():
  g.user = None
  if 'user_id' in session:
    g.user = DB.User.one({'_id': ObjectId(session['user_id'])})

@app.after_request
def after_request(response):
  return response

@app.route('/')
def index():
  tweets = None
  if g.user is not None:
    auth_info = session['auth_info']
    t = Twython(APP_KEY, APP_SECRET,
      auth_info['oauth_token'], auth_info['oauth_token_secret'])
    tweets = t.get_user_timeline(screen_name=g.user['name'])
  return render_template('index.html', tweets=tweets, locale=get_locale())

@app.route('/tweet', methods=['POST'])
def tweet():
  """Calls the remote twitter API to create a new status update."""
  if g.user is None:
    return redirect(url_for('login', next=request.url))

  #update last seen
  g.user['last_seen'] = datetime.datetime.utcnow()
  g.user.save()  

  status = request.form['tweet']

  in_reply_to_status_id = None
  if 'replying_to' in request.form:
    in_reply_to_status_id = request.form['replying_to']

  if not status:
    return redirect(url_for('index'))

  successful = True
  resp = None
  
  try:
    auth_info = session['auth_info']
    t = Twython(APP_KEY, APP_SECRET,
        auth_info['oauth_token'], auth_info['oauth_token_secret'])

    media = image_generator.get_media(status)
    processedStatus = get_status_text(status)

    resp = t.update_status_with_media(media=media, status=processedStatus, in_reply_to_status_id=in_reply_to_status_id)
  except TwythonError as e:
    flash(e, 'notification')
    successful = False

  if(successful):
    tweetId = resp['id']
    flash(str(resp['id']), 'tweetId')

    # keep the tweet's id
    tweet = DB.Tweet()
    tweet['tweet_id'] = tweetId
    tweet['user_id'] = g.user['user_id']
    tweet.save()

  return redirect(url_for('index'))

@app.route('/preview.png', methods=['POST'])
def preview():
  """Sends base64 encoded png in order to preview the status update's image form."""
  if g.user is None:
    return redirect(url_for('login', next=request.url))
  status = request.form['tweet']
  if not status:
    return redirect(url_for('index'))

  #update last seen
  g.user['last_seen'] = datetime.datetime.utcnow()
  g.user.save()

  media = image_generator.get_media(status)
  response = send_file(media,mimetype ='image/png')
  return media.getvalue().encode("base64").replace("\n", "")

@app.route('/login')
def login():
  """Calling into authorize will cause the OpenID auth machinery to kick
  in.  When all worked out as expected, the remote application will
  redirect back to the callback URL provided.
  """

  callback_url = app.config['CALLBACK_BASE'] + 'oauth-authorized'
  if request.args.get('ext') == 'true':
    callback_url += '?ext=true'

  auth_props = twitter.get_authentication_tokens(callback_url=callback_url)

  oauth_token = auth_props['oauth_token']
  oauth_token_secret = auth_props['oauth_token_secret']

  session['oauth_token'] = oauth_token
  session['oauth_token_secret'] = oauth_token_secret
  session.permanent = True

  return redirect(auth_props['auth_url'])


@app.route('/logout')
def logout():
  session.pop('user_id', None)
  session.pop('twitter', None)

  if request.args.get('ext') == 'true':
    return redirect(url_for('extension_logout_callback'))

  flash(gettext('You were signed out'), 'notification')
  return redirect(request.referrer or url_for('index'))

@app.route('/oauth-authorized')
def handle_oauth_callback():
  try:
    t = Twython(APP_KEY, APP_SECRET,
        session['oauth_token'], session['oauth_token_secret'])

    oauth_verifier = request.args.get('oauth_verifier')
    resp = t.get_authorized_tokens(oauth_verifier)
    session['auth_info'] = resp
    
    next_url = request.args.get('next') or url_for('index')

    if request.args.get('ext') == 'true':
      next_url = url_for('extension_callback')

    if resp is None or request.args.get('denied') is not None:
      flash(gettext('You denied the request to sign in.'), 'error')
      return redirect(next_url)

    user = DB.User.one({'user_id': resp['user_id']})

    # user never signed on
    if user is None:
      user = DB.User()
      user['name'] = resp['screen_name']
      user['user_id'] = resp['user_id']
      user.save() #to get db generate an id for this object

    # in any case we update the authenciation token in the db
    # In case the user temporarily revoked access we will have
    # new tokens here.
    user['oauth_token'] = resp['oauth_token']
    user['oauth_secret'] = resp['oauth_token_secret']
    now = datetime.datetime.utcnow()
    user['last_login'] = now
    user['last_seen'] = now
    user.save()

    session['user_id'] = str(user['_id'])
    flash(gettext('You were signed in'), 'notification')

  except Exception, e:
    print e
    flash(gettext('Twitter authorization failed, please try again later.'), 'error')
    next_url = url_for('index')

  finally:
    return redirect(next_url)

# Extension handlers
# ==================

@app.route('/extension-callback')
def extension_callback():
  return render_template('callback.html', locale=get_locale())

@app.route('/extension-logout-callback')
def extension_logout_callback():
  return render_template('callback_logout.html', locale=get_locale())

@app.route('/extension-check-login')
def extension_check_login():
  status = g.user is not None
  code = 200 if status else 401
  return g.user['user_id'] if status else '', code