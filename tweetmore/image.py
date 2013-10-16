# coding=utf8

'''
Tweet More
Copyright (C) 2013 Yasa Akbulut yasakbulut@gmail.com
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

from PIL import Image, ImageFont, ImageDraw
import StringIO

class ImageGenerator:
  """Generates png files containing given text"""

  def __init__(self, \
    img_width=435, \
    padding = {'left': 10, 'right': 10, 'top': 10, 'bottom': 10}, \
    foreground_color = (31, 31, 31), \
    background_color = (255,255,255), \
    font_path = 'tweetmore/OpenSans-Light.ttf', \
    font_size = 16, \
    watermark_text = None,
    watermark_font_size = 14,
    watermark_foreground_color = (124, 124, 124)):

    self.img_width = img_width
    self.padding = padding
    self.foreground_color = foreground_color
    self.background_color = background_color
    self.font = ImageFont.truetype(font_path,font_size,encoding='unic')
    self.char_width, self.line_height = self.font.getsize("M")

    self.watermark_text = watermark_text
    self.watermark_font_size = watermark_font_size
    self.watermark_foreground_color = watermark_foreground_color
    self.watermark_font = ImageFont.truetype(font_path,watermark_font_size,encoding='unic')



  def get_image(self, text):

    lines = []
    user_lines = text.splitlines()
    for user_line in user_lines:
      lines.extend(self.wrap(user_line, self.img_width - (self.padding['left'] + self.padding['right']), self.font))

    img_height = self.padding['top'] + self.padding['bottom'] + (len(lines)*self.line_height)
    
    if(self.watermark_text is not None):
      img_height += self.line_height

    im = Image.new("RGB",(self.img_width,img_height),self.background_color)
    draw = ImageDraw.Draw(im)

    y_text = self.padding['top']
    for line in lines:
      draw.text((self.padding['left'], y_text), line, font=self.font, fill = self.foreground_color)
      y_text += self.line_height

    if(self.watermark_text is not None):
      y_text+=self.padding['bottom']
      watermark_length, watermark_height = self.watermark_font.getsize(self.watermark_text)
      x_watermark = self.img_width - watermark_length - self.padding['right']
      if(x_watermark<self.padding['left']):
        x_watermark = self.padding['left']
      draw.text((x_watermark, y_text), self.watermark_text, font=self.watermark_font, fill = self.watermark_foreground_color)

    return im

  def get_media(self, text):
    image_io = StringIO.StringIO()
    im = self.get_image(text)
    im.save(image_io, format='PNG')
    image_io.seek(0)
    return image_io

  def wrap(self, text, width, font):
    words = text.split(' ')
    lines = []
    line = []
    space_width = (font.getsize(' '))[0]
    remaining_width = width
    for word in words:
      word_length, word_height = font.getsize(word)
      if(word_length<=remaining_width):
        line.append(word)
        remaining_width -= word_length + space_width
      else:
        remaining_width = width
        lines.append(' '.join(line))
        line = [word]
        remaining_width -= word_length + space_width
    lines.append(' '.join(line))
    return lines
