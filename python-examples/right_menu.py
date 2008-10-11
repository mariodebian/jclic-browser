# right_menu

print "menu loaded"

def right_menu(self):
        print "exec menu"
        menu_ui = """
            <ui>
                <popup name="SongMenu">
                  <menuitem action="Play"/>
                  <menuitem action="Queue"/>
                  <menuitem action="Edit"/>
                  <menuitem action="Remove"/>
                </popup>
            </ui>
            """

        self.uimanager = gtk.UIManager()
        self.uimanager.add_ui_from_string(menu_ui)
        accelgroup = self.uimanager.get_accel_group()
        actiongroup = gtk.ActionGroup('Listen')
        actiongroup.add_actions([('Play', gtk.STOCK_MEDIA_PLAY, _('_Play'), None,
                                         _('Play this song'), self.play_selected)])
        actiongroup.add_actions([('Queue', gtk.STOCK_ADD, _('_Queue'), None,
                                         _('Queue this song'), self.enqueue_selected)])
        actiongroup.add_actions([('Edit', gtk.STOCK_EDIT, _('_Edit'), None,
                                         _('Edit this song'), self.edit_selected)])


        actiongroup.add_actions([('Remove', gtk.STOCK_DELETE, _('_Remove'), None,
                          _('Remove this song'), self.remove_selected)])

        self.uimanager.insert_action_group(actiongroup, 1)
        #gobject.idle_add(self.get_toplevel().add_accel_group,accelgroup)

        return self.uimanager.get_widget("/SongMenu")
        
def on_button_press_event(self):
        if event.button == 3 :
            self.menu.popup(None,None,None,event.button,event.time)

        

