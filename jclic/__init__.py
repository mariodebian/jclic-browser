#!/usr/bin/env python
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

import pygtk
pygtk.require('2.0')
from gtk import *
import gtk.glade

import os
import sys

import sqlite
import urllib2
import threading

import datetime
from Numeric import array
from gettext import gettext as _
from gettext import bindtextdomain, textdomain
from locale import setlocale, LC_ALL

# program name to use in gettext .mo
PACKAGE = "jclic_browser"

# constant to font sizes
PANGO_SCALE=1024

# Database in homedir hidden file
dbname=os.environ['HOME'] + '/.jclic_browser.db'

# PXES Username's home root dir
homedir="/home"

IMG_DIR="/var/lib/jclic_browser/imgs/"
ZIP_DIR="/var/lib/jclic_browser/zips/"

# FIXME not use it
URL_IMG="/usr/share/jclic_browser/utils/urls.img"
URL_ZIP="/usr/share/jclic_browser/utils/urls.jclic"


from jclic.JClicLib import JClicLib
from jclic.JClicLib import Workers

# debug put 0 to disable verbose messages
debug=1


gtk.gdk.threads_init()
from threading import Thread

def print_debug(txt):
    if debug:
        print "%s::%s" %(__name__, txt)
    return



class JClicBrowser:
    def __init__(self):
        COL_SEL, COL_ID, COL_ACTIVIDAD, COL_EDAD, COL_MATERIA, COL_IDIOMA, COL_ARCHIVO = range(7)
        self.worker=None
        self.worker_running=False
        self.lib=JClicLib(self)
        if os.path.exists('./po'):
            self.LOCALE_DIR = "./po/"
            self.GLADE_DIR = "./"
            print_debug ("JClicBrowser not installed, using locale in ./po dir")
        else:
            self.GLADE_DIR = "/usr/share/jclic_browser/"
            self.LOCALE_DIR = "/usr/share/locale"
	    
	    # gettext support
        setlocale( LC_ALL )
        bindtextdomain( PACKAGE, self.LOCALE_DIR )
        textdomain( PACKAGE )
        gtk.glade.bindtextdomain(PACKAGE, self.LOCALE_DIR)
        gtk.glade.textdomain(PACKAGE)
        
        # Widgets
        self.ui = gtk.glade.XML(self.GLADE_DIR + 'jclic_browser.glade')
        self.main = self.ui.get_widget('jclicBrowser')
        self.equipos = self.ui.get_widget('networkwindow')
        self.about = self.ui.get_widget('aboutdialog')
        self.progresswindow = self.ui.get_widget('progresswindow')
        
        # widget de progressbar
        self.progressbar = self.ui.get_widget('progressbar')
        
        # signals and buttons
        self.salir = self.ui.get_widget('quitbutton')
        self.salir.connect('clicked', self.salirse )

        self.info = self.ui.get_widget('infobutton')
        self.info.connect('clicked', self.ayuda )

        self.searchtxt = self.ui.get_widget('searchtxt')
        self.searchtxt.connect('activate', self.buscar )
        
        self.searchbutton = self.ui.get_widget('searchbutton')
        self.searchbutton.connect('clicked', self.buscar )
        
        self.showallbutton = self.ui.get_widget('showallbutton')
        self.showallbutton.connect('clicked', self.mostrar_todo )

        self.send = self.ui.get_widget('sendbutton')
        self.send.connect('clicked', self.equipos_show )

        self.netcancelbutton = self.ui.get_widget('netcancelbutton')
        self.netcancelbutton.connect('clicked', self.equipos_hide)
        
        self.netsendtobutton = self.ui.get_widget('netsendtobutton')
        self.netsendtobutton.connect('clicked', self.on_netsendtobutton_click)

        self.refreshdbbutton = self.ui.get_widget('refreshdbbutton')
        self.refreshdbbutton.connect('clicked', self.refresh_db_click)

        self.progresscancel = self.ui.get_widget('progresscancelbutton')
        self.progresscancel.connect('clicked', self.progresswindow_hide)

        # widgets combo list and down progress label
        self.combolist = self.ui.get_widget('combolist')
        self.progresslabeldown = self.ui.get_widget('progresslabeldown')
        self.statusbar = self.ui.get_widget('statusbar')
        
        # TextView elements and buffers
        self.datatxt = self.ui.get_widget('datatxt')
        self.datatxt.set_editable(False)
        self.datatxt.set_cursor_visible(False)
        self.datatxtbuffer = self.datatxt.get_buffer()
        
        self.imagetxt = self.ui.get_widget('imagetxt')
        self.imagetxt.set_editable(False)
        self.imagetxt.set_cursor_visible(False)
        self.imagetxtbuffer = self.imagetxt.get_buffer()

        # close windows signals
        self.main.connect('destroy', self.salirse )
        self.equipos.connect('destroy', self.equipos_hide)
        self.progresswindow.connect('destroy', self.progresswindow_hide)
        
        # GtkTreeView elements
        self.tabla = self.ui.get_widget('data')
        self.connectedlist = self.ui.get_widget('connectedlist')
        self.leftlist = self.ui.get_widget('leftlist')

        # Models
        self.model = gtk.ListStore (bool, int, str, str, str, str, str)
        self.model_homes = gtk.ListStore (bool, str)
        self.model_leftlist = gtk.ListStore (str)
        self.model_combolist = gtk.ListStore (str)


        self.selectedrows=[]
        
        
        # Check that dbname exists
        # if not create it with apropiate schema
        if not os.path.isfile(dbname):
            if self.create_database ():
                self.lib.info_msg ( _("INIT: Empty database %s created.") % dbname )
            else:
                self.lib.error_msg ( _("INIT: Error creating database. Check you have sqlite installed.")  )
        
        # database connect or die :(
        try:
            self.conn = sqlite.connect(db=dbname, mode=077)
            self.cursor = self.conn.cursor()
        except:
            self.lib.error_msg (_("INIT: ERROR conecting to database %s.") % dbname)
            sys.exit(0)
	    
        # sqlite info:
        #   http://bulma.net/body.phtml?nIdNoticia=1472
        #   http://listas.aditel.org/archivos/python-es/2005-February/012170.html

    
    def on_leflist_click(self, leftlist):
        (model, iter) = leftlist.get_selected()
        self.leftlist_value = model.get_value(iter, 0)
        print_debug ("ON_LEFT_LIST: selected \"%s\"" %self.leftlist_value)
        
        # read combo value and exec SQL statement
        SQL="SELECT * from jclic WHERE " + self.combo_value + "=\"" + self.leftlist_value + "\"" 
        self.read_database(SQL)
        
        return


    def on_tabla_click(self, tabla):
        (model, iter) = tabla.get_selected()
        if not iter:
            return
        self.tabla_value = model.get_value(iter, 1)
        self.tabla_archivo = model.get_value(iter, 6)
        print_debug ("ON_TABLA_CLICK: selected \"%d\"" % self.tabla_value)
        # read list value and exec SQL into textview
        SQL="SELECT * from jclic WHERE id=\"%d\" AND archivo=\"%s\" " % (self.tabla_value, self.tabla_archivo)
        self.populate_datatxt(SQL)
        return
        
    """
    def write_into_statusbar(self,msg):
        # thread this function
        #print_debug("Writing \"%s\" into statusbar" % msg)
        th.stop()
        th.start()
        th.run(self.write_into_statusbar2, [msg])
    """


    def write_into_statusbar(self, msg, *args):
        print_debug("STATUSBAR: Writing \"%s\" into statusbar" % msg)
        context_id=self.statusbar.get_context_id("status")
        self.statusbar.pop(context_id)
        self.statusbar.push(context_id, msg)
        return

    

    

    def check_populate_db (self):
        print_debug( _("CHECK_POPULATE_DB: Calculating number of rows...") )
        SQL="SELECT COUNT(*) from jclic;"
        self.cursor.execute(SQL)
        self.row = self.cursor.fetchone()
        if self.row[0] < 1:
            self.lib.error_msg ( _("The database is empty.") )
        return


    """
    def read_database(self,SQL):
        # thread this function
        th.stop()
        th.start()
        th.run(self.read_database2, [SQL])
    """
        
    def read_database(self, SQL):
        COL_SEL, COL_ID, COL_ACTIVIDAD, COL_EDAD, COL_MATERIA, COL_IDIOMA, COL_ARCHIVO = range(7)
        self.write_into_statusbar( _("Reading data...") )
        # clear TreeView
        self.check_populate_db ()
        
        # Clean list (only delete unchecked)
        self.clean_datalist()
        
        print_debug ( SQL )
        # execute SQL stament
        self.cursor.execute(SQL)
        self.row = self.cursor.fetchone()
        counter=0
        while self.row != None:
            print_debug ( "READ_DATABASE: " + _("Row %d") % self.row['id'])
            self.iter = self.model.append (None)
            self.model.set_value (self.iter, COL_SEL, False)
            self.model.set_value (self.iter, COL_ID, self.row['id'] )
            self.model.set_value (self.iter, COL_ACTIVIDAD, self.row['actividad'] )
            self.model.set_value (self.iter, COL_EDAD, self.row['edad'])
            self.model.set_value (self.iter, COL_MATERIA, self.row['materia'])
            self.model.set_value (self.iter, COL_IDIOMA, self.row['idioma'])
            self.model.set_value (self.iter, COL_ARCHIVO, self.row['archivo'])
            self.row = self.cursor.fetchone()
            counter=counter+1
        
        print_debug ("READ_DATABASE: total readed %d" %(counter) )
        self.write_into_statusbar( _("Found %d activities") %(counter) )
        if counter == 0:
            self.lib.info_msg( _("No activities found.") )
        return


    def clean_datalist(self):
        # search checked boxes and save in pathlist
        pathlist=[]
        self.model.foreach(self.delete_not_checked, (pathlist))
        
        # remove in reverse order to avoid of loose pointers
        pathlist.reverse()
        for path in pathlist:
            self.model.remove(self.model.get_iter(path))
        return
    
    def delete_not_checked(self, model, path, iter, data):
        selected=self.model.get_value(iter, 0)
        filename=self.model.get_value(iter, 6)
        if selected :
            print_debug( "DELETE_NOT_CHECKED: _NOT_ deleting %s" % filename )
        else:
            print_debug( "DELETE_NOT_CHECKED: deleting %s " % filename )
            data.append(path)            
        return




    def populate_datatxt(self, SQL):
        self.write_into_statusbar( _("Reading data...") )
        
        print_debug( "POPULATE_DATATXT: Populate datatxt..." )
        
        # clear datatxtbuffer
        start = self.datatxtbuffer.get_start_iter()
        end = self.datatxtbuffer.get_end_iter()
        self.datatxtbuffer.delete(start, end)
        
        # clear imagetxtbuffer
        start = self.imagetxtbuffer.get_start_iter()
        end = self.imagetxtbuffer.get_end_iter()
        self.imagetxtbuffer.delete(start, end)
        
        
        # read iters
        iter = self.datatxtbuffer.get_iter_at_offset (0)
        iter_image = self.imagetxtbuffer.get_iter_at_offset (0)
        
        print_debug ( SQL )
        self.cursor.execute(SQL)
        self.row = self.cursor.fetchone()
        while self.row != None:
            print_debug ("POPULATE_DATABASE: " + _("Row %d") % self.row['id'])
            self.tabla_image=self.row['image']
            if os.path.isfile( IMG_DIR + self.row['image'] ):
                # FIXME sometimes get more than one image
                self.imagetxtbuffer.insert_pixbuf (iter_image, gtk.gdk.pixbuf_new_from_file(IMG_DIR + self.row['image']) )
            else:
                self.imagetxtbuffer.insert (iter_image, "\n\n\t\t" +  _("Image not avalaible.") + "\n\n\t\t")
                anchor_image = self.imagetxtbuffer.create_child_anchor(iter_image)
                
                # A button
                downloadimagebutton=gtk.Button( label=_("Download image"), stock=None )
                downloadimagebutton.connect("clicked", self.on_downloadimagebutton_click )
                self.imagetxt.add_child_at_anchor (downloadimagebutton, anchor_image)
                downloadimagebutton.show_all ()
                
                self.datatxtbuffer.insert_with_tags_by_name (iter, "\n\n" , "medium")
                
            self.datatxtbuffer.insert (iter, "\n")
            self.datatxtbuffer.insert_with_tags_by_name (iter, self.row['actividad'] + "\n" , "big")
            self.datatxtbuffer.insert_with_tags_by_name (iter, _("Age") + ": " + self.row['edad'] + "\n" , "medium")
            self.datatxtbuffer.insert_with_tags_by_name (iter, _("Language") + ": " +  self.row['idioma'] + "\n" , "medium")
            self.datatxtbuffer.insert_with_tags_by_name (iter, _("Descriptors") + ": " + self.row['materia'] + "\n" , "medium")
            self.datatxtbuffer.insert_with_tags_by_name (iter, _("File") + ": " + self.row['archivo'] + "\n\n" , "medium")
            
            isfile=_("Yes")
            # if zip file don't exists show download button
            print_debug("searching file %s" %(self.row['archivo']) )
            if not os.path.isfile( self.row['archivo'] ):
                isfile=_("No")
                self.datatxtbuffer.insert_with_tags_by_name (iter, _("Activity file/s not avalaible.") + "\t" , "not_found")
                anchor = self.datatxtbuffer.create_child_anchor(iter)
                
                # A button
                downloadzipbutton=gtk.Button( label=_("Download Activity"), stock=None )
                downloadzipbutton.connect("clicked", self.on_downloadzipbutton_click )
                self.datatxt.add_child_at_anchor (downloadzipbutton, anchor)
                downloadzipbutton.show_all ()
                
                self.datatxtbuffer.insert_with_tags_by_name (iter, "\n\n" , "medium")
                
            self.datatxtbuffer.insert_with_tags_by_name (iter, _("Description") + ":\n" + self.row['descripcion'] + "\n" , "small")
            self.datatxtbuffer.insert(iter, "\n\n")
            self.write_into_statusbar( _("Activity: %(act)s   Language: %(lang)s   Downloaded: %(status)s") 
                    %{'act':self.row['actividad'], 'lang':self.row['idioma'], 'status':isfile} )
            self.row = self.cursor.fetchone()
            
        return

    def download(self, url, path):
        print_debug("download() url='%s' PATH='%s'" %(url,path) )
        self.worker=Workers(self, target=self.lib.download_inst, args=[url, path])
        self.worker.start()
        
        """
        # thread function
        th.stop()
        th.start()
        th.run(self.download_inst, [url, fname])
        """


    def on_downloadzipbutton_click(self, widget):
        widget.set_sensitive(False)
        self.write_into_statusbar( _("Downloading %s ... ") % (self.tabla_archivo))
        
        # extract zip filename (end of uri)
        i = self.tabla_archivo.rfind('/')
        inst = self.tabla_archivo[i+1:]
        
        # Use zip_urls sqlite data
        SQL="SELECT DISTINCT id, url from zip_urls WHERE id='%s'" % self.tabla_value
        
        # in this table with same id we can take some url's spaces separated
        print_debug (SQL)
        self.cursor.execute(SQL)
        self.row = self.cursor.fetchone()
        while self.row != None:
            url=self.row[1]
            self.row = self.cursor.fetchone()
        
        # make dir ( directory/[optional-subdirectory]/file.jclic.zip )
        dirs=self.tabla_archivo.split('/')[0:-1]
        path=""
        for _dir in dirs:
            path=path + "/" + _dir
            if not os.path.isdir(path):
                print_debug(_("Created %s directory") % path)
                os.mkdir(path)
        
        self.download(url, path)
        
        return


    def on_downloadimagebutton_click(self, widget):
        widget.set_sensitive(False)
        print_debug ( "Download image: %s" % self.tabla_image)
        self.write_into_statusbar( _("Downloading %s ... ") % (self.tabla_image) )
        
        # Connect to JClic server and download image in /tmp/
        url="http://clic.xtec.net/gifs/%s" % self.tabla_image
        
        self.download(url, IMG_DIR)
        
        return


    def combolist_cb(self, combolist):
        model = combolist.get_model()
        index = combolist.get_active()
        if index > -1:
            self.combo_value=model[index][0]
            print_debug ( '%s selected' % self.combo_value) 
            self.read_category()
        return


    def read_category(self):
        self.model_leftlist.clear()
        query = "SELECT DISTINCT " + self.combo_value + " FROM jclic;"
        print_debug (query)
        self.cursor.execute(query)
        self.row = self.cursor.fetchone()
        counter=0
        while self.row != None:
            print_debug ("row= %s" % self.row[0])
            self.iter_leftlist = self.model_leftlist.append(None)
            self.model_leftlist.set_value (self.iter_leftlist, 0, self.row[0])
            self.row = self.cursor.fetchone()
            counter=counter+1
        print_debug ("READ_CATEGORY: total readed %d" %(counter) )
        return


    def refresh_db_click(self, True):
        self.progresswindow.show()
        
    def progresswindow_show(self,True):
        self.progresswindow.show()

    def progresswindow_hide(self,True):
        self.progresswindow.hide()
	
    def leer_homes(self):
        COL_SEL, COL_USER = range(2)
        self.model_homes.clear()
        print_debug ( "LEER_HOMES: " + _("Searching users...") )
        self.homes=os.listdir( homedir )
        for user in self.homes:
            if os.path.isdir(os.path.join(homedir, user)):
                print_debug (_("User %s") % user)
                self.iter_homes = self.model_homes.append(None)
                self.model_homes.set_value (self.iter_homes, COL_SEL, False)
                self.model_homes.set_value (self.iter_homes, COL_USER, user)
        return

    def equipos_show(self, True):
        #self.selectedrows=[]
        #clean selectedrows
        self.selectedrows=[]
        for row in self.model:
            if row[0]:
                self.selectedrows.append ("%d|%s|%s" %(row[1],row[2],row[6]) )
        print_debug ( "EQUIPOS_SHOW: " + _("Selected: %s") % self.selectedrows)
        
        # search homes dirs
        self.leer_homes ()
        
        # show window if selected items
        if len(self.selectedrows) > 0 :
            self.equipos.show ()
        else:
            self.lib.error_msg( _("Please, select one or more activities.") )
        return

    def on_netsendtobutton_click(self, widget):
        print_debug( _("Generating XML JClic library...") )
        errors=False
        # get selected users
        self.selectedusers=[]
        for row in self.model_homes:
            if row[0]:
                self.selectedusers.append ("%s" %(row[1]) )
        print_debug ( _("Selected: %s") % self.selectedusers)
        if len(self.selectedusers) == 0 :
            self.lib.error_msg( _("Please, select one or more users.") )
            return
        
        self.projects_elements=""
        for element in self.selectedrows:
            (id,title,zip) = element.split('|')
            #path=ZIP_DIR + zip
            path=zip
            print_debug("on_netsend path=%s zip=%s" %(path,zip))
            self.projects_elements=self.projects_elements+"<menuElement caption=\"%s\" path=\"%s\" description=\"%s\" />" %(title, path, title)
            self.projects_elements=self.projects_elements+'\n'
        
        #print self.projects_elements
        
        fd=file(self.GLADE_DIR + "/library.jclic", 'r')
        library_list=fd.readlines()
        fd.close()
        
        jclic_xml_file=""
        for line in library_list:
            jclic_xml_file+=line
        
        # FIXME use python-xml libs ????
        # Parse XML file
        # search and replace this items:
        #  %PROJECT_NAME% %PROJECT_TITLE% %PROJECT_DATE% %PROJECT_ELEMENTS%
        
        date="%s" %(datetime.date.today())
        (year, month, day) = date.split('-')
        
        jclic_xml_file=jclic_xml_file.replace('%PROJECT_NAME%', _("JClic-Browser") )
        jclic_xml_file=jclic_xml_file.replace('%PROJECT_TITLE%', _("Main library") )
        jclic_xml_file=jclic_xml_file.replace('%PROJECT_DATE%', '%s/%s/%s' %(month,day,year) )
        jclic_xml_file=jclic_xml_file.replace('%PROJECT_ELEMENTS%', self.projects_elements)
        
        
        for user in self.selectedusers:
            # check if configuration file exists
            conf_file="/home/%s/.edu.xtec.properties" %(user)
            if not os.path.isfile(conf_file):
                fd=file(conf_file, 'w')
                fd.write("""#date=%s/%s/%s\nJClic=/home/%s/JClic\nlanguage=es\n""" %(day, month, year, user) )
                fd.close()
            
            # read JClic dir:
            print_debug( _("Read configuration file of user \"%s\".") %(user) )
            fd = file(conf_file, 'r')
            lines = fd.readlines()
            fd.close()
            for line in lines:
                # delete '\n'
                line=line.split('\n')
                # search '='
                if line[0].find('=') > 0:
                    (var, value) = line[0].split('=')
                    if var=="JClic":
                        jclic_dir=value
                    if var=="language":
                        # FIXME not using yet
                        jclic_language=value
                        
            if jclic_dir=="" or not os.path.isdir(jclic_dir):
                print_debug( _("Error %s dir not found, creating ...") %(jclic_dir) )
                os.system("gksudo --message \"%s\" /usr/bin/jclicbrowser-sudo create '%s'" 
                                %( _("Input your password to create user template."), user ) )
                if not os.path.isdir(jclic_dir):
                    self.lib.error_msg( _("Error writing data in \"%s\" user dir. Access Denied.") %(user) )
                    self.equipos_hide(True)
                    return
            else:
                print_debug( _("%s found and exist") %(jclic_dir) )
            
            #if not os.path.isfile( jclic_dir + "/projects/library.jclic" ):
            #    # FIXME should I create complete directory tree if no exists???
            #    self.lib.error_msg ( _("Library file of user \"%s\" not found, please run JClic with this user.") %(user)  )
            
            try:
                fd = file(jclic_dir + "/projects/library.jclic", 'w')
                fd.write(jclic_xml_file)
                fd.close()
                print_debug( _("Save library file of user \"%s\".") %(user) )
                
                
            except:
                # usually are here is access denied
                # We use sudo
                # can use gksu too:
                #   gksu -m "Message to display" -k "command"
                #errors=True
                #self.lib.error_msg( _("Error writing data in \"%s\" user dir. Access Denied.") %(user) )
                try:
                    # use /usr/share/jclic_browser/copy_library.sh
                    # $1=/tmp/library.jclic
                    # $2=jclic_dir + "/projects/library.jclic"
                    tmpfile="/tmp/library.jclic"
                    fd = file(tmpfile, 'w')
                    fd.write(jclic_xml_file)
                    fd.close()
                    cmd="gksudo /usr/bin/jclicbrowser-sudo library '%s' '%s' " %(tmpfile, jclic_dir+"/projects/library.jclic")
                    os.system( cmd )
