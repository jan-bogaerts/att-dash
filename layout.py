__author__ = 'Jan Bogaerts'
__copyright__ = "Copyright 2015, AllThingsTalk"
__credits__ = []
__maintainer__ = "Jan Bogaerts"
__email__ = "jb@allthingstalk.com"
__status__ = "Prototype"  # "Development", or "Production"

import json
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.event import EventDispatcher
from kivy.uix.checkbox import CheckBox
from kivy.uix.gridlayout import GridLayout
from kivy.uix.spinner import Spinner
import attiotuserclient as IOT
import styleManager as sm
from knob import Knob
from gauge import Gauge
import os

from errors import *

class BaseIO(EventDispatcher):
    def __init__(self, asset, type, **kwargs):
        self.asset = asset
        self.uiEl = None                                                # the ui element that represents this switch, so we can change it's state.
        self._updatingValue = False                                     # when mqtt updates the value, the ui control is updated. We need to prevent that this then triggers sending a new message to the server
        self.controlType = type
        super(BaseIO, self).__init__(**kwargs)

    def prepareUiElement(self):
        """common code, applied to all or most ui elements"""
        if self.uiEl.size:                                                 # if a custom size was specified, don't allow the control to stretch.  if the user did not specify a custom size, then allow the control to stretch.
            self.uiEl.size_hint = (None, None)
            self.uiEl.pos_hint = {"center_x": 0.5}

    def getPropertyEditors(self, skin):
        return []

class SwitchInput(BaseIO):
    value = BooleanProperty(False)
    def __init__(self, value, asset, **kwargs):
        self.value = value
        super(SwitchInput, self).__init__(asset, 'switch', **kwargs)

    def on_value(self, instance, value):
        self._updatingValue = True
        try:
            if self.uiEl:
                if value:
                    self.uiEl.state = "down"
                else:
                    self.uiEl.state = "normal"
        finally:
            self._updatingValue = False

    def getUI(self):
        result = ToggleButton()
        if self.value:
            result.state = 'down'
        skin = sm.getSkin('switch', self.asset)
        result.background_normal = os.path.join(skin['path'], skin["normal"])
        result.background_down = os.path.join(skin['path'], skin["down"])
        result.size = sm.getControlSize(skin, self.asset)
        result.border = 0,0,0,0
        self.uiEl = result
        self.prepareUiElement()
        result.bind(state=self.state_changed)
        return result

    def state_changed(self, instance, value):
        if self._updatingValue == False:                # don't send to cloud if cloud just updated the ui element.
            IOT.send(self.asset.id, value == "down")

class sliderInput(BaseIO):
    value = NumericProperty()
    def __init__(self, value, typeInfo, asset, **kwargs):
        self.value = value
        self._typeInfo = typeInfo
        super(sliderInput, self).__init__(asset, 'slider', **kwargs)

    def on_value(self, instance, value):
        self._updatingValue = True
        try:
            if self.uiEl:
                if self.uiEl.max < value:
                    self.uiEl.max = value
                if self.uiEl.min > value:
                    self.uiEl.min = value
                self.uiEl.value = value
        finally:
            self._updatingValue = False

    def getUI(self):
        """get the ui element"""
        result = Slider()
        if self.value:
            result.value = self.value
        skin = sm.getSkin('slider', self.asset)
        result.size = sm.getControlSize(skin, self.asset)
        result.orientation = sm.getVar(skin, self.asset, "orientation")
        result.min = sm.getMinimum('slider', self.value, self._typeInfo)
        result.max = sm.getMaximum('slider', self.value, self._typeInfo)
        result.step = sm.getStep('slider', self._typeInfo)

        self.uiEl = result
        self.prepareUiElement()
        result.bind(value=self.value_changed)
        return result

    def value_changed(self, instance, value):
        if self._updatingValue == False:                # don't send to cloud if cloud just updated the ui element.
            if self._typeInfo['type'] == 'number':
                IOT.send(self.asset.id, value)
            else:
                IOT.send(self.asset.id, int(value))     # if the cloud expects ints, we can't send something like 1.0

