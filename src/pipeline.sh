#!/bin/sh
set -e

echo 'Converting to black & white...'
cd ../letters
mkdir -p bnw
for i in $(cd src; ls -- *); do
    convert "src/$i" -threshold 80% "bnw/$i"
done
cd - >/dev/null

echo 'Making background transparent...'
./transparentizer.py

echo 'Chopping letter variations...'
./chopper.py

echo 'Trimming chopped variations...'
./trimmer.py

echo 'Done.'