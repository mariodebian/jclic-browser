#!/usr/bin/python
# -*- coding: UTF-8 -*-


#
#  Por Mario Izquierdo Rodríguez
#
#  JclicDownloader descarga las actividades que se le pasen como filtro
#


import sgmllib
import sys
import urllib
import os
from time import sleep
import getopt
import zipfile
from xml.dom import minidom

# si test es True se usan archivos descargados
# sino se descarga de la web ( en una conexion lenta puede tardar años
test=False

debug=False

# leemos los enlaces con este link
install_url="http://clic.xtec.net/jnlp/jclic/install.jnlp"

MAX=1000
# todas las actividades
todas_url="http://clic.xtec.es/db/listact_es.jsp?lang=es&ordre=0&desc=1&from=1&area=*&idioma=*&nivell=*&text_titol=&text_aut=&text_desc=&num=1000"

# tipo de url de cada actividad
act_url="http://clic.xtec.es/db/act_es.jsp?id="

#http://clic.xtec.net/projects/sis2x2/jclic/sis2x2.jclic.inst
proy_url="http://clic.xtec.net/projects"

zips_dir="/var/lib/jclic_browser/zips"
img_dirs="/var/lib/jclic_browser/imgs"


class HTMLParser(sgmllib.SGMLParser):
    def __init__(self, mycod=None):
        sgmllib.SGMLParser.__init__(self)
        self.insideTag = 0
        self.links = []
        self.links_with_name = {}
        self.project_names = {}
        self.mycod=mycod

    def parse(self, data):
        self.feed(data)
        self.close()
        #return self.links

    def start_a(self, args):
        for key, value in args:
            if key.lower() == 'href':
                self.insideTag = 1
                self.lastHref = value

    def handle_data(self, data):
        if self.insideTag:
            self.hrefText = data

    def end_a(self):
        #self.links.append(  [self.lastHref, self.hrefText]  )
        self.links.append(  self.lastHref  )
        self.insideTag = 0        
        cod_act=self.get_cod_act(self.lastHref)
        if cod_act != "":
            #print "cod_act=%s nombre=%s" %(cod_act, self.hrefText)
            self.links_with_name[ cod_act ]=self.hrefText
            
        if self.mycod != None:
            project=self.read_project(self.lastHref)
            if project != "":
                self.project_names[ self.mycod ] = project

        
        
    def get_cod_act(self, params):
        if not "id=" in params: return ""
        params=params.split("=")
        return params[1]

    def get_act_names(self):
        return self.links_with_name

    def get_act_name(self, id_act):
        for link in self.links_with_name:
            if link == id_act :
                return self.links_with_name[id_act]
                
    def read_project(self, params):
        if not "argument=" in params: return ""
        params=params.split("=")
        return params[1]
    
    def get_project_names(self, params):
        return self.project_names
        
    def get_project_name(self, id_act):
        #print "buscando id_act=%s" %(id_act)
        for project in self.project_names:
            if project == id_act:
                return self.project_names[id_act]


    def get_hyperlinks(self):
        return self.links



