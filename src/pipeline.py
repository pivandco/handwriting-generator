#!/usr/bin/env python3

from transparentizer import transparentize
from chopper import chop
from trimmer import trim

print('Making background transparent...')
transparentize()
print('Chopping letter variations...')
chop()
print('Trimming chopped variations...')
trim()
