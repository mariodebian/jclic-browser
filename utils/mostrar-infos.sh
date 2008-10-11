#!/bin/bash

ZIPS_DIR=/var/lib/jclic_browser/zips/
TMP_DIR=/tmp/jclic

_log() {
  echo "$@" 1>&2
}

info_zip() {
 if [ $# != 2 ]; then
	_log "ERROR se necesita el nombre del zip"
	return
 fi

 _log "    Extrayendo $(basename $1) ..."
 rm -rf ${TMP_DIR} && mkdir -p ${TMP_DIR}
 unzip -qq $1 -d ${TMP_DIR} > /dev/null 2>&1
 cat ${TMP_DIR}/*.jclic >> todo
 ARCHIVO=$(find ${TMP_DIR}/ -name "*.jclic")
 if [ "$ARCHIVO" = "" ] ; then
  _log "ERROR: archivo XML .jclic no encontrado"
  return
 fi
 archivo=$1
 titulo=$(xmlstarlet select -T -t -c "JClicProject/settings/title" $ARCHIVO)
 idioma=$(xmlstarlet select -T -t -c "JClicProject/settings/language" $ARCHIVO)
 materia=$(grep descriptors $ARCHIVO | awk -F "area=\"" '{print $2}' | awk -F "\"" '{print $1}')
 edad=$(grep descriptors $ARCHIVO | awk -F "level=\"" '{print $2}' | awk -F "\"" '{print $1}')
 categorias=`xmlstarlet select -T -t -v '//descriptors' $ARCHIVO`
 niveles=`xmlstarlet select -T -t -v '//title' $ARCHIVO`
 
 # read descriptiopn and remove html tags
 descripcion=$(xmlstarlet select -T -t -c "JClicProject/settings/description" $ARCHIVO |  sed -e :a -e 's/<[^>]*>//g')
 zip=$(echo $1 | sed s/"zips\/"//g)

 archivo=$(basename $1)
 dir=$(dirname $zip)
 #id=$(grep "$archivo" urls.jclic 2>/dev/null | grep "$dir" 2>/dev/null | awk -F "|" '{print $1}' )
 id=$(grep "$archivo" urls.jclic 2>/dev/null | head -1 | awk -F "|" '{print $1}' )
 image=$(grep $id urls.img 2>/dev/null | awk -F "|" '{print $2}' | awk -F "/" '{print $5}' )

 # change type of " to '
 titulo=$(echo $titulo | sed s/"\""/"'"/g)
 descripcion=$(echo $descripcion | sed s/"\""/"'"/g)

 echo "INSERT INTO jclic (id,image,actividad,edad,materia,descripcion,idioma,archivo)
  VALUES (\"$id\", \"$image\", \"$titulo\",\"$edad\", \"$materia\", \"$descripcion\", \"$idioma\", \"$2\");
" 
 rm -f todo
}


for i in $(find ${ZIPS_DIR} -name "*.inst" -type f); do
 
 zip_file=$(echo $i| sed s/"inst"/"zip"/g)

 if [ -f $zip_file ]; then
  _log "Encontrado $zip_file"
  info_zip $zip_file $i
 else
   _log "No esta descargado"
 fi
done