class knobInput(BaseIO):
    value = NumericProperty()
    def __init__(self, value, typeInfo, asset, **kwargs):
        self.value = value
        self._typeInfo = typeInfo
        super(knobInput, self).__init__(asset, 'knob', **kwargs)

    def on_value(self, instance, value):
        self._updatingValue = True
        try:
            if self.uiEl:
                if self.uiEl.max < value:
                    self.uiEl.max = value
                if self.uiEl.min > value:
                    self.uiEl.min = value
                self.uiEl.value = value
        finally:
            self._updatingValue = False

    def getUI(self):
        """get the ui element"""
        result = Knob()
        if self.value:
            result.value = self.value
        skin = sm.getSkin('slider', self.asset)
        result.size = sm.getControlSize(skin, self.asset)
        result.knobimg_source = os.path.join(skin['path'], skin["knob"])
        result.marker_img = os.path.join(skin['path'], skin['marker'])
        result.min = sm.getMinimum('knob', self.value, self._typeInfo)
        result.max = sm.getMaximum('knob', self.value, self._typeInfo)
        result.step = sm.getStep('knob', self._typeInfo)
        result.show_label = sm.getVar(skin,  self.asset, "show_label")
        result.show_marker = sm.getVar(skin, self.asset, "show_marker")

        self.uiEl = result
        self.prepareUiElement()
        result.bind(value=self.value_changed)
        return result

    def value_changed(self, instance, value):
        if self._updatingValue == False:                # don't send to cloud if cloud just updated the ui element.
            if self._typeInfo['type'] == 'number':
                IOT.send(self.asset.id, value)
            else:
                IOT.send(self.asset.id, int(value))     # if the cloud expects ints, we can't send something like 1.0

    def getPropertyEditors(self, skin):
        """
        get all the controls for editing the extra properties of this control.
        The list of controls that is returned, our bound to this object (changes will be stored in the skin object)
        :param skin: json object
        :return: a list of kivy controls that can be used for editing the properties for the skin.
        """
        items = []
        grd = GridLayout(cols=2)

        chk = CheckBox(active=sm.getVar(skin,  self.asset, "show_label"))
        chk.bind(active=self.on_show_labelChanged)
        grd.add_widget(chk)
        grd.add_widget(Label(text='show label'))

        chk = CheckBox(active=sm.getVar(skin,  self.asset, "show_marker"))
        chk.bind(active=self.on_show_markerChanged)
        grd.add_widget(chk)
        grd.add_widget(Label(text='show marker'))

        items.append(grd)
        return items

    def on_show_labelChanged(self, checkbox, value):
        if not self.asset.skin:
            self.asset.skin = {'show_label': value}
        else:
            self.asset.skin['show_label'] = value

    def on_show_markerChanged(self, checkbox, value):
        if not self.asset.skin:
            self.asset.skin = {'show_marker': value}
        else:
            self.asset.skin['show_marker'] = value

class LedOutput(BaseIO):
    value = BooleanProperty(False)
    def __init__(self, value, asset, **kwargs):
        self.value = value
        super(LedOutput, self).__init__(asset, 'led', **kwargs)

    def on_value(self, instance, value):
        self._updatingValue = True
        try:
            if self.uiEl:
                if value:
                    self.uiEl.state = "down"
                else:
                    self.uiEl.state = "normal"
        finally:
            self._updatingValue = False

    def getUI(self):
        result = ToggleButton()
        if self.value:
            result.state = 'down'
        skin = sm.getSkin('led', self.asset)
        result.background_normal = os.path.join(skin['path'], skin['normal'])
        result.background_down = os.path.join(skin['path'], skin['down'])
        result.size = sm.getControlSize(skin, self.asset)
        result.border = [0, 0, 0, 0]
        self.uiEl = result
        self.prepareUiElement()
        return result


class GaugeOutput(BaseIO):
    value = NumericProperty()
    def __init__(self, value, typeInfo, asset, **kwargs):
        self.value = value
        self._typeInfo = typeInfo
        super(GaugeOutput, self).__init__(asset, 'gauge', **kwargs)

    def on_value(self, instance, value):
        self._updatingValue = True
        try:
            if self.uiEl:
                if self.max < value:
                    self.max = value
                if self.min > value:
                    self.min = value
                self.uiEl.value = (value / (self.max - self.min)) * 100 # need to convert into % cause the gauge can only process from 0 to 100
        finally:
            self._updatingValue = False

    def getUI(self):
        """get the ui element"""
        result = Gauge()
        skin = sm.getSkin('gauge', self.asset)
        result.size = sm.getControlSize(skin, self.asset)
        result.file_gauge = os.path.join(skin['path'], skin['gauge'])
        result.file_needle = os.path.join(skin['path'], skin['needle'])
        #self.min = sm.getMinimum('gauge', self.value, self._typeInfo)
        #self.max = sm.getMaximum('gauge', self.value, self._typeInfo)
        self.min = 0                                        #temp fix, gauge needs to be updated so it can handle values better
        self.max = 100
        if self.value:
            result.value = (self.value / (self.max - self.min)) * 100 # need to convert into % cause the gauge can only process from 0 to 100

        self.uiEl = result
        self.prepareUiElement()
        return result

