import os
import processing
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
	QgsProcessingAlgorithm, 
	QgsProcessingParameterString, 
	QgsProcessingParameterFileDestination, 
	QgsProcessingParameterFeatureSink,
	QgsProcessingParameterBoolean,
	QgsProcessingFeedback, 
	QgsProcessingContext, 
	QgsProject, 
	QgsVectorLayer,
	QgsVectorFileWriter,
	QgsDataProvider,
	QgsCoordinateReferenceSystem,
	QgsProcessingParameterNumber,
	QgsWkbTypes,
	QgsFeatureRequest,
	QgsVectorFileWriter
)
from qgis.core import QgsProcessingParameterFolderDestination
import time

class FetchOSMDataAlgorithm(QgsProcessingAlgorithm):

	ICAO_CODE = 'ICAO_CODE'
	OUTPUT_DIR = 'OUTPUT_DIR'
	
	AUTO_WIDEN_TAXIWAYS = 'AUTO_WIDEN_TAXIWAY'
	AUTO_WIDEN_TAXIWAYS_WIDTH = 'AUTO_WIDEN_TAXIWAYS_WIDTH'
	AUTO_WIDEN_TAXIWAYS_DISSOLVE = 'AUTO_WIDEN_TAXIWAYS_DISSOLVE'
	AUTO_WIDEN_TAXIWAYS_KEEP_CENTERLINE = 'AUTO_WIDEN_TAXIWAYS_KEEP_CENTERLINE'
	AUTO_WIDENED_TAXIWAYS_LINESTRING = 'AUTO_WIDENED_TAXIWAYS_LINESTRING'
	AUTO_POLYGON_LINESTRING = 'AUTO_POLYGON_LINESTRING'

	SPLIT_TAXIWAYS = 'SPLIT_TAXIWAYS'
	SPLIT_TAXIWAYS_OUTPUT = 'SPLIT_TAXIWAYS_OUTPUT'
	

	FEATURE_TYPES = [
		'heliport',
		'grass'
		'apron',
		'taxiway',
		'parking_position',
		'gate',
		'arresting_gear',
		'terminal',
		'hangar',
		'helipad',
		'holding_position',
		'runway',
		'stopway',
		'beacon',
		'navigationaid',
		'windsock',
		'spaceport',
		'airstrip',
		'aircraft_crossing',
		'tower',
		'service',
		'parking'
	]
	GEOMETRY_TYPES = {
		QgsWkbTypes.PointGeometry: 'POINT',
		QgsWkbTypes.LineGeometry: 'LINE',
		QgsWkbTypes.PolygonGeometry: 'POLIGON'
	}

	def initAlgorithm(self, config=None):
		# Input ICAO code
		self.addParameter(QgsProcessingParameterString(self.ICAO_CODE, 'ICAO Code'))
		self.addParameter(QgsProcessingParameterBoolean(self.AUTO_WIDEN_TAXIWAYS, 'Automatically Widen Taxiways'))
		self.addParameter(QgsProcessingParameterBoolean(self.AUTO_WIDEN_TAXIWAYS_DISSOLVE, 'Automatically Dissolve widened taxiways', defaultValue=True))
		self.addParameter(QgsProcessingParameterBoolean(self.AUTO_WIDEN_TAXIWAYS_KEEP_CENTERLINE, 'Keep Original Line as Centerline', defaultValue=True))
		self.addParameter(QgsProcessingParameterNumber(self.AUTO_WIDEN_TAXIWAYS_WIDTH, 'Auto Taxiway Widen Width'))
		self.addParameter(QgsProcessingParameterBoolean(self.SPLIT_TAXIWAYS, 'Split Taxiways'))
		self.addParameter(QgsProcessingParameterFolderDestination(self.SPLIT_TAXIWAYS_OUTPUT, 'Split Taxiways Output Directory'))
		self.addParameter(QgsProcessingParameterFolderDestination(self.OUTPUT_DIR, 'Output Directory'))

	def processAlgorithm(self, parameters, context: QgsProcessingContext, feedback: QgsProcessingFeedback):
		# Get ICAO code and output directory
		icao_code = self.parameterAsString(parameters, self.ICAO_CODE, context).upper()
		output_dir = self.parameterAsString(parameters, self.OUTPUT_DIR, context)

		# AUTO WIDEN TAXIWAY SETTINGS
		auto_widen_taxiway = self.parameterAsBoolean(parameters, self.AUTO_WIDEN_TAXIWAYS, context)
		auto_widen_width = self.parameterAsInt(parameters, self.AUTO_WIDEN_TAXIWAYS_WIDTH, context)
		auto_widen_dissolve = self.parameterAsBoolean(parameters, self.AUTO_WIDEN_TAXIWAYS_DISSOLVE, context)
		auto_widen_keep_centerline = self.parameterAsBoolean(parameters, self.AUTO_WIDEN_TAXIWAYS_KEEP_CENTERLINE, context)

		split_taxiways = self.parameterAsBoolean(parameters, self.SPLIT_TAXIWAYS, context)
		split_taxiways_output_folder = self.parameterAsString(parameters, self.SPLIT_TAXIWAYS_OUTPUT, context)

		
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

			# Add the layer to the project
			if sub_vlayer.isValid():
				QgsProject.instance().addMapLayer(sub_vlayer)
				sub_vlayer.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
				QgsProject.instance().addMapLayer(sub_vlayer)
		
		ad_multipoly: QgsVectorLayer = ad_layer_initial['OUTPUT_MULTIPOLYGONS']
		if not ad_multipoly.isValid():
			feedback.reportError("Failed to load aerodrome layer.")
			return {}
		
		ad_extent = ad_multipoly.extent()

		count = 2
		total_features = len(self.FEATURE_TYPES)
		ref_layers = []
		

		for feature in self.FEATURE_TYPES:
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
				taxiway = False
				sub_vlayer.setName(f"{str(count).zfill(3)}_{feature}_{self.GEOMETRY_TYPES[sub_vlayer.geometryType()]}")

				discovered_taxiway_ref_codes = []


				for layer_feature in sub_vlayer.getFeatures():
					
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

					loaded_taxiways: list[QgsVectorLayer] = []
					layer_paths = []


					if split_taxiways:
						for ref in discovered_taxiway_ref_codes:
							sub_vlayer.selectByExpression(f'ref="{ref}"', QgsVectorLayer.SetSelection)
							ref_layer = sub_vlayer.materialize(QgsFeatureRequest().setFilterFids(sub_vlayer.selectedFeatureIds()))
							save_options = QgsVectorFileWriter.SaveVectorOptions()
							transform_context = QgsProject.instance().transformContext()
							error = QgsVectorFileWriter.writeAsVectorFormatV3(
								ref_layer,
								os.path.join(split_taxiways_output_folder, ref_layer.name()),
								transform_context,
								save_options
							)
							ref_layer.setName(f'TAXIWAY_{ref}')
							ref_layers.append(ref_layer)

							sub_vlayer.removeSelection()						
						QgsProject.instance().addMapLayers(ref_layers)


					if auto_widen_taxiway and auto_widen_width > 0:
						
						QgsProject.instance().addMapLayer(sub_vlayer)
						output_layer: QgsVectorLayer = processing.run("twywiden:taxiwaywidener", {
							'INPUT': sub_vlayer.id(),
							'BUFFER_DISTANCE':auto_widen_width / 2,
							'BUFFER_CAP_STYLE':0,
							'AUTO_POLY_LINESTRING':False,
							'DISSOLVE': auto_widen_dissolve,
							'OUTPUT':'memory:'
						})['OUTPUT']
						
						output_layer.setName(f"{str(count+1).zfill(3)}_{feature}_{self.GEOMETRY_TYPES[output_layer.geometryType()]}")

						if not auto_widen_keep_centerline:
							QgsProject.instance().removeMapLayer(sub_vlayer)
							
						
					else:
						sub_vlayer.setName(f"{str(count).zfill(3)}_{feature}_centerline_{self.GEOMETRY_TYPES[sub_vlayer.geometryType()]}")
						QgsProject.instance().addMapLayer(sub_vlayer)

								
								

					sub_vlayer.setName(f"{str(count).zfill(3)}_{feature}_centerline_{self.GEOMETRY_TYPES[sub_vlayer.geometryType()]}")

				else:
					QgsProject.instance().addMapLayer(sub_vlayer)
				count += 1




		feedback.pushInfo(f"Completed fetching data for {icao_code}")
		return {'Output directory': output_dir}

	def load_all_layers_from_gpkg(self, gpkg_path, feedback):
		""" Load all layers from a given GeoPackage """
		layer = QgsVectorLayer(gpkg_path,"test","ogr")
		subLayers =layer.dataProvider().subLayers()
		sub_vlayers = []

		for subLayer in subLayers:
			name = subLayer.split(QgsDataProvider.SUBLAYER_SEPARATOR)[1]
			uri = "%s|layername=%s" % (gpkg_path, name,)
			# Create layer
			sub_vlayer = QgsVectorLayer(uri, name, 'ogr')
			sub_vlayers.append(sub_vlayer)
				
		return sub_vlayers
			
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