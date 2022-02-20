from .background_remover import remove_background
from .series_splitter import split_series

print("Making background transparent...")
remove_background()
print("Splitting and cropping letter variations...")
split_series()
