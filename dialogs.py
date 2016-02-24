__author__ = 'Jan Bogaerts'
__copyright__ = "Copyright 2016, AllThingsTalk"
__credits__ = []
__maintainer__ = "Jan Bogaerts"
__email__ = "jb@allthingstalk.com"
__status__ = "Prototype"  # "Development", or "Production"

from kivy.uix.popup import Popup
from kivy.properties import NumericProperty, StringProperty, ObjectProperty
from kivy.uix.dropdown import DropDown
from kivy.uix.togglebutton import  ToggleButton
from kivy.uix.treeview import TreeViewNode, TreeViewLabel
import os
import sys
import copy

from genericwidgets import *
import styleManager as sm
import attiotuserclient as iot

class GroupDialog(Popup):
    "edit groups"
    group_title = StringProperty('')
    icon = StringProperty('')
    iconInput = ObjectProperty()
    titleInput = ObjectProperty()

    def __init__(self, data, **kwargs):
        self.callback = None
        self.data = data
        super(GroupDialog, self).__init__(**kwargs)

    def selectImage(self):
        runpath = os.path.dirname(os.path.realpath(sys.argv[0]))
        dlg = SelectImageDialog(self.selectImageDone, runpath)
        dlg.open()

    def selectImageDone(self, fileName):
        self.icon = fileName

    def done(self):
        self.data.title = self.titleInput.text
        self.data.icon = self.icon

        if self.callback:
            self.callback(self.data)

        self.dismiss()


class SectionDialog(Popup):
    "edit groups"
    titleInput = ObjectProperty()

    def __init__(self, data, **kwargs):
        self.callback = None
        self.data = data
        super(SectionDialog, self).__init__(**kwargs)
        self.titleInput.text = data.title

    def done(self):
        self.data.title = self.titleInput.text

        if self.callback:
            self.callback(self.data)

        self.dismiss()


class TreeViewButton(ToggleButton, TreeViewNode):
    pass

class AssetDialog(Popup):
    "edit groups"
    assetInput = ObjectProperty()
    labelInput = ObjectProperty()
    assetLabel = StringProperty('')
    selectedSkinExample = StringProperty('')
    currentSize = NumericProperty(1)


    def __init__(self, data, **kwargs):
        self.callback = None
        self.data = data
        self.tempData = copy.copy(data)             # make a shallow copy of the data object which we will be using to edit. It can load stuff
        self.assetLabel = data.title
        self.parentW = None  # for new items
        super(AssetDialog, self).__init__(**kwargs)

    def populateTreeView(self):
        """renders the root grounds in the treeview."""

    def populateTreeNode(self, treeview, node):
        if not node:
            grounds = iot.getGrounds(True)
            for ground in grounds:
                result = TreeViewLabel(text=ground['title'],is_open=False, is_leaf=False)
                result.ground_id=ground['id']
                yield result
        elif hasattr(node, 'ground_id'):
            devices = iot.getDevices(node.ground_id)
            for device in devices:
                result = TreeViewLabel(is_open=False, is_leaf=False)
                result.device_id = device['id']
                if device['title']:
                    result.text=device['title']             # for old devices that didn't ahve a title yet.
                else:
                    result.text=device['name']
                yield result
        elif hasattr(node, 'device_id'):
            assets = iot.getAssets(node.device_id)
            for asset in assets:
                result = TreeViewLabel(is_open=False, is_leaf=True)
                result.asset_id = asset['id']
                if asset['title']:
                    result.text=asset['title']             # for old devices that didn't ahve a title yet.
                else:
                    result.text=asset['name']
                yield result
                if self.tempData.id == asset['id']:
                    treeview.select_node(result)


    def on_assetChanged(self, id):
        if id:
            self.tempData.id = id.asset_id
            self.tempData.isLoaded = False
            self.tempData.load(False)
            self.assetLabel = self.tempData.title
            if self.tempData.skin:
                self.selectedSkinExample = self.tempData.skin['Example']

    def showStylesDropDown(self, relativeTo):
        """show a drop down box with all the available style images"""
        if self.tempData.control:
            dropdown = DropDown(auto_width=False, width='140dp')
            skins = sm.getAvailableSkins(self.tempData.control.controlType)
            for skin in skins:
                btn = ImageButton(source=skin['example'],  size_hint_y=None, height=44)
                btn.skin = skin
                btn.bind(on_release=lambda btn: self.setSkin(btn.skin))
                dropdown.add_widget(btn)
            dropdown.open(relativeTo)

    def setSkin(self, skin):
        """set the skin"""
        self.selectedSkinExample = skin

    def setSize(self, size):
        """set the size of the control"""

    def done(self):
        self.data.id = self.assetInput.text

        if self.callback:
            self.callback(self.parentW, self.data)

        self.dismiss()


class NewLayoutPopup(Popup):
    """text input"""
    nameInput = ObjectProperty()

    def __init__(self, main,  **kwargs):
        self.main = main
        self.parentW = None  # for new items
        super(NewLayoutPopup, self).__init__(**kwargs)
        self.nameInput.text = "new layout"

    def done(self):
        self.dismiss()
        self.main.newLayoutDone(self.nameInput.text)


class CredentialsDialog(Popup):
    "set credentials"
    userNameInput = ObjectProperty()
    pwdInput = ObjectProperty()

    serverInput = ObjectProperty()
    brokerInput = ObjectProperty()

    def __init__(self, main, forNewLayout, **kwargs):
        self.main = main
        self.isNew = forNewLayout
        super(CredentialsDialog, self).__init__(**kwargs)
        self.userNameInput.text = main.data.userName
        self.pwdInput.text = main.data.password
        if main.data.server:
            self.serverInput.text = main.data.server
        else:
            self.serverInput.text = 'api.smartliving.io'
        if main.data.broker:
            self.brokerInput.text = main.data.broker
        else:
            self.brokerInput.text = 'broker.smartliving.io'



    def dismissOk(self):
        self.dismiss()
        self.main.data.userName = self.userNameInput.text
        self.main.data.password = self.pwdInput.text
        self.main.data.server = self.serverInput.text
        self.main.data.broker = self.brokerInput.text

        self.main.setCredentialsDone(self.isNew)


class LoadDialog(Popup):
    def load(self, path, file):
        file = os.path.join(path, file[0])      # the load dialgo returns a list of selected files
        self.dismiss()
        self.main.openLayoutDone(file)

    def cancel(self):
        self.dismiss()

class SelectImageDialog(Popup):
    '''select an image. Use the callback function to get the result '''
    def __init__(self, callback, path, **kwargs):
        self.callback = callback
        self.path = path
        super(SelectImageDialog, self).__init__(**kwargs)

    def load(self, path, file):
        file = os.path.join(path, file[0])      # the load dialgo returns a list of selected files
        file = file.replace('\\', '/')          # make certain that paths with \ are replaced with / -> otherwise json wont load correctly.
        self.dismiss()
        self.callback(file)

    def cancel(self):
        self.dismiss()