class JclicDownloader:
    def __init__(self):
        if debug: print "__init()__"
        self.todas=None
        
    def get_todas(self):
        if debug: print "get_todas()"
        
        if not test: f=urllib.urlopen(todas_url)
        if test: f=open("lista.html","r")
        
        self.todas = f.read()
        f.close()
        return self.todas
    
    def get_proy_inst(self, id_act):
        #if not test: print "Leyendo proyecto num: %s" %(id_act)
        
        if not test: f=urllib.urlopen(act_url + id_act)
        if test: f=open("proy.html", "r")
        
        myparser2 = HTMLParser(id_act)
        myparser2.parse( f.read() )
        enlaces =myparser2.get_hyperlinks()
        f.close
        return myparser2.get_project_name(id_act)
    
    def crea_directorio(self, dir_name):
        if os.path.isdir(dir_name):
            return
        path_completo="/"
        for path in dir_name.split("/"):
            if path != "":
                path_completo+=path + "/"
                if not os.path.isdir(path_completo):
                    os.mkdir(path_completo)
    
    def get_proy_filelist(self, url):
        
        #check if file exists 
        file_name=url.split('/')[-1]
        proy_dir=zips_dir + "/" + url.split('/')[-3]
        
        if os.path.isfile(proy_dir + "/" + file_name):
            #if debug: print "%s encontrado, no descargando de nuevo..." %(file_name)
            f=open(proy_dir + "/" + file_name, "r")
        else:    
            if debug: print "Descargando %s" %(url)
            f=urllib.urlopen(url)
        
        # read         
        file_src=[]
        folder=None
        name=None
        data=f.readlines()
        f.close
        
        for line in data:
            if "file src" in line:
                file_src.append( line.split('"')[1] )
            if "folder" in line:
                folder=line.split('folder=')[1]
                folder=folder.split('"')[1]
            if "title" in line:
                name=line.split('title=')[1]
                name=name.split('"')[1]
        
        if not os.path.isfile(proy_dir + "/" + file_name):
            # save inst file
            proy_dir=zips_dir + "/" + folder
            if not os.path.isdir(proy_dir):
                print "Creando directorio %s" %(proy_dir)
                self.crea_directorio(proy_dir)
            #if debug: print "Guardando proyecto en:" + proy_dir + "/" + file_name
            f=open(proy_dir + "/" + file_name, "w")
            f.write("".join(data))
            f.close()
        
        if folder!= None:
            # return data
            return [folder, name, file_src]
    
    def get_todas_id(self):
        if debug: print "get_todas_id()"
        self.get_todas()
        myparser = HTMLParser()
        if debug: print "parsing...%d" %len(self.todas)
        
        myparser.parse(self.todas)
        enlaces=myparser.get_hyperlinks()
        self.id_todas=myparser.get_act_names()
        
        self.actividades={}
        parametros={}
        cod_act=None
        counter=0
        for enlace in enlaces:
            if counter > max_files: continue
            #print enlace
            cod_act=None
            if not "?" in enlace: continue
            enlace = enlace.split('?',1)[1]
            
            if not "id=" in enlace: continue
            enlace=enlace.split('=')
            self.actividades[enlace[1]]=[  ]
            counter+=1
            
        if debug: print "Encontradas %d actividades." %len(self.actividades)
        
        return self.actividades
        
    def get_file_list(self):
        if debug: print "get_file_list()"
        if debug: print "Leyendo información de proyectos... (tarda un rato)"
        counter=0
        for act in self.actividades:
            if counter > max_files: continue
            inst_file=self.get_proy_inst(act)
            self.actividades[act].append( inst_file )
            if inst_file != None:
                tmp=self.get_proy_filelist(inst_file)
                folder=tmp[0]
                name=tmp[1]
                src=tmp[2]
            else:
                folder=None
                name=None
                src=[]
            self.actividades[act].append( folder )
            self.actividades[act].append( name )
            self.actividades[act].append( src )
            counter+=1
            #print self.actividades
            #sys.exit(1)


    def download_file(self, url, destino):
        #if debug: print "download_file(%s, %s)" %(url, destino)
        print ":::>>> Descargando %s" %(url.split("/")[-1])
        basedir="/".join(destino.split("/")[:-1])
        self.crea_directorio(basedir)
        f=urllib.urlopen(url)
        data=f.read()
        f.close
        f=open(destino, "w")
        f.write(data)
        f.close()

    def get_zips(self):
        if debug: print "get_zips()"
        
        counter=1
        for id_act in self.actividades:
            if counter > max_files : continue
            if len(self.actividades[id_act]) == 0: continue
            #print self.actividades[id_act]
            if not self.actividades[id_act][1]: continue
            proy_dir=zips_dir + "/" + self.actividades[id_act][1]
            files=self.actividades[id_act][3]
            
            #check for files
            for _file in files:
                if not os.path.isfile(proy_dir + "/" + _file):
                    #http://clic.xtec.net/projects/sis2x2/jclic/sis2x2.jclic.inst
                    url=proy_url + "/" + self.actividades[id_act][1] + "/jclic/" + _file
                    #print url
                    self.download_file(url, proy_dir + "/" + _file)
                else:
                    print "El archivo %s ya existe" %(_file)
            counter+=1

    def read_jclic_xml(self, data):
        parsed={}
        import StringIO                       
        xmldoc = minidom.parse(StringIO.StringIO(str(data)))
        try:
            parsed["title"]=xmldoc.firstChild.childNodes[1].childNodes[1].firstChild.nodeValue
        except:
            pass
        try:    
            parsed["revision_date"]=xmldoc.firstChild.childNodes[1].childNodes[3].getAttribute("date")
        except:
            pass
        try:
            parsed["revision_description"]=xmldoc.firstChild.childNodes[1].childNodes[3].getAttribute("description")
        except:
            pass    
        try:
            parsed["author_mail"]=xmldoc.firstChild.childNodes[1].childNodes[7].getAttribute("mail")
        except:
            pass
        try:
            parsed["author_name"]=xmldoc.firstChild.childNodes[1].childNodes[7].getAttribute("name")
        except:
            pass
        try:
            parsed["language"]=xmldoc.firstChild.childNodes[1].childNodes[9].firstChild.nodeValue
        except:
            pass
        try:
            parsed["description"]=xmldoc.firstChild.childNodes[1].childNodes[11].childNodes[1].firstChild.toxml()
        except:
            pass
        try:
            parsed["descriptors"]=xmldoc.firstChild.childNodes[1].childNodes[13].firstChild.nodeValue
        except:
            pass
        try:    
            parsed["descriptors_area"]=xmldoc.firstChild.childNodes[1].childNodes[13].getAttribute("area")
        except:
            pass
        try:
            parsed["descriptors_level"]= xmldoc.firstChild.childNodes[1].childNodes[13].getAttribute("level")
        except:
            pass
        return parsed
             
 
    
    def read_jclic_from_zip(self, zip_file):
        #print  "Reading ZIP %s" %(zip_file)
        """
        z = zipfile.ZipFile(zip_file, "r")
        for filename in z.namelist():
            if filename.split(".")[-1] != "jclic" : continue
            print "Parseando %s" %filename
            bytes=z.read(filename)
            data=self.read_jclic_xml(bytes)
            print data
            return data
        """        
        try:
            z = zipfile.ZipFile(zip_file, "r")
            for filename in z.namelist():
                if filename.split(".")[-1] != "jclic" : continue
                print "Parseando %s" %filename
                bytes=z.read(filename)
                data=self.read_jclic_xml(bytes)
                print data
                return data
        except:
            pass
            #print "Error reading ZIP file %s" %(zip_file.split("/")[-1] ) 
        
    
    def read_zips(self):
        counter=0
        self.zip_files={}
        for id_act in self.actividades:
            if counter > max_files: continue
            if len(self.actividades[id_act]) == 0: continue
            #print self.actividades[id_act]
            if not self.actividades[id_act][1]: continue
            proy_dir=zips_dir + "/" + self.actividades[id_act][1]
            files=self.actividades[id_act][3]
            for _file in files:
                if _file.split(".")[-1] == "zip":
                    self.zip_files[id_act]=[zips_dir + "/" + self.actividades[id_act][1] + "/" + _file]
                    self.read_jclic_from_zip(zips_dir + "/" + self.actividades[id_act][1] + "/" + _file)
        
        #print self.zip_files
        
