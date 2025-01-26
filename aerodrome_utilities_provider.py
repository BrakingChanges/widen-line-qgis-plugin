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

from qgis.core import QgsProcessingProvider
from .taxiway_widen_algorithm import TaxiwayWidenerAlgorithm
from .polygon_to_singlepart_algorithm import PolygonToSinglePartLinesAlgorithm
from .fetch_osm_data_algorithm import FetchOSMDataAlgorithm
from .geojson_to_topsky_groundradar import GeojsonToTopskyGroundradar
from .split_taxiway_algorithm import SplitTaxiwayAlgorithm
from .colorize_algorithm import ColorizeAlgorithm

class AerodromeUtilitiesProvider(QgsProcessingProvider):

    def __init__(self):
        """
        Default constructor.
        """
        QgsProcessingProvider.__init__(self)

    def unload(self):
        """
        Unloads the provider. Any tear-down steps required by the provider
        should be implemented here.
        """
        pass

    def loadAlgorithms(self):
        """
        Loads all algorithms belonging to this provider.
        """
        self.addAlgorithm(TaxiwayWidenerAlgorithm())
        self.addAlgorithm(PolygonToSinglePartLinesAlgorithm())
        self.addAlgorithm(FetchOSMDataAlgorithm())
        self.addAlgorithm(GeojsonToTopskyGroundradar())
        self.addAlgorithm(SplitTaxiwayAlgorithm())
        self.addAlgorithm(ColorizeAlgorithm())

    def id(self):
        """
        Returns the unique provider id, used for identifying the provider. This
        string should be a unique, short, character only string, eg "qgis" or
        "gdal". This string should not be localised.
        """
        return 'aerodromeutilities'

    def name(self):
        """
        Returns the provider name, which is used to describe the provider
        within the GUI.

        This string should be short (e.g. "Lastools") and localised.
        """
        return self.tr('AerodromeUtilities')

    def icon(self):
        """
        Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return QgsProcessingProvider.icon(self)

    def longName(self):
        """
        Returns the a longer version of the provider name, which can include
        extra details such as version numbers. E.g. "Lastools LIDAR tools
        (version 2.2.1)". This string should be localised. The default
        implementation returns the same string as name().
        """
        return self.name()
