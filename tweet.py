# coding=utf8

'''
Tweet More
Copyright (C) <2013>  <Dedeler>

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

from flask import Flask, request, redirect, url_for, session, flash, g, \
     render_template, send_file

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from flask.ext.babel import Babel
from flask.ext.babel import gettext, ngettext

from twython import Twython, TwythonError

from image import ImageGenerator

import os, re

class Tw333tException(Exception):
    pass

# Setup Flask
# -----------
app = Flask('dedeler')
babel = Babel(app)
port = int(os.environ.get("PORT", 5000))

# Load configuration from file pointed by `DEDELER_SETTINGS` env. variable
app.config.from_envvar('DEDELER_SETTINGS')

#initialize Twython
APP_KEY = app.config['APP_KEY']
APP_SECRET = app.config['APP_SECRET']
twitter = Twython(APP_KEY, APP_SECRET)
TWITTER_HTTPS_LINK_LENGTH = 23 #FIXME: GET help/configuration/short_url_length
TWITTER_HTTP_LINK_LENGTH = 22 #FIXME: GET help/configuration/short_url_length
CONTINUATION_CHARARCTERS = u'… '
MAX_STATUS_TEXT_LENGTH = 140 - TWITTER_HTTP_LINK_LENGTH - 1

# setup sqlalchemy
engine = create_engine(app.config['DATABASE_URI'])
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()
image_generator = ImageGenerator(watermark_text=app.config['WATERMARK_TEXT'])

# RegEx source: http://daringfireball.net/2010/07/improved_regex_for_matching_urls
url_regex_pattern = r"(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'.,<>?«»“”‘’]))"
url_regex = re.compile(url_regex_pattern, re.I | re.M | re.U)

def init_db():
    print("INIT DB")
    Base.metadata.create_all(bind=engine)

class User(Base):
    __tablename__ = 'users'
    id = Column('user_id', Integer, primary_key=True)
    name = Column(String(60))
    oauth_token = Column(String(200))
    oauth_secret = Column(String(200))

    def __init__(self, name):
        self.name = name

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'].keys())

@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])

@app.after_request
def after_request(response):
    db_session.remove()
    return response

@app.route('/')
def index():
    tweets = None
    if g.user is not None:
        auth_info = session['auth_info']
        t = Twython(APP_KEY, APP_SECRET,
            auth_info['oauth_token'], auth_info['oauth_token_secret'])
        tweets = t.get_user_timeline(screen_name=g.user.name)
    return render_template('index.html', tweets=tweets, locale=get_locale())

@app.route('/tweet', methods=['POST'])
def tweet():
    """Calls the remote twitter API to create a new status update."""
    if g.user is None:
        return redirect(url_for('login', next=request.url))
    status = request.form['tweet']
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

        resp = t.update_status_with_media(media=media, status=processedStatus)
    except TwythonError as e:
        flash(e, 'notification')
        successful = False

    if(successful):
        tweetId = resp['id']
        flash(str(resp['id']), 'tweetId')
    return redirect(url_for('index'))

@app.route('/preview.png', methods=['POST'])
def preview():
    """Sends base64 encoded png in order to preview the status update's image form."""
    if g.user is None:
        return redirect(url_for('login', next=request.url))
    status = request.form['tweet']
    if not status:
        return redirect(url_for('index'))

    media = image_generator.get_media(status)
    response = send_file(media,mimetype ='image/png')
    return media.getvalue().encode("base64").replace("\n", "")

@app.route('/login')
def login():
    """Calling into authorize will cause the OpenID auth machinery to kick
    in.  When all worked out as expected, the remote application will
    redirect back to the callback URL provided.
    """
    # return twitter.authorize(callback=url_for('oauth_authorized',
    #     next=request.args.get('next') or request.referrer or None))

    auth_props = twitter.get_authentication_tokens(callback_url=app.config['CALLBACK_BASE'] + 'oauth-authorized')

    oauth_token = auth_props['oauth_token']
    oauth_token_secret = auth_props['oauth_token_secret']

    session['oauth_token'] = oauth_token
    session['oauth_token_secret'] = oauth_token_secret

    return redirect(auth_props['auth_url'])


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('twitter', None)
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
        if resp is None or request.args.get('denied') is not None:
            flash(gettext('You denied the request to sign in.'), 'error')
            return redirect(next_url)

        user = User.query.filter_by(name=resp['screen_name']).first()

        # user never signed on
        if user is None:
            user = User(resp['screen_name'])
            db_session.add(user)

        # in any case we update the authenciation token in the db
        # In case the user temporarily revoked access we will have
        # new tokens here.
        user.oauth_token = resp['oauth_token']
        user.oauth_secret = resp['oauth_token_secret']
        db_session.commit()

        session['user_id'] = user.id
        flash(gettext('You were signed in'), 'notification')
        
    except Exception, e:
        flash(gettext('Twitter authorization failed, please try again later.'), 'error')
        next_url = url_for('index')

    finally:
        return redirect(next_url)

def get_remaining_chars(max_status_length, mentions, urls):
     remaining_chars = max_status_length 
     remaining_chars -= len(' '.join(mentions))
     
     #urls get shortened, and space seperated. 
     remaining_chars -= sum([get_short_url_length(url)+1 for url in urls])

     #for ellipsis and space character 
     remaining_chars -= len(CONTINUATION_CHARARCTERS) 
     return remaining_chars

def get_status_text(tweet):
    # Twitter also left-strips tweets
    tweet = tweet.strip()

    #reserve a place for the picture we're going to post
    max_status_length=MAX_STATUS_TEXT_LENGTH

    if(len(tweet)<(max_status_length)):
        return tweet

    urls = get_urls(tweet)
    mentions = get_mentions_and_hashtags(tweet)
    words = tweet.split(' ')

    remaining_chars = get_remaining_chars(max_status_length, mentions, urls)
    shortened_words = []

    #if remaining characters is less than length of the cont. characters, don't bother
    if(remaining_chars>len(CONTINUATION_CHARARCTERS)):
        overflowed = False
        for index, word in enumerate(words):
            #length of an url is not len(word), but TWITTER_HTTP(s)_LINK_LENGTH
            if (len(word)<remaining_chars or (word in urls and get_short_url_length(word)<remaining_chars)):
                if(word in urls):
                    urls.remove(word)
                    shortened_words.append(word)
                    remaining_chars += len(word) - get_short_url_length(word)
                elif(word in mentions):
                    shortened_words.append(word)
                    mentions.remove(word) 
                else:
                    shortened_words.append(word)
                    remaining_chars -= len(word) +1
            else:
                remaining_chars+=1 #for the space that doesn't exist (at the end)
                overflowed = True
                break
        #append ellipsis to the last word
        print len(words), index, word, remaining_chars
        if (len(shortened_words)>0 and overflowed):
            shortened_words[-1] += CONTINUATION_CHARARCTERS 
    status = ' '.join(shortened_words)

    # If there is no direct mention let urls appear before mentions
    if tweet[0] != '@':
        status += ' '.join(wrap_status_elements(urls+mentions))
    else:
        status += ' '.join(wrap_status_elements(mentions+urls))

    # check if tweet is directly targeted to someone<br>
    # If tweet is not directly targeted to someone than don't let a mention appear 
    # at the start of the line
    if tweet[0] != '@' and len(mentions) > 0 and len(urls) == 0:
        if status[0]=='@':
            status = '.' + status

    if(len(status)==0):
        status = ''
    return status

def wrap_status_elements(elements):
    """Discards elements who, when concatenated, would exceed twitter's status length"""
    remaining_chars = MAX_STATUS_TEXT_LENGTH
    wrapped = []
    for element in elements:
        if(len(element)<remaining_chars):
            wrapped.append(element)
            #if element is an url, it will get shortened to TWITTER_HTTP(S)_LINK_LENGTH
            element_length = len(element) if element[0]=='#' or element[0]=='@' else get_short_url_length(element)
            remaining_chars -= (element_length + 1)
    return wrapped

def get_mentions_and_hashtags(tweet):
    words = tweet.replace('\n', ' ').split(' ')
    return [word for word in words if len(word)>0 and (word[0]=='@' or word[0]=='#')]

def get_urls(tweet):
    return list(group[0] for group in url_regex.findall(tweet) )

def get_short_url_length(long_url):
    if(long_url.startswith('https://')):
        return TWITTER_HTTPS_LINK_LENGTH
    if(long_url.startswith('http://')):
        return TWITTER_HTTP_LINK_LENGTH
    return None

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(port=port)
