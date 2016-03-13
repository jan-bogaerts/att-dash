__author__ = 'Jan Bogaerts'
__copyright__ = "Copyright 2016, AllThingsTalk"
__credits__ = []
__maintainer__ = "Jan Bogaerts"
__email__ = "jb@allthingstalk.com"
__status__ = "Prototype"  # "Development", or "Production"

from kivy.uix.widget import Widget
from kivy.properties import BooleanProperty, StringProperty, NumericProperty

class Led(Widget):
    Value = BooleanProperty(False)
    Color = StringProperty("")
    Brigthness = NumericProperty(0.8)
    BorderThickness = StringProperty('4dp')
    BorderColor = StringProperty("")