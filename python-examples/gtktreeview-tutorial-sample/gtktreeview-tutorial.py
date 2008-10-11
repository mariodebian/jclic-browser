#! /usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade

class GtkTreeViewTutorialSample:
   def __cell_data_func (self, column, cell, model, iter, data=None):
      active = model.get_value (iter, 2)
      nome = model.get_value (iter, 0)
      if active:
         cell.set_property ('foreground', 'red')
	 cell.set_property ('markup', '<b>' + nome + '</b>')
      else:
         cell.set_property ('foreground', 'black')

   def edited_callback (self, cell, rowpath, new_text, user_data):
      model, col_id = user_data
      iter = model.get_iter (rowpath)
      model.set_value (iter, col_id, new_text)

   def __init__ (self):
      self.ui = gtk.glade.XML ('gtktreeview-tutorial.glade')
      self.callbacks = {
         'on_mainwindow_delete_event'  : self.mainwindow_delete_event,  \
	 'on_button_addrow_clicked'    : self.button_addrow_clicked,    \
	 'on_button_deleterow_clicked' : self.button_deleterow_clicked, \
	 'on_button_close_clicked'     : self.button_close_clicked
      }
      self.ui.signal_autoconnect (self.callbacks)
      
      self.mainwindow = self.ui.get_widget ('mainwindow')
      self.treeview   = self.ui.get_widget ('treeview1')
      self.treeview.get_selection().set_mode (gtk.SELECTION_SINGLE)

      self.model = gtk.ListStore (str, str, bool, object, gtk.gdk.Pixbuf)
      COL_NOME, COL_COGNOME, COL_ATTIVO, COL_DATI, COL_FOTO = range(5)
      # Varie forme di inserimento
      iter = self.model.append (['Antonio', 'Rossi', True, None, None])
      iter = self.model.prepend (['Francesco', 'Bianchi', True, None, None])	
      iter = self.model.insert (2, ['Silvio', 'Verdi', False, None, None])
      iter = self.model.insert_before (iter, ['Fabrizio', 'Grigi', False, \
         None, None])
      
      iter = self.model.insert_after (iter, None)
      self.model.set_value (iter, COL_NOME, 'Mario')
      self.model.set_value (iter, COL_COGNOME, 'Gialli')
      self.model.set_value (iter, COL_ATTIVO, True)
      self.model.set_value (iter, COL_DATI, None)
      self.model.set_value (iter, COL_FOTO, None)

      self.treeview.set_model (self.model)

      # Creiamo una cella (immagine, in questo caso), la associamo alla
      # colonna, impostiamo le proprieta'
      cell = gtk.CellRendererPixbuf ()
      column = gtk.TreeViewColumn ("Foto")
      column.pack_start (cell)
      column.set_attributes (cell, pixbuf = COL_FOTO)
      self.treeview.append_column (column)

      cell = gtk.CellRendererText ()
      # E' possibile usare questo codice piu' compatto per definire le
      # proprieta' di una cella e associarla alla colonna in un'unica
      # istruzione
      column = gtk.TreeViewColumn ("Nome", cell, text = COL_NOME)
      column.set_cell_data_func (cell, self.__cell_data_func, None)
      column.set_resizable (True)
      column.set_sort_column_id(COL_NOME)
      cell.set_property('editable', True)
      cell.connect('edited', self.edited_callback, (self.model, COL_NOME))
      self.treeview.append_column (column)

      cell = gtk.CellRendererText ()
      column = gtk.TreeViewColumn ("Cognome", cell, text = COL_COGNOME)
      column.set_resizable (True)
      column.set_sort_column_id(COL_COGNOME)
      cell.set_property('editable', True)
      cell.connect('edited', self.edited_callback, (self.model, COL_COGNOME))
      self.treeview.append_column (column)

      cell = gtk.CellRendererToggle ()
      column = gtk.TreeViewColumn ("Attivo", cell, active = COL_ATTIVO)
      self.treeview.append_column (column)

      self.mainwindow.show_all ()


   def button_close_clicked (self, widget, data=None):
      gtk.main_quit ()
      
   def button_addrow_clicked (self, widget, data=None):
      from random import Random
      rnd = Random ()

      # Dati per la nuova riga
      attivo = rnd.randint (0, 1)
      foto = gtk.gdk.pixbuf_new_from_file('foto.jpg')
      newrow = ['Tarapia', 'Tapioco', attivo, None, foto]

      # Se c'e` una riga selezionata, inseriamo la nuova riga
      # dopo quella selezionata, altrimenti la aggiungiamo
      # per ultima
      selection = self.treeview.get_selection ()
      model, iter = selection.get_selected ()
      if iter:
	      newiter = model.insert_after (iter, newrow)
      else:
	      newiter = self.model.append (newrow)
      
      # selezioniamo la riga appena aggiunta
      selection.select_iter (newiter)
      
   def button_deleterow_clicked (self, widget, data=None):
      # Se c'e` una riga selezionata, la eliminiamo
      selection = self.treeview.get_selection ()
      model, iter = selection.get_selected ()
      if iter:
         model.remove (iter)

   def mainwindow_delete_event (self, widget, data=None):
      gtk.main_quit ()
 
   def run (self):
      gtk.main ()

if __name__ == '__main__':
   sample = GtkTreeViewTutorialSample ()
   sample.run ()
