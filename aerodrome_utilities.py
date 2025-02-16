# -*- coding: utf-8 -*-

"""
/***************************************************************************
 AerodromeUtilities
                                 A QGIS plugin
 Fetches OSM Data and processes it for aerodroms with various algorithms
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-09-08
        copyright            : (C) 2024 by Aiden Omondi
        email                : helpertech83@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Aiden Omondi'
__date__ = '2024-09-08'
__copyright__ = '(C) 2024 by Aiden Omondi'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import sys
import inspect

from qgis.core import QgsApplication
from qgis.PyQt.QtWidgets import QAction
from .aerodrome_utilities_provider import AerodromeUtilitiesProvider

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)


class AerodromeUtilitiesPlugin(object):

    def __init__(self, iface):
        self.provider = None
        self.iface = iface

    def initProcessing(self):
        """Init Processing provider for QGIS >= 3.8."""
        self.provider = AerodromeUtilitiesProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()
        self.debug_action = QAction("Toggle Debug Mode", self.iface.mainWindow())
        self.debug_action.setCheckable(True)
        self.iface.addToolBarIcon(self.debug_action)

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
