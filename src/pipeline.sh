#!/bin/sh
set -e

echo 'Making background transparent...'
./transparentizer.py

echo 'Chopping letter variations...'
./chopper.py

echo 'Trimming chopped variations...'
./trimmer.py

echo 'Done.'