__author__ = 'Jan Bogaerts'
__copyright__ = "Copyright 2016, AllThingsTalk"
__credits__ = []
__maintainer__ = "Jan Bogaerts"
__email__ = "jb@allthingstalk.com"
__status__ = "Prototype"  # "Development", or "Production"


import kivy
kivy.require('1.9.1')   # replace with your current kivy version !

import logging
logging.getLogger().setLevel(logging.INFO)

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
import kivy.metrics
import iconfonts
from ConfigParser import *
import os

try:
    from jnius import autoclass  # SDcard Android
except:
    logging.exception('failed to load andreoid specific libs')

import dialogs
import layout
import attiotuserclient as IOT
import styleManager as sm
from layoutwidgets import *
from errors import *
import data as dt


class MainWindow(Widget):
    menu = ObjectProperty(None)
    workspace = ObjectProperty(None)
    rootLayout = ObjectProperty(None)
    selectedGroup = None

    def __init__(self, **kwargs):
        self.isEditing = False
        self.selectedItems = set([])
        self.editActionBar = None
        self.sectionWidth = 0.33                                    #default value, assigned to all new sections that get created.
        Window.softinput_mode = 'below_target'                            # so the screen resizes when the keybaord is shown, otherwise it hides editing.
        super(MainWindow, self).__init__(**kwargs)



    def on_width(self, instance, width):
        #showErrorMsg("width: " + str(width) + ", dpi: " + str(kivy.metrics.metrics.dpi) + ", inch: " + str(width / kivy.metrics.metrics.dpi) + ", rounded: " + str(kivy.metrics.metrics.dpi_rounded) + ", density: " +str(kivy.metrics.metrics.density) )
        width = width / kivy.metrics.metrics.density  #kivy.metrics.metrics.dpi
        if width < 500:
            self.sectionWidth = 1
        elif width < 900:
            self.sectionWidth = 0.5
        else:
            self.sectionWidth = 0.33
        if self.selectedGroup:                                      # we can only add a new section if there is a group selected.
            for section in self.workspace.children:
                section.sectionWidth = self.sectionWidth

    def load(self, fileName):
        global data
        connectError = False
        try:
            dt.fileName = fileName
            dt.data = layout.Layout()
            self.data = dt.data                                                # small hack so that other modules can reach data without hassle.
            if os.path.isfile(fileName):                                    # could be that it's a new file (first startup) -> default layout gets a default filename
                dt.data.load(fileName)
            if dt.data.userName and dt.data.password and dt.data.server and dt.data.broker:
                try:
                    IOT.connect(dt.data.userName, dt.data.password, dt.data.server, dt.data.broker)
                except Exception as e:
                    connectError = True
                    showError(e, None,  "Failed to connect to the internet, please check your network settings. ")
                    raise                                                   # raise the exception again, we don't want the menu to load, cause it will fail
                self.loadMenu()                                             #must be done after connecting, cause it might have to load assets
            else:
                self.loadMenu()                                             #must be done before editLayout (for new layouts)
                self.editLayout(None)                                   # there is no connection yet, automatically go to edit mode. Also helps with the button.
        except Exception as e:
            if not connectError:
                showError(e)

    def loadMenu(self):
        self.menu.clear_widgets()           #clear any possible previous widgets
        for group in dt.data.groups:
            self.addGroup(group)
        filler = Widget()               # for filling the empty space at the end.
        self.menu.add_widget(filler)


    def addGroup(self, group, index = 0):
        """add a group to the menu.
        returns the newly created item"""
        item = GroupMenuItem(group)
        self.menu.add_widget(item, index)
        if group.isSelected:
            self.selectedGroup = item
            self.loadSections()
            item.showSelectionBox(True)
        return item

    def newGroup(self, obj, value):
        """create a new group"""
        group = layout.Group(dt.data)
        group.isSelected = False
        dlg = dialogs.GroupDialog(group, title='new group')
        dlg.data = group
        dlg.group_title = group.title
        dlg.caller = self
        dlg.callback = self.onNewGroupDone
        dlg.open()

    def onNewGroupDone(self, group):
        if not group.title:
            group.title = "new group"
        menuItem = self.addGroup(group, 1)
        self.setSelectedGroup(menuItem)
        dt.data.groups.append(group)
        if self.isEditing:
            self.addEditTo(menuItem, 20)

    def editGroup(self, group):
        """show a dialog so the user can edit the group"""
        dlg = dialogs.GroupDialog(group, title='edit group')
        dlg.group_title = group.title
        dlg.icon = group.icon
        dlg.open()


    def showMainDropDown(self, attachTo):
        dropdown = DropDown(auto_width=False, width='140dp')

        btn = Button(text='%s New' % iconfonts.icon('fa-file-o'), markup=True, size_hint_y=None, height='44dp')
        btn.bind(on_release=lambda btn: self.newLayout(btn.parent.parent))
        dropdown.add_widget(btn)

        btn = Button(text='%s Edit' % iconfonts.icon('fa-edit'), markup=True, size_hint_y=None, height='44dp')
        btn.bind(on_release=lambda btn: self.editLayout(btn.parent.parent))
        dropdown.add_widget(btn)

        btn = Button(text='%s Credentials' % iconfonts.icon('fa-user'), markup=True, size_hint_y=None, height='44dp')
        btn.bind(on_release=lambda btn: self.editCredentials(btn.parent.parent))
        dropdown.add_widget(btn)

        btn = Button(text='%s Open' % iconfonts.icon('fa-folder-open-o'), markup=True, size_hint_y=None, height='44dp')
        btn.bind(on_release=lambda btn: self.openLayout(btn.parent.parent))
        dropdown.add_widget(btn)

        dropdown.open(attachTo)

    def newSection(self, obj, value):
        """create a new group"""
        section = layout.Section(self.selectedGroup.data)
        dlg = dialogs.SectionDialog(section, title='new section')
        dlg.data = section
        dlg.callback = self.onNewSectionDone
        dlg.open()

    def onNewSectionDone(self, section):
        sectionW = SectionWidget(section, sectionWidth = self.sectionWidth)
        self.workspace.add_widget(sectionW, 1)

        self.selectedGroup.data.sections.append(section)
        if self.isEditing:
            self.addEditTo(sectionW, 30)
            self.addAddTo(sectionW.assets, self.newAsset, sectionW)

    def editSection(self, section):
        """show a dialog so the user can edit the group"""
        dlg = dialogs.SectionDialog(section, title='edit section')
        dlg.open()





    def newAsset(self, obj, value):
        """create a new group"""
        asset = layout.Asset(obj.section.data, "")
        dlg = dialogs.AssetDialog(asset, title='new asset')
        dlg.data = asset
        dlg.parentW = obj.section                    #keep ref of parent widget, so we can later on add the asstet widget to the correct section.
        dlg.callback = self.onNewAssetDone
        dlg.open()

    def onNewAssetDone(self, parentW, asset):
        parentW.data.assets.append(asset)
        assetW = self.addAssetToSection(asset, parentW)
        if self.isEditing:
            self.addEditTo(assetW, 20)

    def editAsset(self, asset, widget):
        """show a dialog so the user can edit the group"""
        dlg = dialogs.AssetDialog(asset, title='edit asset')
        dlg.parentW = widget
        dlg.callback = self.onEditAssetDone
        dlg.open()

    def onEditAssetDone(self, parentW, asset):
        if asset.control:
            uiEl = asset.control.getUI()
        else:
            uiEl = InvalidControlWidget()
        parentW.control_container.remove_widget(parentW.control_container.children[0]) # remove the old widget, addd the new one
        parentW.control_container.add_widget(uiEl)

    def addAssetToSection(self, asset, sectionW):
        assetW = AssetWidget(asset)
        if self.isEditing:
            sectionW.assets.add_widget(assetW, 1)
        else:
            sectionW.assets.add_widget(assetW)
        if asset.control:
            uiEl = asset.control.getUI()
        else:
            uiEl = InvalidControlWidget()

        assetW.control_container.add_widget(uiEl)
        return assetW

    def setSelectedGroup(self, group):
        """switch selected group and render the content"""
        if self.selectedGroup:
            self.selectedGroup.toggleSelected()
        self.selectedGroup = group
        if self.selectedGroup:
            self.selectedGroup.toggleSelected()
            self.loadSections()
        else:
            self.workspace.clear_widgets()              # no group, then workspace is completely empty

    def loadSections(self):
        """loads the sections of the currently selected group in the workspace"""
        self.workspace.clear_widgets()
        self.selectedItems.clear()                                  # not yet supported to remember selection after page switch
        if self.selectedGroup:
            for section in self.selectedGroup.data.sections:
                sectionW = SectionWidget(section)
                sectionW.sectionWidth = self.sectionWidth
                self.workspace.add_widget(sectionW)
                toRemove = []
                for asset in section.assets:
                    try:
                        if asset.isLoaded == False:
                            asset.load()
                        self.addAssetToSection(asset, sectionW)
                    except Exception as e:
                        toRemove.append(asset)
                        showError(e, ", removing asset from dashboard")
                for item in toRemove: section.assets.remove(item)
            if self.isEditing:
                self.editWorkSpace()

    def _clearUI(self):
        """clears out the current ui elements"""
        self.menu.clear_widgets()
        self.workspace.clear_widgets()

    def reset(self):
        if self.isEditing:
            self.endEdit()
        dt.save()                     # first save the current layout, so we don't loose current data
        self._clearUI()
        IOT.disconnect(False)           # new layout, so close connection to previous

    def newLayout(self, popup):
        """create a new layout"""
        try:
            if popup:
                popup.dismiss()

            dlg = dialogs.NewLayoutPopup(self, title="Name of new layout")
            dlg.dataPath = Application.get_dataPath()
            dlg.open(self)
        except Exception as e:
            showError(e)

    def newLayoutDone(self, name):
        self.reset()
        dt.data = layout.Layout()
        dt.data.title = self.title = os.path.splitext(os.path.basename(name))[0]
        filler = Widget()               # for filling the empty space at the end.
        self.menu.add_widget(filler)
        dt.fileName = name            # path and extension were already added by the dialog, so it can check for file existance.
        self.selectedItems.clear()
        self.selectedGroup = None           # no groups, so there can be none seleced.
        self.editLayout(None)

    def addSetCredentialsBtnNew(self):
        btn = Button()
        btn.text = "click here to set you account credentials."
        btn.halign = 'center'
        btn.valign = 'middle'
        btn.size_hint = (None, None)
        btn.width = '200dp'
        btn.height = '100dp'
        btn.text_size = btn.size
        btn.bind(on_press=self.setCredentialsNew)
        self.workspace.add_widget(btn)

    def setCredentialsNew(self, sender):
        """set the credentials for a new layout (first time credentials are set)"""
        dlg = dialogs.CredentialsDialog(self, True)
        dlg.open(self)

    def editCredentials(self, popup):
        """set the credentials for a new layout (first time credentials are set)"""
        try:
            if popup:
                popup.dismiss()
            dlg = dialogs.CredentialsDialog(self, False)
            dlg.open(self)
        except Exception as e:
            showError(e)

    def setCredentialsDone(self, forNewLayout):
        try:
            if not forNewLayout:                                    # if we were already connected, reconnect.
                IOT.disconnect(False)
            IOT.connect(dt.data.userName, dt.data.password, dt.data.server, dt.data.broker)     # connect with the new credentials
            if forNewLayout:                                        # if it was a new layout, there was a button on the workspace to set the credentials, this can be removed now.
                self.workspace.remove_widget(self.workspace.children[0])
        except Exception as e:
            showError(e)


    def addEditTo(self, addTo, offset):
        edit = EditButton()
        edit.offset = offset
        edit.reposition(addTo, None)
        addTo.bind(size=edit.reposition, pos=edit.reposition)
        edit.bind(state=self.toggleEdit)
        addTo.add_widget(edit)

    def toggleEdit(self, instance, value):
        if value == 'down':
            instance.text = '[size=25]%s[/size]'%(iconfonts.icon('fa-check-square-o'))
            self.selectedItems.add(instance)
        else:
            instance.text = '[size=25]%s[/size]'%(iconfonts.icon('fa-square-o'))
            self.selectedItems.remove(instance)

    def addAddTo(self, addTo ,callback = None, section = None):
        add = EditButton()
        add.text = '[size=30]%s[/size]'%(iconfonts.icon('fa-plus'))
        addTo.add_widget(add)
        if section:
            add.section = section       #provide ref to section which will become the parent of the asset
        if callback:
            add.bind(state=callback)

    def editLayout(self, popup):
        """start editing the current layout"""
        try:
            if popup:
                popup.dismiss()
            if not self.isEditing:                                              # don't edit again if already editing.
                self.isEditing = True
                self.editActionBar = EditActionBar()                            # add this before any selectionbox, otherewise they are located incorrectly
                self.editActionBar.title = self.data.title
                self.rootLayout.add_widget(self.editActionBar, len(self.rootLayout.children))
                for group in self.menu.children:
                    edit = EditButton()
                    if not group == self.menu.children[0]:
                        edit.x = group.x + group.width - kivy.metrics.dp(20)
                        edit.bind(state=self.toggleEdit)
                        group.bind(size=edit.reposition, pos=edit.reposition)
                    else:
                        edit.text = '[size=30]%s[/size]'%(iconfonts.icon('fa-plus'))
                        edit.x = group.x
                        edit.bind(state=self.newGroup)
                        group.bind(size=edit.repositionAdd, pos=edit.repositionAdd)
                    edit.y = group.y + group.height - kivy.metrics.dp(20)
                    group.add_widget(edit)
                self.editWorkSpace()
        except Exception as e:
            showError(e)

    def editWorkSpace(self):
        if self.selectedGroup:                                      # we can only add a new section if there is a group selected.
            for section in self.workspace.children:
                self.addEditTo(section, 30)
                if hasattr(section, 'assets'):
                    for asset in section.assets.children:
                        self.addEditTo(asset, 20)
                    self.addAddTo(section.assets, self.newAsset, section)
            self.addAddTo(self.workspace, self.newSection)
        if not (dt.data.userName and dt.data.password and dt.data.server and dt.data.broker):
            self.addSetCredentialsBtnNew()

    def endEdit(self):
        """stop the current edit session, remove all the edit and add widgets"""
        self.isEditing = False
        self.rootLayout.remove_widget(self.editActionBar)       # do this first, so that location of the rest is faster/correcter
        self.loadMenu()                 #reload the menu to remove the selection boxes
        self.loadSections()             #reloading the sections will first clear out all the old stuff
        self.editActionBar = None

    def editSelected(self):
        """for each selected item, show an editor"""
        for selected in self.selectedItems:
            parent = selected.parent
            if type(parent) == GroupMenuItem:
                self.editGroup(parent.data)
            elif type(parent) == SectionWidget:
                self.editSection(parent.data)
            elif type(parent) == AssetWidget:
                self.editAsset(parent.data, parent)


    def deleteSelected(self):
        """delete all the selected items"""
        for item in self.selectedItems:
            parent = item.parent
            if type(parent)  in [AssetWidget, GroupMenuItem, SectionWidget]:
                if self.selectedGroup == item:              # if we are removing the currently selected group, switch to another group , if tere is still one, otherwise we go to null.
                    if len(parent.parent.children) > 0:
                        self.setSelectedGroup(parent.parent.children[-1])
                    else:
                        self.setSelectedGroup(None)
                parent.data.delete()                    #delete the data.
                parent.parent.remove_widget(parent)
        self.selectedItems.clear()



    def openLayout(self, popup):
        """show the open dialog box"""
        try:
            if popup:
                popup.dismiss()
            dlg = dialogs.LoadDialog()
            dlg.main = self
            dlg.open()
        except Exception as e:
            showError(e)

    def openLayoutDone(self, fileToOpen):
        if fileToOpen:
            self.reset()
            self.load(fileToOpen)

