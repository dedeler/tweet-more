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

from twython import Twython, TwythonError

from image import ImageGenerator

import os

# Setup Flask
# -----------
app = Flask('dedeler')
port = int(os.environ.get("PORT", 5000))

# Load configuration from file pointed by `DEDELER_SETTINGS` env. variable
app.config.from_envvar('DEDELER_SETTINGS')

#initialize Twython
APP_KEY = app.config['APP_KEY']
APP_SECRET = app.config['APP_SECRET']
twitter = Twython(APP_KEY, APP_SECRET)

# setup sqlalchemy
engine = create_engine(app.config['DATABASE_URI'])
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()
image_generator = ImageGenerator()


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
            # flash('Unable to load tweets from Twitter. Maybe out of '
            #       'API calls or Twitter is overloaded.')
    return render_template('index.html', tweets=tweets)


@app.route('/tweet', methods=['POST'])
def tweet():
    """Calls the remote twitter API to create a new status update."""
    if g.user is None:
        return redirect(url_for('login', next=request.url))
    status = request.form['tweet']
    if not status:
        return redirect(url_for('index'))

    auth_info = session['auth_info']
    t = Twython(APP_KEY, APP_SECRET,
            auth_info['oauth_token'], auth_info['oauth_token_secret'])
    
    successful = True
    resp = None
    try:
        media = image_generator.get_media(status)
        resp = t.update_status_with_media(media=media, status=get_status_text(status))
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

    auth_props = twitter.get_authentication_tokens(callback_url=app.config['CALLBACK_BASE'])

    oauth_token = auth_props['oauth_token']
    oauth_token_secret = auth_props['oauth_token_secret']

    session['oauth_token'] = oauth_token
    session['oauth_token_secret'] = oauth_token_secret

    return redirect(auth_props['auth_url'])


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('twitter', None)
    flash('You were signed out', 'notification')
    return redirect(request.referrer or url_for('index'))

@app.route('/oauth-authorized')
def handle_oauth_callback():
    t = Twython(APP_KEY, APP_SECRET,
            session['oauth_token'], session['oauth_token_secret'])

    oauth_verifier = request.args.get('oauth_verifier')
    resp = t.get_authorized_tokens(oauth_verifier)
    session['auth_info'] = resp
    
    next_url = request.args.get('next') or url_for('index')
    if resp is None:
        flash(u'You denied the request to sign in.', 'notification')
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
    flash('You were signed in', 'notification')
    return redirect(next_url)

def get_status_text(tweet):
    status = ' '.join(get_mentions_and_hashtags(tweet))
    if(len(status)==0):
        status = ''
    return status


def get_mentions_and_hashtags(tweet):
    words = tweet.split(' ')
    return [word for word in words if len(word)>0 and (word[0]=='@' or word[0]=='#')]

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)
