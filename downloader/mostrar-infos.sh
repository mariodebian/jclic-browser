#!/bin/bash

ZIPS_DIR=/var/lib/jclic_browser/zips/
TMP_DIR=/tmp/jclic

rm -f errors
touch errors

_error() {
  echo "ERROR: $@" 1>&2
  echo "$@" >> errors
}

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
  _error " archivo XML .jclic no encontrado arg1=\"$1\" arg2=\"$2\""
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

 img_url=$(grep $id urls.img | awk -F "|" '{print $2}')
 zip_url=$(grep $id urls.jclic | awk -F "|" '{print $2}'| sed s/"zip"/"inst"/g)

 # change type of " to '
 titulo=$(echo $titulo | sed s/"\""/"'"/g)
 descripcion=$(echo $descripcion | sed s/"\""/"'"/g)

 echo "INSERT INTO jclic (id,image,actividad,edad,materia,descripcion,idioma,archivo)
  VALUES (\"$id\", \"$image\", \"$titulo\",\"$edad\", \"$materia\", \"$descripcion\", \"$idioma\", \"$zip\");

INSERT INTO zip_urls (id, url)
 VALUES (\"$id\", \"$zip_url\");

INSERT INTO img_urls (id, url)
 VALUES (\"$id\", \"$img_url\");

" 
 rm -f todo
}

# delete all database content
echo "

CREATE TABLE jclic (
  ID INTEGER, 
  image VARCHAR(100),  
  actividad VARCHAR(100),
  edad VARCHAR(50), 
  materia VARCHAR(50), 
  descripcion TEXT, 
  idioma VARCHAR(30), 
  archivo VARCHAR(255) 
);

CREATE TABLE zip_urls (
  id INTEGER,
  url TEXT 
);

CREATE TABLE img_urls (
  id INTEGER,
  url TEXT 
);

"


for i in $(find ${ZIPS_DIR} -name "*.inst" -type f); do
 
 zip_file=$(echo "$i"| sed s/"inst"/"zip"/g)

 if [ -f "$zip_file" ]; then
  _log "Encontrado $zip_file"
  info_zip "$zip_file" "$i"
 else
   _error "i=\"$i\" zip_file=\"$zip_file\" no esta descargado"
 fi
done