##########################################

def usage():
    print ""
    print "jclic_downloader"
    print "             Usage:"
    print "                    --help (this help)"
    print "                    --debug (show verbose text)"
    print ""
    print "                    --update-inst (update/download all inst files)"
    print "                    --update-zips (parse ints files and get jclic.zip files)"
    print "                    --update-imgs (get all image activities)"
    print ""
    print "                    --read-zips (read all zips info)"

# parametros de arranque

options=["help", "debug", "update-inst", "update-zips", "update-imgs", "max=", "read-zips"]
        
try:
    opts, args = getopt.getopt(sys.argv[1:], ":hd", options)
except getopt.error, msg:
    print msg
    print "for command line options use jclic_downloader --help"
    sys.exit(2)

mode=0
max_files=MAX

# process options
for o, a in opts:
    #print o
    #print a
    #print "-----"
    if o in ("-d", "--debug"):
        print "DEBUG ACTIVE"
        debug = True
    if o == "--update-inst": mode=1
    if o == "--update-zips": mode=2
    if o == "--update-imgs": mode=3
    if o ==  "--read-zips":  mode=4
    if o == "--max":
        max_files=int(a)
    if o in ("-h", "--help"):
        usage()
        sys.exit()

##########################################

# self.actividades es un diccionario
# * el key es el id de actividad
# * el valor es una lista
#       lista[0] = fichero jclic.inst
#       lista[1] = directorio de descarga
#       lista[2] = Nombre de actividad (sacado del jclic.inst)
#       lista[3] = otra lista con los ficheros que contiene

if __name__ == "__main__":
    
    if max_files != MAX: print "Límite de número de actividades=%d" %(max_files)
    app = JclicDownloader()
    app.get_todas_id()
    app.get_file_list()
    
    if mode == 2: app.get_zips()
    
    if mode == 3: app.get_imgs()
    
    if mode == 4: app.read_zips()


sys.exit(0)



