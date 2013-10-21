Tweet More
==========

Lets you tweet unlimited characters by converting the text into an image where all twitter clients are able to show inline (without browsing to a website or opening another app)

Moreover all your tags, mentions and links are kept and still functional ;)

Dependencies
------------

**Software packages:**

* python (you don't say)
* pip
* libpq-dev (for psycopg2)
* python-dev (for psycopg2)

Check out installation instructions here: http://www.pip-installer.org/en/latest/installing.html

Note that python version is `2.7.4`.

**Python packages:**

* flask 0.9
* flask-babel 0.9
* sqlalchemy 0.8.1
* twython 2.10.1

Note that `twython` version is crucial for embedding images into tweets. 

```
# use virtualenv to protect baby pandas!
pip install flask flask-babel sqlalchemy
pip install -I twython
```

`-I` to install all dependencies, namely `requests` and `requests_oauthlib`.

Installation troubleshooting
----------------------------

For error:

        raise ImportError("The _imagingft C module is not installed")
    ImportError: The _imagingft C module is not installed

See: http://codeinthehole.com/writing/how-to-install-pil-on-64-bit-ubuntu-1204/

Configuration & Launching
-------------------------

To launch the application issue following commands

```
export DEDELER_SETTINGS='settings.py'
export APP_KEY='XXX'
export APP_SECRET='XXX'
export MONGO_URI='mongodb://<username>:<password>@<host>:<port>/tweetmore'
export ENV='dev'
python runserver.py
```

* If you are in development medium then you can choose not to set `MONGO_URI` so mongo uses localhost
* Optionally, you can set WATERMARK_TEXT to display a litte watermark-footer message to each image.

**Note that** `export ENV='dev'` should only be used in development environment and in prod it should be left blank.

**mongo on lxc:** `sudo -u mongodb mongod  --smallfiles --dbpath /var/lib/mongodb/`

### Heroku

To set env. variable on Heroku

```
heroku config:set DEDELER_SETTINGS='settings.py'
heroku config:set APP_KEY='XXX'
heroku config:set APP_SECRET='XXX'
heroku config:set MONGO_URI='mongodb://<username>:<password>@<host>:<port>/tweetmore'
```

Note that you need to uncomment the line `app.run(host='0.0.0.0', port=port)` in `runserver.py` if you are not using Heroku.

Translations
------------

```
# generate messages.pot file
pybabel extract -F babel.cfg -o messages.pot .

# generate a translation for a language, for example Turkish(tr)
# note that you need to remove fuzzy word from generated language translation
pybabel init -i messages.pot -d translations -l tr


# compile translations
pybabel compile -d translations

# update translations
pybabel extract -F babel.cfg -o messages.pot .
pybabel update -i messages.pot -d translations

```

See http://pythonhosted.org/Flask-Babel for details

Chrome Extension
----------------



License
-------

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