class TextInput(BaseIO):
    #if 'enum' in datatype:
    value = StringProperty()
    def __init__(self, value, typeInfo, asset, **kwargs):
        self.value = value
        self._typeInfo = typeInfo
        super(TextInput, self).__init__(asset, 'text', **kwargs)

    def on_value(self, instance, value):
        self._updatingValue = True
        try:
            self.uiEl.text = value
        finally:
            self._updatingValue = False

    def getUI(self):
        """get the ui element"""
        if 'enum' in self._typeInfo:
            result = Spinner()
            result.values = self._typeInfo['enum']
        else:
            result = TextInput()
        if self.value:
            result.text = self.value
        skin = sm.getSkin('text', self.asset)
        result.size = sm.getControlSize(skin, self.asset)

        self.uiEl = result
        self.prepareUiElement()
        result.bind(text=self.value_changed)
        return result

    def value_changed(self, instance, value):
        if self._updatingValue == False:                # don't send to cloud if cloud just updated the ui element.
            IOT.send(self.asset.id, value)

class TextOutput(BaseIO):
    value = StringProperty()
    def __init__(self, value, typeInfo, asset, **kwargs):
        self.value = value
        self._typeInfo = typeInfo
        super(TextOutput, self).__init__(asset, 'gauge', **kwargs)

    def on_value(self, instance, value):
        self._updatingValue = True
        try:
            if self.uiEl:
                self.uiEl.text = value
        finally:
            self._updatingValue = False

    def getUI(self):
        """get the ui element"""
        result = Label()
        skin = sm.getSkin('label', self.asset)
        result.text_size = sm.getControlSize(skin, self.asset)
        result.bind(texture_size=self.setter('size'))
        if self.value:
            result.text = self.value

        self.uiEl = result
        self.prepareUiElement()
        return result

class Asset:
    def __init__(self, parent, id):
        self.parent = parent
        self.isLoaded = False
        self.id = id
        self.title = ""
        self.control = None
        self.skin = None

    def load(self, subscribe = True):
        """load all the data for the asset. At this point, we also register with the broker
        returns the asset object that was retrieved from the platform"""
        data = IOT.getAsset(self.id)
        if data:
            if self.skin and 'title' in self.skin:          # if user overwote the title, use that value, otherwise use the default value from the cloud
                self.title = self.skin['title']
            else:
                self.title = data["title"]
            self.control = self.getControl(data['is'], data['control'], data['profile'], data['state'])
            self.isLoaded = True
            if subscribe:
                IOT.subscribe(self.id, self._valueChanged)
        return data

    def loadSecure(self, subscribe = True):
        """load all the data for the asset. At this point, we also register with the broker
        returns the asset object that was retrieved from the platform"""
        try:
            return self.load(subscribe)
        except Exception as e:
            showError(e)

    def getGenericActuatorControl(self, datatype, value):
        type = str(datatype['type'])
        if type == 'boolean':
            self.control = SwitchInput(value['value'], self)
            return
        elif type == 'number' or type == 'integer':
            self.control = sliderInput(value['value'], datatype, self)
            return
        self.control = TextInput(str(value['value']), datatype, self)

    def getGenericSensorControl(self, datatype, value):
        type = datatype['type']
        if type == 'boolean':
            self.control = LedOutput(value['value'], self)
            return
        elif type == 'number' or type == 'integer':
            self.control = GaugeOutput(value['value'], datatype, self)
            return
        self.control = TextOutput(str(value['value']), datatype, self)

    def getControl(self, assetType, requested, datatype, value):
        """build the name of the data object that should be used in the display"""
        if not self.control:
            if assetType == 'actuator':
                if not requested['name']:
                    self.getGenericActuatorControl(datatype, value)
                elif requested['name'] in ['slider', 'line-progress']:
                    if datatype['type'] in ['integer', 'number']:                   # can only handle numbers in a slider at the moment
                        self.control = sliderInput(value['value'], datatype, self)
                        return self.control
                elif requested['name'] == 'knob':
                    if datatype['type'] in ['integer', 'number']:
                        self.control = knobInput(value['value'], datatype, self)
                        return self.control
                elif requested['name'] == 'toggle':
                    if type == 'boolean':
                        self.control = SwitchInput(value['value'], self)
                        return self.control
                self.getGenericActuatorControl(datatype, value)
            elif assetType == 'sensor':
                if not requested['name']:
                    self.getGenericSensorControl(datatype, value)
                elif requested['name'] in ['slider', 'line-progress']:
                    if datatype['type'] in ['integer', 'number']:
                        self.control = GaugeOutput(value['value'], datatype, self)
                        return self.control
                elif requested['name'] == 'onoff':
                    if type == 'boolean':
                        self.control = LedOutput(value['value'], self)
                        return self.control
                self.getGenericSensorControl(datatype, value)
        return self.control

    def _valueChanged(self, value):
        """called when the clour has reported a value change for this asset"""
        if self.control:
            self.control.value = value['Value']

    def delete(self):
        self.parent.assets.remove(self)

