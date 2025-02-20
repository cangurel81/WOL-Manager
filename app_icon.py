import base64
from PIL import Image
import io

# İkon oluştur
icon = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
with open('app.ico', 'wb') as icon_file:
    icon.save(icon_file, format='ICO') 