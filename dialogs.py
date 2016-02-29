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
from kivy.uix.button import Button
from kivy.uix.treeview import TreeView, TreeViewNode, TreeViewLabel
from kivy.uix.scrollview import ScrollView
import os
import sys
import copy

from genericwidgets import *
import styleManager as sm
import attiotuserclient as iot
from errors import *

class GroupDialog(Popup):
    "edit groups"
    group_title = StringProperty('')
    icon = StringProperty('None')
    iconInput = ObjectProperty()
    titleInput = ObjectProperty()

    def __init__(self, data, **kwargs):
        self.callback = None
        self.data = data
        super(GroupDialog, self).__init__(**kwargs)

    def selectImage(self):
        runpath = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'images')
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
    #assetInput = ObjectProperty()
    assetName = StringProperty("Click here to select the asset")
    labelInput = ObjectProperty()
    assetLabel = StringProperty('')
    selectedSkinExample = ObjectProperty('')
    currentSize = NumericProperty(1)
    mainLayout = ObjectProperty()               # provides a reference to the layout that contains the editing objects, used to add/remove the skin specific editors


    def __init__(self, data, **kwargs):
        self.callback = None
        self.skinPropertyControls = None            # keep a reference to the controls that were added for editing the skin specific properties
        self.data = data
        self.tempData = copy.copy(data)             # make a shallow copy of the data object which we will be using to edit. It can load stuff
        if data.control:
            self.selectedSkin = sm.getSkin(data.control.controlType, data)
        self.parentW = None  # for new items
        if self.data.skin and 'size' in self.data.skin:
            self.currentSize = self.data.skin['size']
        super(AssetDialog, self).__init__(**kwargs)
        if self.data.id:
            self.loadUIFromAsset()

    def showAssetSelector(self):
        """renders the root grounds in the treeview."""
        popup = Popup(title="select asset")
        popup.size_hint = (0.8,0.8)
        tv = TreeView(root_options=dict(text='Tree One'), hide_root=True, indent_level=4)
        tv.size_hint = 1, None
        tv.bind(minimum_height = tv.setter('height'))
        tv.load_func = self.populateTreeNode
        tv.bind(selected_node=self.on_assetChanged)
        root = ScrollView(pos = (0, 0))
        root.add_widget(tv)
        popup.add_widget(root)
        popup.open()

    def populateTreeNode(self, treeview, node):
        if not node:
            grounds = iot.getGrounds(True)
            for ground in grounds:
                result = TreeViewLabel(text=ground['title'],is_open=False, is_leaf=False, no_selection=True)
                result.ground_id=ground['id']
                yield result
        elif hasattr(node, 'ground_id'):
            devices = iot.getDevices(node.ground_id)
            for device in devices:
                result = TreeViewLabel(is_open=False, is_leaf=False, no_selection=True)
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

    def loadUIFromAsset(self, setDefaultSkin = False):
        """load all the ui elements for the asset currently loaded in tempdata
        if setDefaultSkin is true, then the 'default' skin will be loaded (or the first in the list)"""
        assetData = self.tempData.load(False)
        if assetData:                                                   # we display the exact name of the asset + device, not the title that we supplied.
            device = iot.getDevice(assetData['deviceId'])
            self.assetName = str(device['title'] or device['name'] or '') + ' - ' + str(assetData['title'] or '')
        self.assetLabel = self.tempData.title
        if hasattr(self, 'selectedSkin') and self.selectedSkin:
            if 'example' in self.selectedSkin:
                imgPath = os.path.join(self.selectedSkin['path'], self.selectedSkin['example'])
                self.selectedSkinExample.source = imgPath
                self.selectedSkinExample.size = sm.getControlSize(self.selectedSkin, self.tempData)
        elif setDefaultSkin:
            skins = sm.getAvailableSkins(self.tempData.control.controlType)
            if 'default' in skins:
                self.setSkin(skins['default'])
            elif len(skins) > 0:
                self.setSkin(skins[0])

        if hasattr(self, 'selectedSkin') and self.selectedSkin:         #could have changed if setDefaultSkin was true
            if self.tempData.control:
                if self.skinPropertyControls:
                    map(self.mainLayout.remove_widget, self.skinPropertyControls)
                self.skinPropertyControls = self.tempData.control.getPropertyEditors(self.selectedSkin)
                map(self.mainLayout.add_widget, self.skinPropertyControls)


    def on_assetChanged(self, instance, id):
        try:
            if instance:
                instance.parent.parent.parent.parent.dismiss()
            if id:
                self.tempData.id = id.asset_id
                self.tempData.isLoaded = False
                self.loadUIFromAsset(True)
        except Exception as e:
            showError(e)

    def showStylesDropDown(self, relativeTo):
        """show a drop down box with all the available style images"""
        if self.tempData.control:
            dropdown = DropDown(auto_width=False, width='140dp')
            skins = sm.getAvailableSkins(self.tempData.control.controlType)
            for skin in skins:
                if 'example' in skin:
                    imgpPath = os.path.join(skin['path'], skin['example'])
                    btn = ImageButton(source=imgpPath,  size_hint_y=None, height=44)
                else:
                    btn = Button(text= skin['name'],  size_hint_y=None, height=44)
                btn.skin = skin
                #btn.bind(on_release=lambda btn: self.setSkin(btn.skin))
                btn.bind(on_press=self.stylesDropDownClosed)
                dropdown.add_widget(btn)
            dropdown.open(relativeTo)


    def stylesDropDownClosed(self, btn):
        """set the skin, close the dropdown"""
        self.setSkin(btn.skin)
        btn.parent.parent.select(None)  #this closes the popup

    def setSkin(self, skin):
        """set the skin"""
        if self.tempData.skin:
            self.tempData.skin["name"] = skin["name"]
        else:
            self.tempData.skin = {'name': skin["name"]}
        if 'example' in skin:
            self.selectedSkinExample.source = os.path.join(skin['path'], skin['example'])
        else:
            self.selectedSkinExample.source = 'None'
        self.selectedSkinExample.size = sm.getControlSize(skin, self.tempData)
        self.selectedSkin = skin

    def setSize(self, size):
        """set the size of the control"""
        if self.tempData.skin:
            self.tempData.skin["size"] = size
        else:
            self.tempData.skin = {'size': size}
        self.selectedSkinExample.size = sm.getControlSize(self.selectedSkin, self.tempData)

    def done(self):
        if self.tempData.id:                        # only do something if there is an id, could be that user closed window after selecting 'add new'
            self.data.id = self.tempData.id
            self.data.skin = self.tempData.skin
            self.data.title = self.tempData.title
            self.data.isLoaded = False
            self.data.load()                # reload the asset data so the control can be rerendered

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

    def done(self):
        if self.nameInput.text:
            name = os.path.join(self.dataPath, self.nameInput.text + '.board')
            if not os.path.isfile(name):
                self.dismiss()
                self.main.newLayoutDone(name)
            else:
                showErrorMsg('layout already exists, please provide another name')



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