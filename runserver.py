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

import os
from tweetmore import app
port = int(os.environ.get("PORT", 5000))

# uncomment line below if you want to run outside of Heroku with `python runserver.py` command
# app.run(host='0.0.0.0', port=port)