class Section:
    def __init__(self, parent):
        self.parent = parent
        self.title = ''
        self.isExpanded = True
        self.assets = []
    def delete(self):
        self.parent.sections.remove(self)

class Group(EventDispatcher):
    title = StringProperty('')
    icon = StringProperty('')
    def __init__(self, parent, **kwargs):
        """"ceate object"""
        self.parent = parent
        self.sections = []
        self.isSelected = False
        super(Group, self).__init__(**kwargs)


    def delete(self):
        self.parent.groups.remove(self)

class Layout:
    def __init__(self):
        """create object"""
        self.groups = []
        self.userName = ""
        self.password = ''
        self.server = ''
        self.broker = ''

    def load(self, filename):
        """"load the config from file"""
        with open(filename) as data_file:
            data = json.load(data_file)
            if data["version"] == 1.0:
                credentials = data["credentials"]
                self.userName = credentials["username"]
                self.password = credentials["password"]
                self.server = credentials["server"]
                self.broker = credentials["broker"]
                for group in data["layout"]:
                    grp = Group(self)
                    self.groups.append(grp)
                    grp.title = group["group"]
                    grp.icon = group["icon"]
                    if 'isSelected' in group:
                        grp.isSelected = group["isSelected"]
                    else:
                        grp.isSelected = False
                    for section in group["sections"]:
                        sctn = Section(grp)
                        grp.sections.append(sctn)
                        sctn.title = section["section"]
                        sctn.isExpanded = section["isExpanded"]
                        for rec in section["assets"]:
                            asset = Asset(sctn, rec["id"])
                            if "skin" in rec:
                                asset.skin = rec["skin"]
                            sctn.assets.append(asset)
            else:
                raise Exception("The layout you are trying to load is of an unsupported version.")

    def save(self, filename):
        """save the layout to specified file"""
        with open(filename, 'w') as f:
            f.write('{{"version":1.0, "credentials":{{"username": "{}", "password": "{}", "server":"{}", "broker": "{}"}}, "layout":['
                    .format(self.userName, self.password, self.server, self.broker))
            for grp in self.groups:
                if grp != self.groups[0]: f.write(', ')
                f.write('{{ "group": "{}", "icon": "{}", "isSelected": {}, "sections":['.format(grp.title, grp.icon, str(grp.isSelected).lower()) )
                for sctn in grp.sections:
                    if sctn != grp.sections[0]: f.write(', ')
                    f.write('{{"section": "{}", "isExpanded": {}, "assets":[ '.format(sctn.title, str(sctn.isExpanded).lower()))
                    for asset in sctn.assets:
                        if asset != sctn.assets[0]: f.write(', ')
                        f.write('{{"id": "{}"'.format(asset.id))
                        if asset.skin:
                            f.write(', "skin": ' + json.dumps(asset.skin))
                        f.write('}')
                    f.write(']}')
                f.write(']}')
            f.write(']}')
