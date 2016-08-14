__author__ = 'Jan Bogaerts'
__copyright__ = "Copyright 2016, AllThingsTalk"
__credits__ = []
__maintainer__ = "Jan Bogaerts"
__email__ = "jb@allthingstalk.com"
__status__ = "Prototype"  # "Development", or "Production"

from kivy.uix.label import Label
from kivy.uix.popup import Popup

def showError(e, toAppend = None, toPrepend = None):
    if toPrepend:
        error = toPrepend
    else:
        error = ''
    if hasattr(e, 'strerror'):
        error += e.strerror
    else:
        error += e.message
    if toAppend:
        error += toAppend
    lbl = Label(text=error, size=(300, 200),text_size = (300, 200), halign = 'center', valign = 'middle')
    popup = Popup(title='error', content=lbl,size_hint=(None, None), size=(300, 200), auto_dismiss=True)
    popup.open()


def showErrorMsg(msg):
    lbl = Label(text=msg, size=(300, 200),text_size = (300, 200), halign = 'center', valign = 'middle')
    popup = Popup(title='error', content=lbl,size_hint=(None, None), size=(300, 200), auto_dismiss=True)
    popup.open()
    #popup.dismiss()


_reconnectPopup = None

def _reconectClosed(parame):
    global _reconnectPopup
    _reconnectPopup = None


def closeReconnectError():
    """call this when the reconnect error message box can be closed. (if there is any."""
    if _reconnectPopup:
        _reconnectPopup.dismiss()

def showReconnectError(msg):
    """call this to show an error message for internet reconection issues. While the dialog is open"""
    global _reconnectPopup
    if not _reconnectPopup:
        lbl = Label(text= "Failed to reconnect network, please check your network settings. Error: {}".format(msg), size=(400, 300), text_size=(400, 300), halign='center', valign='middle')
        _reconnectPopup = Popup(title='connection', content=lbl, size_hint=(None, None), size=(400, 300), auto_dismiss=False, on_dismiss=_reconectClosed)
        _reconnectPopup.open()