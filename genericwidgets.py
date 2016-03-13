__author__ = 'Jan Bogaerts'
__copyright__ = "Copyright 2016, AllThingsTalk"
__credits__ = []
__maintainer__ = "Jan Bogaerts"
__email__ = "jb@allthingstalk.com"
__status__ = "Prototype"  # "Development", or "Production"

from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import AsyncImage
from kivy.uix.slider import Slider
from kivy.properties import BooleanProperty, ObjectProperty

class ImageButton(ButtonBehavior, AsyncImage):
    pass

class SliderExt(Slider):
    show_label = BooleanProperty(True)
    show_marker = BooleanProperty(False)
    _label = ObjectProperty(None)  # Internal label that show value.

    def __init__(self, value, typeInfo, asset, **kwargs):
        self.on_dragEnded = None
        super(SliderExt, self).__init__(**kwargs)
        self.bind(show_label=self._show_label)
        self.bind(show_marker=self._show_marker)

    def _show_label(self, o, value):
        if value and self._label not in self.children:
            self.add_widget(self._label)
        elif not value and self._label in self.children:
            self.remove_widget(self._label)

    def _show_marker(self, o, value):
        """add/remove the object"""
        #todo: add TickMarker to slider


    def on_touch_up(self, touch):
        result = super(SliderExt, self).on_touch_up(touch)
        if result and self.on_dragEnded:
            self.on_dragEnded(self, self.value)
        return result