__author__ = 'Jan Bogaerts'
__copyright__ = "Copyright 2016, AllThingsTalk"
__credits__ = []
__maintainer__ = "Jan Bogaerts"
__email__ = "jb@allthingstalk.com"
__status__ = "Prototype"  # "Development", or "Production"

from kivy.uix.widget import Widget
from kivy.uix.dropdown import DropDown
from kivy.uix.behaviors import ButtonBehavior, ToggleButtonBehavior
from kivy.properties import NumericProperty, StringProperty, ObjectProperty
from kivy.uix.actionbar import ActionBar, ActionButton
from kivy.uix.togglebutton import ToggleButton
from kivy.graphics.vertex_instructions import *
from kivy.graphics.context_instructions import *
from kivy.uix.floatlayout import FloatLayout

from genericwidgets import *

class EditActionBar(ActionBar):
    pass

class EditButton(ToggleButton):
    """button used to select a control for editing"""

    def __init__(self, **kwargs):
        self.offset = 20
        super(EditButton, self).__init__(**kwargs)

    def reposition(self, parent, value):
        self.x = parent.x + parent.width - self.offset
        self.y = parent.y + parent.height - self.offset

    def repositionAdd(self, parent, value):
        self.x = parent.x + self.offset
        self.y = parent.y + parent.height - self.offset

#class MainDropDown(DropDown):
#    """drop down for editing"""

class InvalidControlWidget(Widget):
    """a widget that is displayed when the control couldn't be loaded"""

class AssetWidget(Widget):
    control_container = ObjectProperty(None)
    def __init__(self, data, **kwargs):
        self.data = data
        super(AssetWidget, self).__init__(**kwargs)


class SectionWidget(Widget):
    assets = ObjectProperty(None)
    def __init__(self, data, **kwargs):
        self.data = data
        super(SectionWidget, self).__init__(**kwargs)

class GroupMenuItem(ButtonBehavior, Widget):
    """represents a button with text on the menu bar. when clicked, load all the sections of this group on the workspace"""
    #selectionHeight = NumericProperty(0)
    #selectionWidth = NumericProperty(0)

    def __init__(self, data, **kwargs):
        self.data = data
        # self.group = 'menu'
        super(GroupMenuItem, self).__init__(**kwargs)
        self.backgroundRect = None
        self.backgroundLine = None
        self.bind(pos=self.update_select)
        self.bind(size=self.update_select)

    def showSelectionBox(self, value):
        if value:
            with self.canvas.before:
                Color(0.1, 0.2, 0.2, 1)
                self.backgroundRect = RoundedRectangle(pos=self.pos, size=self.size)
                Color(0.9, 0.9, 0.2, 1)
                self.backgroundLine = Line(rounded_rectangle=(self.x, self.y, float(self.width), float(self.height), 10.0, 10.0, 10.0, 10.0))
        else:
            self.canvas.before.clear()
            self.backgroundRect = None
            self.backgroundLine = None

    def update_select(self, parent, value):
        if self.backgroundLine:
            self.backgroundLine.rounded_rectangle = (self.x, self.y, float(self.width), float(self.height), 10.0, 10.0, 10.0, 10.0)
        if self.backgroundRect:
            self.backgroundRect.pos = self.pos
            self.backgroundRect.size = self.size

    def toggleSelected(self):
        self.data.isSelected = not self.data.isSelected
        self.showSelectionBox(self.data.isSelected)

    def on_press(self):
        if self.data.isSelected == False:                   # only react if we are not selected, if we are, we don't need to switch focus.
            self.parent.parent.parent.parent.parent.parent.setSelectedGroup(self)

