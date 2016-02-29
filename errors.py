__author__ = 'Jan Bogaerts'
__copyright__ = "Copyright 2016, AllThingsTalk"
__credits__ = []
__maintainer__ = "Jan Bogaerts"
__email__ = "jb@allthingstalk.com"
__status__ = "Prototype"  # "Development", or "Production"

from kivy.uix.label import Label
from kivy.uix.popup import Popup

def showError(e, toAppend = None):
    if hasattr(e, 'strerror'):
        error = e.strerror
    else:
        error = e.message
    if toAppend:
        error += toAppend
    lbl = Label(text=error, size=(300, 200),text_size = (300, 200), halign = 'center', valign = 'middle')
    popup = Popup(title='error', content=lbl,size_hint=(None, None), size=(300, 200), auto_dismiss=True)
    popup.open()


def showErrorMsg(msg):
    lbl = Label(text=msg, size=(300, 200),text_size = (300, 200), halign = 'center', valign = 'middle')
    popup = Popup(title='error', content=lbl,size_hint=(None, None), size=(300, 200), auto_dismiss=True)
    popup.open()