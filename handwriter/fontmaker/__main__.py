from .background_remover import remove_background
from .cropper import crop
from .series_splitter import split_series

print("Making background transparent...")
remove_background()
print("Chopping letter variations...")
split_series()
print("Trimming chopped variations...")
crop()
