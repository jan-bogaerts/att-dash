__author__ = 'Jan Bogaerts'
__copyright__ = "Copyright 2016, AllThingsTalk"
__credits__ = []
__maintainer__ = "Jan Bogaerts"
__email__ = "jb@allthingstalk.com"
__status__ = "Prototype"  # "Development", or "Production"


import kivy
kivy.require('1.9.1')   # replace with your current kivy version !

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
import iconfonts
from ConfigParser import *
import os

from dialogs import *
import layout
import attiotuserclient as IOT
from layoutwidgets import *
from errors import *

class MainWindow(Widget):
    menu = ObjectProperty(None)
    workspace = ObjectProperty(None)
    rootLayout = ObjectProperty(None)
    data = None
    selectedGroup = None
    #mainMenu = DropDown()           # for some reason, we need this. If it is removed, the dropdown menu defined in kv no longer works and gives an error

    def __init__(self, **kwargs):
        self.fileName = None
        self.isEditing = False
        self.selectedItems = set([])
        self.editActionBar = None
        super(MainWindow, self).__init__(**kwargs)

    def load(self, fileName):
        try:
            self.fileName = fileName
            self.data = layout.Layout()
            self.data.load(fileName)
            if self.data.userName and self.data.password and self.data.server and self.data.broker:
                IOT.connect(self.data.userName, self.data.password, self.data.server, self.data.broker)
                self.loadMenu()                                             #must be done after connecting, cause it might have to load assets
            else:
                self.loadMenu()                                             #must be done before editLayout (for new layouts)
                self.editLayout(None)                                   # there is no connection yet, automatically go to edit mode. Also helps with the button.
        except Exception as e:
            showError(e)

    def loadMenu(self):
        self.menu.clear_widgets()           #clear any possible previous widgets
        for group in self.data.groups:
            self.addGroup(group)
        filler = Widget()               # for filling the empty space at the end.
        self.menu.add_widget(filler)

    def save(self):
        if self.data:
            self.data.save(self.fileName)

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
        group = layout.Group(self.data)
        group.isSelected = False
        group.title = "new group"
        dlg = GroupDialog(group, title='new group')
        dlg.data = group
        dlg.group_title = group.title
        dlg.caller = self
        dlg.callback = self.onNewGroupDone
        dlg.open()

    def onNewGroupDone(self, group):
        menuItem = self.addGroup(group, 1)
        self.setSelectedGroup(menuItem)
        self.data.groups.append(group)
        if self.isEditing:
            self.addEditTo(menuItem, 20)

    def editGroup(self, group):
        """show a dialog so the user can edit the group"""
        dlg = GroupDialog(group, title='edit group')
        dlg.group_title = group.title
        dlg.icon = group.icon
        dlg.open()


    def showMainDropDown(self, attachTo):
        dropdown = DropDown(auto_width=False, width='140dp')

        btn = Button(text='%s New' % iconfonts.icon('fa-file-o'), markup=True, size_hint_y=None, height=44)
        btn.bind(on_release=lambda btn: self.newLayout(btn.parent.parent))
        dropdown.add_widget(btn)

        btn = Button(text='%s Edit' % iconfonts.icon('fa-edit'), markup=True, size_hint_y=None, height=44)
        btn.bind(on_release=lambda btn: self.editLayout(btn.parent.parent))
        dropdown.add_widget(btn)

        btn = Button(text='%s Credentials' % iconfonts.icon('fa-user'), markup=True, size_hint_y=None, height=44)
        btn.bind(on_release=lambda btn: self.editCredentials(btn.parent.parent))
        dropdown.add_widget(btn)

        btn = Button(text='%s Open' % iconfonts.icon('fa-folder-open-o'), markup=True, size_hint_y=None, height=44)
        btn.bind(on_release=lambda btn: self.openLayout(btn.parent.parent))
        dropdown.add_widget(btn)

        dropdown.open(attachTo)

    def newSection(self, obj, value):
        """create a new group"""
        section = layout.Section(self.selectedGroup.data)
        dlg = SectionDialog(section, title='new section')
        dlg.data = section
        dlg.callback = self.onNewSectionDone
        dlg.open()

    def onNewSectionDone(self, section):
        sectionW = SectionWidget(section)
        self.workspace.add_widget(sectionW, 1)

        self.selectedGroup.data.sections.append(section)
        if self.isEditing:
            self.addEditTo(sectionW, 30)
            self.addAddTo(sectionW.assets, self.newAsset, sectionW)

    def editSection(self, section):
        """show a dialog so the user can edit the group"""
        dlg = SectionDialog(section, title='edit section')
        dlg.open()





    def newAsset(self, obj, value):
        """create a new group"""
        asset = layout.Asset(obj.section.data, "")
        dlg = AssetDialog(asset, title='new asset')
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
        dlg = AssetDialog(asset, title='edit asset')
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
                self.workspace.add_widget(sectionW)
                for asset in section.assets:
                    if asset.isLoaded == False:
                        asset.load()
                    self.addAssetToSection(asset, sectionW)
            if self.isEditing:
                self.editWorkSpace()

    def _clearUI(self):
        """clears out the current ui elements"""
        self.menu.clear_widgets()
        self.workspace.clear_widgets()

    def reset(self):
        if self.isEditing:
            self.endEdit()
        self.save()                     # first save the current layout, so we don't loose current data
        self._clearUI()
        IOT.disconnect(False)           # new layout, so close connection to previous

    def newLayout(self, popup):
        """create a new layout"""
        try:
            self.reset()
            self.data = layout.Layout()
            filler = Widget()               # for filling the empty space at the end.
            self.menu.add_widget(filler)
            if popup:
                popup.dismiss()

            dlg = NewLayoutPopup(self, title="Name of new layout")
            dlg.open(self)
        except Exception as e:
            showError(e)

    def newLayoutDone(self, name):
        self.fileName = os.path.join(Application.user_data_dir, name + '.board')     # add the path and extension.
        self.selectedItems.clear()
        self.selectedGroup = None           # no groups, so there can be none seleced.
        self.editLayout(None)

    def addSetCredentialsBtnNew(self):
        btn = Button()
        btn.text = "click here to set you account credentials."
        btn.halign = 'center'
        btn.valign = 'middle'
        btn.size_hint = (None, None)
        btn.width = 200
        btn.height = 100
        btn.text_size = btn.size
        btn.bind(on_press=self.setCredentialsNew)
        self.workspace.add_widget(btn)

    def setCredentialsNew(self, sender):
        """set the credentials for a new layout (first time credentials are set)"""
        dlg = CredentialsDialog(self, True)
        dlg.open(self)

    def editCredentials(self, popup):
        """set the credentials for a new layout (first time credentials are set)"""
        try:
            if popup:
                popup.dismiss()
            dlg = CredentialsDialog(self, False)
            dlg.open(self)
        except Exception as e:
            showError(e)

    def setCredentialsDone(self, forNewLayout):
        try:
            if not forNewLayout:                                    # if we were already connected, reconnect.
                IOT.disconnect(False)
            IOT.connect(self.data.userName, self.data.password, self.data.server, self.data.broker)     # connect with the new credentials
            if forNewLayout:                                        # if it was a new layout, there was a button on the workspace to set the credentials, this can be removed now.
                self.workspace.clear_widgets()
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
            instance.text = '%s'%(iconfonts.icon('fa-check-square-o'))
            self.selectedItems.add(instance)
        else:
            instance.text = '%s'%(iconfonts.icon('fa-square-o'))
            self.selectedItems.remove(instance)

    def addAddTo(self, addTo ,callback = None, section = None):
        add = EditButton()
        add.text = '%s'%(iconfonts.icon('fa-plus'))
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
                self.rootLayout.add_widget(self.editActionBar, len(self.rootLayout.children))
                for group in self.menu.children:
                    edit = EditButton()
                    if not group == self.menu.children[0]:
                        edit.x = group.x + group.width - 20
                        edit.bind(state=self.toggleEdit)
                        group.bind(size=edit.reposition, pos=edit.reposition)
                    else:
                        edit.text = '%s'%(iconfonts.icon('fa-plus'))
                        edit.x = group.x
                        edit.bind(state=self.newGroup)
                        group.bind(size=edit.repositionAdd, pos=edit.repositionAdd)
                    edit.y = group.y + group.height - 20
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
        if not (self.data.userName and self.data.password and self.data.server and self.data.broker):
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



    def openLayout(self, popup):
        """show the open dialog box"""
        try:
            if popup:
                popup.dismiss()
            dlg = LoadDialog()
            dlg.main = self
            dlg.open()
        except Exception as e:
            showError(e)

    def openLayoutDone(self, fileToOpen):
        if fileToOpen:
            self.reset()
            self.load(fileToOpen)

