#!/bin/sh

jclic_data=$1
jclic_path=$2

if [ $# -ne 2 ]; then
  echo "Need 2 arguments."
  exit 1
fi

if [ ! -f ${jclic_data} ]; then
  echo "Data file $1 don't exists."
  exit 1
fi

if [ ! -f ${jclic_path} ]; then
  echo "Data file $2 don't exists."
  exit 1
fi

cat $1 > $2
if [ $? != 0 ]; then
  echo "Error, something wrong ocurred."
  exit 1
else
  echo "Done."
  exit 0
fi
