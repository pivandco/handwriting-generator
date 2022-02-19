from .background_remover import remove_background
from .series_splitter import split_series
from .cropper import crop


if __name__ == '__main__':
    print('Making background transparent...')
    remove_background()
    print('Chopping letter variations...')
    split_series()
    print('Trimming chopped variations...')
    crop()
