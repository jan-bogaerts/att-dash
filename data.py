__author__ = 'Jan Bogaerts'
__copyright__ = "Copyright 2016, AllThingsTalk"
__credits__ = []
__maintainer__ = "Jan Bogaerts"
__email__ = "jb@allthingstalk.com"
__status__ = "Prototype"  # "Development", or "Production"

# this module stores the globally accessible data objects.
# we have to do this, cause the objects Application and MainWindow don't appear to have the same context when on_puuse and on_resume
# are called, making it hard to share module-global variables or fields on 'Application'

data = None
fileName = None
config = None

def save():
    if data:
        data.save(fileName)