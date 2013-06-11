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

import os

port = int(os.environ.get("PORT", 5000))

# Configuration
# DATABASE_URI = 'sqlite:////tmp/flask-oauth.db'
DATABASE_URI = os.environ['DATABASE_URL']
SECRET_KEY = 'development key'
DEBUG = True
CALLBACK_BASE = 'http://tweet-more.herokuapp.com/'
# CALLBACK_BASE = 'http://127.0.0.1:%s/oauth-authorized'%port # for local dev

# Twitter keys
APP_KEY = os.environ['APP_KEY']
APP_SECRET = os.environ['APP_SECRET']