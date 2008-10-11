#!/bin/sh

descargar_zip=zips/
descargar_img=img/

download_list() {
 echo "Downloadinf list of all activities"
 wget -q "http://clic.xtec.net/db/listact_es.jsp?lang=es&ordre=0&desc=1&from=1&area=*&idioma=*&ctm=1&nivell=*&text_titol=&text_aut=&text_desc=&num=1000" -O web
 grep act_es.jsp web | grep id > lista
 cat lista | awk -F "href=\"" '{print $2}' | awk -F "\">" '{print "http://clic.xtec.net/db/"$1}' > urls
 rm -f web lista
 echo "Avalaible "`cat urls | wc -l` "activities"
}

update_url_list() {
 rm -f urls.jclic
 rm -f urls.img
 for cosa in $(cat urls); do
   id_act=$(echo $cosa | awk -F "?id=" '{print $2}' )
   echo "Downloading page $id_act"
   wget -q $cosa -O web
   zip=$(grep urlJC web | awk -F "-->" '{print $2}' | awk -F "<\!--" '{print $1}' 2> /dev/null)
   img=$(grep "name=\"img\"" web | awk -F "src=\"" '{print $2}' | awk -F "\" " '{print $1}' )
   echo $id_act"|"$zip >> urls.jclic
   echo $id_act"|"$img >> urls.img
   rm -f web
 done
}

download_jclic() {
 for line in $(cat urls.jclic); do
  id_act=$(echo $line | awk -F "|" '{print $1}' )
  urls=$(echo $line | awk -F "|" '{print $2}' )
  echo "Checking zip data of $id_act"
  for url in $urls; do
      echo $url
      pro_name=`echo $url| awk -F "/" '{print $5}'`
      act_name=`echo $url| awk -F "/" '{print $7}'`
      if [ `echo $act_name|grep -c ".zip"` == 0 ]; then
        pro_name=`echo $url| awk -F "/" '{print $5"/"$7}'`
        act_name=`echo $url| awk -F "/" '{print $8}'`
      fi
      # creamos dir si no existe
      if [ ! -d $descargar_zip/$pro_name ]; then
       echo "mkdir -p $descargar_zip/$pro_name"
       mkdir -p $descargar_zip/$pro_name
      fi

     # miramos si ya esta bajado
     if [ -f $descargar_zip/$pro_name/$act_name ]; then
       echo "Encontrado $act_name"
     else
       echo "  descargando $url"
       wget -q $url
       echo "mv $act_name $descargar_zip/$pro_name"
       mv -i "$act_name" $descargar_zip/$pro_name
     fi
  done
 done
}

download_img() {
 for line in $(cat urls.img); do
  id_act=$(echo $line | awk -F "|" '{print $1}' )
  urls=$(echo $line | awk -F "|" '{print $2}' )
  echo "Checking img data of $id_act"
  for url in $urls; do
      echo $url
      act_name=`echo $url| awk -F "/" '{print $5}'`
     # miramos si ya esta bajado
     if [ -f $descargar_img/$act_name ]; then
       echo "Encontrado $act_name"
     else
       echo "  descargando $url"
       wget -q $url
       echo "mv $act_name $descargar_img/"
       mv -i "$act_name" $descargar_img/
     fi
  done
 done
}





download_list

update_url_list

#download_jclic

#download_img
