#!/bin/bash

directorio=img

mkdir -p mini

for i in $(ls $directorio); do
  echo -n "Escalando $i.... "
  convert -sample 70%x70% img/$i mini/$i
  echo " hecho."
done
