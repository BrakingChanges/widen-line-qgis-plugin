import os
import processing
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
	QgsProcessingAlgorithm, 
	QgsProcessingParameterString, 
	QgsProcessingParameterFileDestination, 
	QgsProcessingParameterFeatureSink, 
	QgsProcessingFeedback, 
	QgsProcessingContext, 
	QgsProject, 
	QgsVectorLayer,
	QgsVectorFileWriter,
	QgsDataProvider
)
from qgis.core import QgsProcessingParameterFolderDestination

class FetchOSMDataAlgorithm(QgsProcessingAlgorithm):

	ICAO_CODE = 'ICAO_CODE'
	OUTPUT_DIR = 'OUTPUT_DIR'
	
	FEATURE_TYPES = ['heliport', 'runway', 'stopway', 'helipad', 'taxiway', 'holding_position',
					 'arresting_gear', 'apron', 'parking_position', 'gate', 'terminal', 'hangar',
					 'grass', 'beacon', 'navigationaid', 'windsock', 'spaceport', 'airstrip',
					 'aircraft_crossing', 'tower', 'service', 'parking']

	def initAlgorithm(self, config=None):
		# Input ICAO code
		self.addParameter(QgsProcessingParameterString(self.ICAO_CODE, 'ICAO Code (e.g., HKJK)'))
		
		# Output directory where fetched OSM data will be saved
		self.addParameter(QgsProcessingParameterFolderDestination(self.OUTPUT_DIR, 'Output Directory'))

	def processAlgorithm(self, parameters, context: QgsProcessingContext, feedback: QgsProcessingFeedback):
		# Get ICAO code and output directory
		icao_code = self.parameterAsString(parameters, self.ICAO_CODE, context).upper()
		output_dir = self.parameterAsString(parameters, self.OUTPUT_DIR, context)
		
		# Run OSM query for airport based on ICAO code
		feedback.pushInfo(f"Fetching OSM data for {icao_code}...")
		feature_path = os.path.join(output_dir, f'001_aeroway_aerodrome.gpkg')
		ad_layer_initial = processing.run("quickosm:downloadosmdatanotspatialquery", {
			'KEY': 'icao',
			'VALUE': icao_code,
			'TIMEOUT': 25,
			'SERVER': 'https://overpass-api.de/api/interpreter',
			'FILE': feature_path
		}, context=context, feedback=feedback)

		layer = QgsVectorLayer(feature_path, "master", "ogr")
		sub_layers = layer.dataProvider().subLayers()

		for sub_layer in sub_layers:
			name = sub_layer.split(QgsDataProvider.sublayerSeparator())[1]
			uri = f"{feature_path}|layername={name}"
			sub_vlayer = QgsVectorLayer(uri, name, "ogr")
			QgsProject.instance().addMapLayer(sub_vlayer)

		
		ad_multipoly: QgsVectorLayer = ad_layer_initial['OUTPUT_MULTIPOLYGONS']
		if not ad_multipoly.isValid():
			feedback.reportError("Failed to load aerodrome layer.")
			return {}
		
		ad_extent = ad_multipoly.extent()

		count = 2
		total_features = len(self.FEATURE_TYPES)

		for feature in self.FEATURE_TYPES:
			feedback.pushInfo(f"Fetching {feature} data...")
			feature_path = os.path.join(output_dir, f'{str(count).zfill(3)}_{feature}.gpkg')
			feature_initial = processing.run("quickosm:downloadosmdataextentquery", {
				'KEY': 'aeroway',
				'VALUE': feature,
				'EXTENT': ad_extent,
				'TIMEOUT': 25,
				'SERVER': 'https://overpass-api.de/api/interpreter',
				'FILE': feature_path
			}, context=context, feedback=feedback)
			
			# filtered_layers = list(filter(lambda x: x.featureCount() > 0, feature_initial.values()))
			# for layer in filtered_layers:
			# 	layer_name = f'{str(count).zfill(3)}_aeroway_{feature}'
			# 	layer.setName(layer_name)

			# 	layer_path = os.path.join(output_dir, f'{layer_name}.gpkg')
				
			# 	processing.run("native:saveselectedfeatures", {
			# 		'INPUT': layer,
			# 		'OUTPUT': layer_path
			# 	}, context=context, feedback=feedback)
			
			# 	self.load_all_layers_from_gpkg(layer_path, feedback)
			# 	count += 1

			layer = QgsVectorLayer(feature_path, "master", "ogr")
			sub_layers = layer.dataProvider().subLayers()

			for sub_layer in sub_layers:
				name = sub_layer.split(QgsDataProvider.sublayerSeparator())[1]
				uri = f"{feature_path}|layername={name}"
				sub_vlayer = QgsVectorLayer(uri, name, "ogr")
				QgsProject.instance().addMapLayer(sub_vlayer)


			# Update progress after processing each feature
			count += 1
			feedback.setProgress((count / total_features) * 100)

		feedback.pushInfo(f"Completed fetching data for {icao_code}")
		return {'Output directory': output_dir}

	def load_all_layers_from_gpkg(self, gpkg_path, feedback):
		""" Load all layers from a given GeoPackage """
		layer = QgsVectorLayer(gpkg_path,"test","ogr")
		subLayers =layer.dataProvider().subLayers()

		for subLayer in subLayers:
			name = subLayer.split(QgsDataProvider.SUBLAYER_SEPARATOR)[1]
			uri = "%s|layername=%s" % (gpkg_path, name,)
			# Create layer
			sub_vlayer = QgsVectorLayer(uri, name, 'ogr')
			# Add layer to map
			QgsProject.instance().addMapLayer(sub_vlayer)
			
	
	def name(self):
		return 'fetchosmdata'

	def displayName(self):
		return self.tr(self.name())

	def group(self):
		return self.tr(self.groupId())

	def groupId(self):
		return ''

	def tr(self, string):
		return QCoreApplication.translate('Processing', string)

	def createInstance(self):
		return FetchOSMDataAlgorithm()