#                    tmpfile2="/tmp/copy_unauthorized.sh"
#                    fd = file(tmpfile2, 'w')
#                    cmd="#!/bin/sh" + '\n'
#                    cmd= cmd + "gksudo /usr/share/jclic_browser/utils/copy_library.sh \"%s\" \"%s\" " %(tmpfile, jclic_dir + "/projects/library.jclic")
#                    cmd = cmd + '\n'
#                    fd.write(cmd)
#                    fd.close()
#                    cmd="sh %s" %(tmpfile2)
#                    print "EXEC: %s" %(cmd)
                    
                    #if os.path.isfile( jclic_dir+"/projects/library.jclic.lock" ):
                    #    self.lib.error_msg( _("Error writing data in \"%s\" user dir. Access Denied.") %(user) )
                    #else:
                    #    print_debug( _("Data send to selected users sucesfully.") )
                    
                    # delete temp files
                    os.remove(tmpfile)
                    #os.remove(tmpfile2)
                except:
                    errors=True
                    self.lib.error_msg( _("Error writing data in \"%s\" user dir. Access Denied.") %(user) )
                #return
                    
        self.equipos_hide(True) 
        if not errors:
            self.lib.info_msg( _("Data send to selected users sucesfully.")  )
        else:
            self.lib.info_msg( _("You don't have enought privileges to copy JClic library to some user's home.\n\nPlease, read the jclic-browser README file.") )

    def equipos_hide(self, True):
        # hide window
        print_debug (_("hide hosts"))
        self.equipos.hide()
        return

    def ayuda(self, True):
        self.about.show()
        print_debug ( _("Help...") )
        return

    def buscar(self, True):
        advancedsearch=False
        if self.searchtxt.get_text() != '' :
	       # FIXME use and to search more than one item
	       searchitem=self.searchtxt.get_text().split(' ')
	       for item in searchitem:
	           if item == "and" or item == "AND":
	               print_debug( "FOUND AND" )
	               searchby=" AND "
	               advancedsearch=True
	           if item == "or" or item == "OR":
	               print_debug( "FOUND OR")
	               searchby=" OR "
	               advancedsearch=True
	               
	       print_debug (_("Searching \"%s\" ") % self.searchtxt.get_text())
	       txt=self.searchtxt.get_text()
	       if not advancedsearch:
	           SQL="SELECT * from jclic WHERE id LIKE \"%" + txt + "%\" OR descripcion LIKE \"%" + txt + "%\" OR actividad LIKE \"%" + txt + "%\" OR edad LIKE \"%" + txt + "%\" OR materia LIKE \"%" + txt + "%\" OR archivo LIKE \"%" + txt + "%\";"
	           self.read_database(SQL)
	       else:
	           print_debug( "ADVANCED SEARCH")
	           SQL="SELECT * from jclic WHERE  "
	           item_num=0
	           for item in searchitem:
	               if item != "and" and item != "AND" and item != "or" and item != "OR":
	                   if item_num!=0:
	                       SQL = SQL + " " + searchby
	                   SQL= SQL + " ( descripcion LIKE \"%" + item + "%\" OR actividad LIKE \"%" + item + "%\" "
	                   SQL= SQL + " OR edad LIKE \"%" + item + "%\" OR materia LIKE \"%" + item + "%\" OR archivo LIKE \"%" + item + "%\""
	                   SQL= SQL + " ) "
	                   item_num=item_num+1
	           SQL=SQL+";"
	           self.read_database(SQL)
        else:
	       SQL="SELECT * from jclic"
	       self.read_database(SQL)
	       print_debug (_("Nothing to search :("))
	       return

    def mostrar_todo(self, True):
        SQL="SELECT * from jclic;"
        self.searchtxt.set_text("")
        self.read_database(SQL)
        print_debug (_("Clean up filters"))
        return
        
    def activar_casilla(self, cell, path, model):
        model[path][0] = not model[path][0]
        print_debug ("Toggle '%s' to: %s" % (not model[path][0], model[path][0],))
        
        # FIXME ask for download if don't exists
        print_debug("searching file %s" % (model[path][6]) )
        if not os.path.isfile( model[path][6] ) and model[path][0]:
            if self.lib.ask_msg( _("Zip file not found, download it?") ) == "yes":
                # response YES
                print_debug( _("Downloading....") )
                self.tabla_value = model[path][1]
                self.tabla_archivo = model[path][6]
                self.on_downloadzipbutton_click(self)
            else:
                # response NO or close window, UNCHECK file
                print_debug ( _("User don't want to download \"%s\"") %(model[path][6]) )
                model[path][0]=False
        return
        
    def activar_home_casilla(self, cell, path, model):
        model[path][0] = not model[path][0]
        print_debug ("Toggle '%s' to: %s" % (not model[path][0], model[path][0],))
        return

    def init_tabla(self):
        COL_SEL, COL_ID, COL_ACTIVIDAD, COL_EDAD, COL_MATERIA, COL_IDIOMA, COL_ARCHIVO = range(7)
        self.tabla.set_model (self.model)
        
        cell1 = gtk.CellRendererToggle ()
        column1 = gtk.TreeViewColumn (_("Sel"), cell1, active = COL_SEL)
        cell1.set_property('activatable', True)
        cell1.connect('toggled', self.activar_casilla, self.model )
        
        self.tabla.append_column (column1)
		
        cell2 = gtk.CellRendererText ()
        column2 = gtk.TreeViewColumn (_("Id"), cell2, text = COL_ID)
        column2.set_resizable (True)	
        column2.set_sort_column_id(COL_ID)
        self.tabla.append_column (column2)

        cell3 = gtk.CellRendererText ()
        column3 = gtk.TreeViewColumn (_("Activity"), cell3, text = COL_ACTIVIDAD)
        column3.set_resizable (True)	
        column3.set_sort_column_id(COL_ACTIVIDAD)
        self.tabla.append_column (column3)
	
        cell4 = gtk.CellRendererText ()
        column4 = gtk.TreeViewColumn (_("Age"), cell4, text = COL_EDAD)
        column4.set_resizable (True)
        column4.set_sort_column_id(COL_EDAD)
        self.tabla.append_column (column4)

        cell5 = gtk.CellRendererText ()
        column5 = gtk.TreeViewColumn (_("Descriptors"), cell5, text = COL_MATERIA)
        column5.set_resizable (True)
        column5.set_sort_column_id(COL_MATERIA)
        self.tabla.append_column (column5)

        cell6 = gtk.CellRendererText ()
        column6 = gtk.TreeViewColumn (_("Language"), cell6, text = COL_IDIOMA)
        column6.set_resizable (True)
        column6.set_sort_column_id(COL_IDIOMA)
        self.tabla.append_column (column6)
        
        cell7 = gtk.CellRendererText ()
        column7 = gtk.TreeViewColumn (_("File"), cell7, text = COL_ARCHIVO)
        column7.set_resizable (True)
        column7.set_sort_column_id(COL_ARCHIVO)
        self.tabla.append_column (column7)
        
        
        tabla_file = self.tabla.get_selection()
        tabla_file.connect("changed", self.on_tabla_click)
        return

    def init_homes(self):
        COL_SEL, COL_USER = range(2)
        self.connectedlist.set_model (self.model_homes)
        
        cell1 = gtk.CellRendererToggle ()
        column1 = gtk.TreeViewColumn (_("Sel"), cell1, active = COL_SEL)
        cell1.set_property('activatable', True)
        cell1.connect('toggled', self.activar_home_casilla, self.model_homes )
        
        self.connectedlist.append_column (column1)
		
        cell2 = gtk.CellRendererText ()
        column2 = gtk.TreeViewColumn (_("Username"), cell2, text = COL_USER)
        column2.set_resizable (True)	
        column2.set_sort_column_id(COL_USER)
        self.connectedlist.append_column (column2)
        return

    def init_lista(self):
        
        self.leftlist.set_model (self.model_leftlist)
		
        cell = gtk.CellRendererText ()
        column = gtk.TreeViewColumn (_("Property"), cell, text = 0)
        column.set_resizable (True)	
        column.set_sort_column_id(1)
        self.leftlist.append_column (column)

        selection = self.leftlist.get_selection()
        selection.connect("changed", self.on_leflist_click)
        return
        
    def init_combo(self):
        
        self.combolist.set_model (self.model_combolist)
        # FIXME should use english table names????
        lista=['Actividad', 'Edad', 'Idioma']
        cell = gtk.CellRendererText()
        
        self.combolist.pack_start(cell)
        self.combolist.add_attribute(cell, 'text', 0)
        for n in lista:
            self.model_combolist.append([n])
        self.combolist.set_model(self.model_combolist)
        self.combolist.connect('changed', self.combolist_cb)
        return

    def insert_one_tag_into_buffer(buffer, name, *params):
        tag = gtk.TextTag(name)
        while(params):
            tag.set_property(params[0], params[1])
            params = params[2:]
        table = buffer.get_tag_table()
        table.add(tag)

    def init_datatxt(self):
        tag=gtk.TextTag("big")
        tag.set_property("size", 20 * PANGO_SCALE)
        table=self.datatxtbuffer.get_tag_table()
        table.add(tag)
        
        tag=gtk.TextTag("medium")
        tag.set_property("size", 10 * PANGO_SCALE)
        table=self.datatxtbuffer.get_tag_table()
        table.add(tag)
        
        tag=gtk.TextTag("not_found")
        tag.set_property("size", 10 * PANGO_SCALE)
        tag.set_property("foreground", "#FF0000")
        table=self.datatxtbuffer.get_tag_table()
        table.add(tag)
        
        tag=gtk.TextTag("small")
        tag.set_property("size", 8 * PANGO_SCALE)
        table=self.datatxtbuffer.get_tag_table()
        table.add(tag)
        
        self.datatxt.set_property("wrap-mode", gtk.WRAP_WORD)
        

    def salirse(self,True):
        print_debug ( _("Exiting") )
        self.conn.close()
        gtk.main_quit()
        sys.exit(0)

    def run (self):
        gtk.main ()

def main():
    jclic = JClicBrowser ()
    jclic.init_tabla ()
    jclic.init_homes ()
    jclic.init_lista ()
    jclic.init_combo ()
    jclic.init_datatxt ()
    # Run app    
    jclic.run ()


if __name__ == '__main__':
    main()



