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

from flask import request
from flask.ext.babel import Babel
from tweetmore import app

import re

babel = Babel(app)

# *_LINK_LENGTH constants must be get from help/configuration/short_url_length daily
# last update 14th November 2013
TWITTER_HTTPS_LINK_LENGTH = 23
TWITTER_HTTP_LINK_LENGTH = 22
TWITTER_MEDIA_LINK_LENGTH = 23

CONTINUATION_CHARARCTERS = u'… '
MAX_STATUS_TEXT_LENGTH = 140 - TWITTER_MEDIA_LINK_LENGTH - 1

# RegEx source: http://daringfireball.net/2010/07/improved_regex_for_matching_urls
url_regex_pattern = r"(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'.,<>?«»“”‘’]))"
url_regex = re.compile(url_regex_pattern, re.I | re.M | re.U)

url_regex_pattern_no_protocol = r"(\w+\.(aero|asia|biz|cat|com|coop|edu|gov|info|int|jobs|mil|mobi|museum|name|net|org|pro|tel|travel|xxx){1}(\.(ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|za|zm|zw)){0,1})"
url_regex_no_protocol = re.compile(url_regex_pattern_no_protocol, re.I | re.M | re.U)

@babel.localeselector
def get_locale():
  return request.accept_languages.best_match(app.config['LANGUAGES'].keys())

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
    # CAUTION! below print causes unsolved encoding errors in (unknown)edge cases! Use in local only, if even necessary.
    # print len(words), index, word, remaining_chars
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
  return list(group[0] for group in url_regex.findall(tweet) ) + list(group[0] for group in url_regex_no_protocol.findall(tweet) )

def get_short_url_length(long_url):
  if(long_url.startswith('https://')):
    return TWITTER_HTTPS_LINK_LENGTH
  return TWITTER_HTTP_LINK_LENGTH # maybe http, ftp or smth. else