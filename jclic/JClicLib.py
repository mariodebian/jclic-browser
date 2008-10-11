# -*- coding: UTF-8 -*-
##########################################################################
# jclic_browser writen by MarioDebian <mariodebian@gmail.com>
#
#    jclic_browser version 0.0.5
#
# Copyright (c) 2005 Mario Izquierdo <mariodebian@gmail.com>
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
###########################################################################

from gettext import gettext as _
import urllib2
import pygtk
pygtk.require('2.0')
import gtk


debug=1

def print_debug(txt):
    if debug:
        print "%s::%s" %("JClicLib", txt)
    return


class JClicLib:
    def __init__(self, main):
        self.main=main
        print_debug ("__init__:init()")
        
    def download_inst(self, url, path):
        gtk.gdk.threads_enter()
        self.main.write_into_statusbar( _("Downloading %s ... ") % (path) )
        gtk.gdk.threads_leave()
        
        baseurl="/".join(url.split("/")[0:-1])
        finst=path + "/" + url.split("/")[-1]
        
        print_debug("DOWNLOAD: Downloading %s => %s" % (url, path))
        if url=="":
            print_debug("DOWNLOAD: ERROR: not url")
            return
        if path=="":
            print_debug("DOWNLOAD: ERROR: not path")
            return
        
        try:
            gtk.gdk.threads_enter()
            self.main.write_into_statusbar( _("Downloading %s ... ") % (path) )
            gtk.gdk.threads_leave()
            
            print_debug( "Downloading URL=%s ... " % (url) )
            furl = urllib2.urlopen(url)
            
            # Save in ZIP_DIR/IMG_DIR
            f = file(finst,'wb')
            f.write(furl.read())
            f.close()
            
            gtk.gdk.threads_enter()
            self.main.write_into_statusbar( _("Download inst file sucessfull, downloading rest of files") )
            gtk.gdk.threads_leave()
            
            files=self.get_allfiles(finst)
            for _file in files:
                gtk.gdk.threads_enter()
                self.main.write_into_statusbar( _("Downloading %s ...") %_file )
                gtk.gdk.threads_leave()
                self.download_file(baseurl + "/" + _file, path + "/" + _file)
                gtk.gdk.threads_enter()
                self.main.write_into_statusbar( "" )
                gtk.gdk.threads_leave()
            
            gtk.gdk.threads_enter()
            SQL="SELECT * from jclic WHERE id=\"%d\" AND archivo=\"%s\" " % (self.main.tabla_value, self.main.tabla_archivo)
            self.main.populate_datatxt(SQL) 
            gtk.gdk.threads_leave()
            
            
            return 1
        except:
            gtk.gdk.threads_enter()
            self.main.write_into_statusbar( _("Download failed.") )
            gtk.gdk.threads_leave()
            return 0
            
    def get_allfiles(self, instfile):
        path=""
        for _dir in instfile.split('/'):
            if _dir.find(".jclic.inst") == -1:
                path=path + _dir + "/"
                
        f = file (instfile, 'r')
        data=f.read().split('\n')
        f.close()
        print_debug(data)
        files=[]
        for line in data:
            if line.find("file src") != -1 :
                files.append( line.split('"')[1] )
        print_debug("download_allfiles() files=%s" %files)
        return files


    def download_file(self, url, dest):
        print_debug("Downloading %s and saving at %s ..." %(url,dest) )
        furl = urllib2.urlopen(url)
        f = file(dest,'wb')
        f.write(furl.read())
        f.close()
        print_debug("Download done.")

    def create_database (self):
        print_debug ( _("CREATE_DATABASE: Creating database schema...") )
        SQL="CREATE TABLE jclic ("
        SQL+="  ID INTEGER, "
        SQL+="  image VARCHAR(100),  "
        SQL+="  actividad VARCHAR(100),"
        SQL+="  edad VARCHAR(50), "
        SQL+="  materia VARCHAR(50), "
        SQL+="  descripcion TEXT, "
        SQL+="  idioma VARCHAR(30), "
        SQL+="  archivo VARCHAR(255) "
        SQL+=");"
        SQL+="CREATE TABLE zip_urls ("
        SQL+="  id INTEGER,"
        SQL+="  url TEXT "
        SQL+=");"
        SQL+="CREATE TABLE img_urls ("
        SQL+="  id INTEGER,"
        SQL+="  url TEXT "
        SQL+=");"
        if os.system("echo -e \"" + SQL + "\" | sqlite " + dbname ):
            return 0
        else:
            return 1



    def error_msg(self,txt):
        d = gtk.MessageDialog(None,
                          gtk.DIALOG_MODAL |
			  gtk.DIALOG_DESTROY_WITH_PARENT,
                          gtk.MESSAGE_WARNING,
                          gtk.BUTTONS_OK,
                          txt)
        d.run()
        d.destroy()
        print_debug ( _("ERROR: %s") % txt )

    
    def info_msg(self,txt):
        d = gtk.MessageDialog(None,
                          gtk.DIALOG_MODAL |
			  gtk.DIALOG_DESTROY_WITH_PARENT,
                          gtk.MESSAGE_INFO,
                          gtk.BUTTONS_OK,
                          txt)
        d.run()
        d.destroy()
        print_debug ( _("INFO: %s") % txt )

    def ask_msg(self,txt):
        response="yes"
        d = gtk.MessageDialog(None,
                          gtk.DIALOG_MODAL |
			  gtk.DIALOG_DESTROY_WITH_PARENT,
                          gtk.MESSAGE_QUESTION,
                          gtk.BUTTONS_YES_NO,
                          txt)
        if d.run() == gtk.RESPONSE_YES:
            response="yes"
        else:
            response="no"
        d.destroy()
        
        return response


