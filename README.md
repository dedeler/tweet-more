Tweet More
==========

Lets you tweet unlimited characters by converting the text into an image where all twitter clients are able to show inline (without browsing to a website or opening another app)

Moreover all your tags, mentions and links are kept and still functional ;)

Dependencies
------------

**Software packages:**

* python (you don't say)
* pip

Check out installation instructions here: http://www.pip-installer.org/en/latest/installing.html

Note that python version is `2.7.4`.

**Python packages:**

* flask 0.9
* sqlalchemy 0.8.1
* twython 2.10.1

Note that `twython` version is crucial for embedding images into tweets. 

```
sudo pip install flask sqlalchemy
sudo pip install -I twython
```

`-I` to install all dependencies, namely `requests` and `requests_oauthlib`.

Configuration & Launching
-------------------------

Rename `settings.py.example` to `settings.py` and fill *Twitter keys*.

To launch the application issue following commands

```
export DEDELER_SETTINGS='settings.py'
python tweet.py
```

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