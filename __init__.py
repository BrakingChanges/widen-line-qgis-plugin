# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TaxiwayWidener
                                 A QGIS plugin
 Widens taxiways fetched from OSM
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
 This script initializes the plugin, making it known to QGIS.
"""

__author__ = 'Aiden Omondi'
__date__ = '2024-09-08'
__copyright__ = '(C) 2024 by Aiden Omondi'


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load TaxiwayWidener class from file TaxiwayWidener.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .aerodrome_utilities import AerodromeUtilitiesPlugin
    return AerodromeUtilitiesPlugin()
