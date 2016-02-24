__author__ = 'Jan Bogaerts'
__copyright__ = "Copyright 2016, AllThingsTalk"
__credits__ = []
__maintainer__ = "Jan Bogaerts"
__email__ = "jb@allthingstalk.com"
__status__ = "Prototype"  # "Development", or "Production"

import os
import json

#toggleButton_normal = "images\up_button.png"
#toggleButton_down = "images\down_button.png"
#toggleButton_size = (41, 60)

#gauge_gauge = "images/controls/gauge/cadran.png"
#gauge_needle = "images/controls/gauge/needle.png"

#hor_slider_size = (100, 40)
#ver_slider_size = (40, 100)

skinTypes = {}                  # dictionary of all skin types. value is dictionary of skin names + skin

def loadSkins(path):
    """load all the available skins from disk"""
    global skinTypes
    skinTypes = {}                                  # clear any prev values.
    for root, dirs, files in os.walk(path):
        for dir in dirs:
            skins = {}
            skinTypes[dir] = skins
            for root2, dirs2, files2 in os.walk(os.path.join(root, dir)):
                for skin in dirs2:
                    with open(os.path.join(root2, skin, 'definition.json')) as data_file:
                        skins[os.path.abspath(skin)] = json.load(data_file)


def getAvailableSkins(type):
    skins = skinTypes[type]
    return [value for name, value in skins]

def getSkin(type, asset):
    """get the skin for the specified control type and state.
    The asset can overwrite default values"""
    skins = skinTypes[type]
    if skins:
        if asset and asset.skin and "name" in asset.skin:
            return skins[asset.skin["name"]]
        else:
            return skins["default"]


def getControlSize(skin, asset):
    """get the size of control. The asset can overwrite it."""
    if skin:
        if asset and asset.skin and "size" in asset.skin:
            return (skin["size"][0] * asset.skin["size"], skin["size"][1] * asset.skin["size"])
        return (skin["size"][0], skin["size"][1])

    return (100, 100)



def getVar(skin, asset, name):
    if asset and asset.skin and name in asset.skin:
        return asset.skin[name]
    return skin[name]

def getMinimum(type, value, typeInfo):
    if type in ["slider", "gauge"]:
        if 'minimum' in typeInfo:
            result = typeInfo['minimum']
        elif value > 0:
            result = 0
        else:
            result = value * 2
        return result

def getMaximum(type, value, typeInfo):
    if type in ["slider", "gauge"]:
        if 'maximum' in typeInfo:
            result = typeInfo['maximum']
        elif value > 0:
            result = value * 2
        else:
            result = 0
        return result

def getStep(type, typeInfo):
    if type == "slider":
        if typeInfo['type'] == "number":
            return 0.1
        else:
            return 1                                    # we need to make certain that for integers, we use a step size of 1