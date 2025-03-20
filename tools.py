import os
from qgis.PyQt.uic import loadUiType, loadUi

def resolve(name, basepath=None):
    if not basepath:
      basepath = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(basepath, name)

def load_ui(path):
    """Get compile UI file.

    :param args List of path elements e.g. ['img', 'logos', 'image.png']
    :type args: str

    :return: Compiled UI file.
    """
    ui_class, _ = loadUiType(path)
    return ui_class