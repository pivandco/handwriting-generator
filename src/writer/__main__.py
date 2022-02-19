from argparse import ArgumentParser

from fontmaker.cropper import crop_image

from . import draw
from .font import Font

argp = ArgumentParser()
argp.add_argument("textfile", type=open)
argp.add_argument("-d", "--debug", action="store_true")
args = argp.parse_args()

text = args.textfile.read().replace("ё", "е").replace("Ё", "Е")
font = Font.load(text)
result = draw(font, text, args.debug)
result = crop_image(result)
result.save("out.png")
