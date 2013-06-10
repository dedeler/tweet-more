from flask import Flask, request, redirect, url_for, session, flash, g, \
     render_template

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from twython import Twython, TwythonError

from image import ImageGenerator

APP_KEY = ""
APP_SECRET = ""
twitter = Twython(APP_KEY, APP_SECRET)

# configuration
DATABASE_URI = 'sqlite:////tmp/flask-oauth.db'
SECRET_KEY = 'development key'
DEBUG = True

# setup flask
app = Flask(__name__)
app.debug = DEBUG
app.secret_key = SECRET_KEY

# setup sqlalchemy
engine = create_engine(DATABASE_URI)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()
image_generator = ImageGenerator()


def init_db():
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
        resp = t.update_status_with_media(media=media, status='Check this out')
    except TwythonError as e:
        flash(e, 'notification')
        successful = False

    print(resp)

    if(successful):
        tweetId = resp['id']
        flash(str(resp['id']), 'tweetId')
    return redirect(url_for('index'))


@app.route('/login')
def login():
    """Calling into authorize will cause the OpenID auth machinery to kick
    in.  When all worked out as expected, the remote application will
    redirect back to the callback URL provided.
    """
    # return twitter.authorize(callback=url_for('oauth_authorized',
    #     next=request.args.get('next') or request.referrer or None))

    auth_props = twitter.get_authentication_tokens(callback_url='http://127.0.0.1:5000/oauth-authorized')

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
    
    print('======================================')

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


if __name__ == '__main__':
    init_db()
    app.run()
