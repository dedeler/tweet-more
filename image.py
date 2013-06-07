from PIL import Image, ImageFont, ImageDraw

import textwrap

def getImage(tweet):
  #435px is the ideal width for twitter
  img_width = 435
  padding = {'left': 10, 'right': 10, 'top': 10, 'bottom': 10}
  foreground_color = (31, 31, 31)
  background_color = (255,255,255)
  font_path = 'OpenSans-Light.ttf'
  font_size = 16
  
  font = ImageFont.truetype(font_path,font_size,encoding='unic')
  char_width, line_height = font.getsize("c")
  max_chars = (img_width - (padding['left'] + padding['right']))/char_width
  lines = wrap(tweet, img_width - (padding['left'] + padding['right']), font)

  img_height = padding['top'] + padding['bottom'] + (len(lines)*line_height)

  im = Image.new("RGB",(img_width,img_height),background_color)
  draw = ImageDraw.Draw(im)

  y_text = padding['top']
  for line in lines:
    draw.text((padding['left'], y_text), line, font=font, fill = foreground_color)
    y_text += line_height
  return im

def wrap(text, width, font):
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