from threading import Thread

class Workers:
    """
        Ejemplo de uso:
        self.main.worker=shared.Workers(self, target=self.get_screenshot, args=[ip])
        self.main.worker.start()
    """
    def __init__(self, main, target, args, dog=True):
        self.dog=dog
        self.main=main
        self.target=target
        self.args=args
        
        if not self.dog:
            print_debug ( "worker() no other jobs job=%s args=%s" %(self.target, self.args) )
            self.th=Thread(target=self.target, args=(self.args) )
            self.__stop=True
            return
        
        if self.main.worker_running == True:
            print_debug ( "worker() other jobs pending NO START job=%s args=%s" %(self.target, self.args) )
        else:
            print_debug ( "worker() no other jobs job=%s args=%s" %(self.target, self.args) )
            self.th=Thread(target=self.target, args=(self.args) )
            self.__stop=True
    
    def start_watch_dog(self, dog_thread):
        if not self.dog:
            print_debug ( "start_watch_dog() dog DISABLED" )
            return
        print_debug ( "start_watch_dog() starting watch dog..." )
        watch_dog=Thread(target=self.watch_dog, args=([dog_thread]) )
        watch_dog.start()

    def watch_dog(self, dog_thread):
        print_debug ( "watch_dog()  __init__ " )
        dog_thread.join()
        self.set_finished()
        print_debug ( "watch_dog() FINISHED" )
        
    def start(self):
        if self.main.worker_running == False:
            self.th.start()     # start thread
            self.set_started()  # config var as started
            self.start_watch_dog(self.th) # start watch_dog
        else:
            print_debug ( "worker() other work pending... not starting" )
        
    def stop(self):
        self.__stop=True
        self.__finished=True
        #self.main.worker_running=False
        
    def set_finished(self):
        self.__finished = True
        self.__stop=False
        self.main.worker_running=False

    def set_started(self):
        self.__finished=False
        self.__stop=False
        self.main.worker_running=True

    def is_stoped(self):
        return self.__stop
        
    def get_finished(self):
        return self.__finished

    def set_for_all_action(self, function, allhost, action):
        action_args=[allhost, action]
        Thread( target=function, args=(action_args) ).start()

