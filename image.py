from PIL import Image, ImageFont, ImageDraw
import StringIO

class ImageGenerator:
  """Generates png files containing given text"""

  def __init__(self, \
    img_width=435, \
    padding = {'left': 10, 'right': 10, 'top': 10, 'bottom': 10}, \
    foreground_color = (31, 31, 31), \
    background_color = (255,255,255), \
    font_path = 'OpenSans-Light.ttf', \
    font_size = 16):

    self.img_width = img_width
    self.padding = padding
    self.foreground_color = foreground_color
    self.background_color = background_color
    self.font = ImageFont.truetype(font_path,font_size,encoding='unic')
    self.char_width, self.line_height = self.font.getsize("M")


  def get_image(self, text):

    lines = []
    user_lines = text.splitlines()
    for user_line in user_lines:
      lines.extend(self.wrap(user_line, self.img_width - (self.padding['left'] + self.padding['right']), self.font))

    img_height = self.padding['top'] + self.padding['bottom'] + (len(lines)*self.line_height)

    im = Image.new("RGB",(self.img_width,img_height),self.background_color)
    draw = ImageDraw.Draw(im)

    y_text = self.padding['top']
    for line in lines:
      draw.text((self.padding['left'], y_text), line, font=self.font, fill = self.foreground_color)
      y_text += self.line_height
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