appConfigFileName = 'app.config'



server = 'none'
broker = None

class attDashApp(App):

    def __init__(self, **kwargs):
        self._main = None
        super(attDashApp, self).__init__(**kwargs)

    def build(self):
        if not os.path.isdir(self.get_dataPath()):          # make certain taht the dir exists to save layout-boards.
            os.makedirs(self.get_dataPath())
        self._main = MainWindow()
        dt.config = ConfigParser()
        if dt.config.read(appConfigFileName) and dt.config.has_option('general', 'layout'):
            fileName = dt.config.get('general', 'layout')
        else:
            fileName = os.path.join(Application.get_dataPath(), 'default.board')
        self._main.load(fileName)
        return self._main

    def saveState(self, recoverable):
        try:
            dt.save()                           # save the current state, so we can restore
            if not dt.config.has_section('general'):
                dt.config.add_section('general')
            dt.config.set('general', 'layout', dt.fileName)
            with open(appConfigFileName, 'w') as f:
                dt.config.write(f)
            IOT.disconnect(recoverable)                        # close network connection, for cleanup
        except:
            logging.exception('failed to save application state')

    def on_pause(self):                         # can get called multiple times, sometimes no memory objects are set
        self.saveState(True)
        return True

    def on_resume(self):
        try:
            if dt.data:                            # can get called multiple times, sometimes no memory objects are set
                IOT.reconnect(dt.data.server, dt.data.broker)
                logging.info("reconnected after resume")
        except Exception as e:
            showError(e, ": Failed to reconnect network, please check your network settings.")

    def on_stop(self):
        self.saveState(False)


    def get_dataPath(self):
        try:
            Environment = autoclass('android.os.Environment')
            return os.path.join(Environment.get_running_app().getExternalStorageDirectory(), 'boards')

        # Not on Android
        except:
            return os.path.join(self.user_data_dir, 'boards')

iconfonts.register('default_font', 'iconfonts/fontawesome-webfont.ttf', 'iconfonts/font-awesome.fontd')

Application = attDashApp()

if __name__ == '__main__':
    sm.loadSkins('skins')
    Application.run()