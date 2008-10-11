#!/bin/sh

dir=mini

for img in $(ls $dir); do


ancho=$(identify $dir/$img | awk '{print $3}'| awk -F"x" '{print $1}')
 alto=$(identify $dir/$img | awk '{print $3}'| awk -F"x" '{print $2}')

if [ $ancho -gt 300 -o $alto -gt 245 ]; then
 echo $img: $ancho x $alto
fi


done
