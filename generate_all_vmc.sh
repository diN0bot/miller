#!/bin/sh
#
#
#
#
export PYTHONPATH=./

for f in `ls input_files/*.rml`
do
  echo "Generating VMC for $f..."
  python parsers/rmlparser.py $f
  echo "    ...done"
done
