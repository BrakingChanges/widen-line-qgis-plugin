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

import os
import processing
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
	QgsProcessingAlgorithm,
	QgsProcessingParameterVectorLayer,
	QgsVectorLayer,
	QgsFeatureRequest,
	QgsProject
)

class SplitTaxiwayAlgorithm(QgsProcessingAlgorithm):
	INPUT = 'INPUT'

	def initAlgorithm(self, config=None):
		self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT, 'Input Line Layer'))
	
	def processAlgorithm(self, parameters, context, feedback):
		layer = self.parameterAsVectorLayer(parameters, self.INPUT, context)

		discovered_taxiway_ref_codes = []
		ref_layers = []
		
		for layer_feature in layer.getFeatures():
			
			aeroway = "N/A"
			ref = "NULL"

			if "aeroway" in layer_feature.fields().names():
				aeroway = layer_feature["aeroway"]

			if aeroway == "taxiway":
				taxiway = True

				if "ref" in layer_feature.fields().names():
					ref = layer_feature["ref"]

				if ref not in discovered_taxiway_ref_codes:
					discovered_taxiway_ref_codes.append(ref)
		
		if taxiway:
			for ref in discovered_taxiway_ref_codes:
				layer.selectByExpression(f'"ref"=\'{ref}\'', QgsVectorLayer.SetSelection)
				ref_layer = layer.materialize(QgsFeatureRequest().setFilterFids(layer.selectedFeatureIds()))
				ref_layer.setName(f'TAXIWAY_{ref}')
				ref_layers.append(ref_layer)

				layer.removeSelection()						
			QgsProject.instance().addMapLayers(ref_layers)
		return {}

	def name(self):
		"""
		Returns the algorithm name, used for identifying the algorithm. This
		string should be fixed for the algorithm, and must not be localised.
		The name should be unique within each provider. Names should contain
		lowercase alphanumeric characters only and no spaces or other
		formatting characters.
		"""
		return 'splittaxiway'

	def displayName(self):
		"""
		Returns the translated algorithm name, which should be used for any
		user-visible display of the algorithm name.
		"""
		return 'Split Taxiways'

	def group(self):
		"""
		Returns the name of the group this algorithm belongs to. This string
		should be localised.
		"""
		return self.tr(self.groupId())

	def groupId(self):
		"""
		Returns the unique ID of the group this algorithm belongs to. This
		string should be fixed for the algorithm, and must not be localised.
		The group id should be unique within each provider. Group id should
		contain lowercase alphanumeric characters only and no spaces or other
		formatting characters.
		"""
		return ''
	
	def tr(self, string):
		return QCoreApplication.translate('Processing', string)

	def createInstance(self):
		return SplitTaxiwayAlgorithm()