appConfigFileName = 'app.config'

class attDashApp(App):
    _main = None
    _config = None
    def build(self):
        self._main = MainWindow()
        self._config = ConfigParser()
        if self._config.read(appConfigFileName) and self._config.has_option('general', 'layout'):
            fileName = self._config.get('general', 'layout')
        else:
            fileName = "layout.json"
        self._main.load(fileName)
        return self._main

    def on_pause(self):
        self._main.save()                           # save the current state, in case that the application gets fully closed.
        IOT.disconnect(True)                        # close network connection, we have to re-open it when the app becomes active, anyway. Also this saves resources on the system.
        return True

    def on_resume(self):
        try:
            IOT.reconnect(self._main.data.server, self._main.data.broker)
        except Exception as e:
            showError(e)

    def on_stop(self):
        self._main.save()                           # save the current state, so we can restore
        if not self._config.has_section('general'):
            self._config.add_section('general')
        self._config.set('general', 'layout', self._main.fileName)
        with open(appConfigFileName, 'w') as f:
            self._config.write(f)
        IOT.disconnect(False)                        # close network connection, for cleanup


iconfonts.register('default_font', 'iconfonts/fontawesome-webfont.ttf', 'iconfonts/font-awesome.fontd')

Application = attDashApp()

if __name__ == '__main__':
    sm.loadSkins('skins')
    Application.run()