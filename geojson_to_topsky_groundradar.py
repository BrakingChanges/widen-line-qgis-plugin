from qgis.PyQt.QtCore import QCoreApplication

from qgis.core import (
	QgsProcessingAlgorithm, 
	QgsProcessingParameterFolderDestination, 
	QgsProcessingParameterBoolean,
	QgsProcessingParameterString,
	QgsVectorLayer,
	QgsWkbTypes
)

from qgis.utils import iface

import math
import os

class GeojsonToTopskyGroundradar(QgsProcessingAlgorithm):

	OUT_DIR = 'OUT_DIR'
	MULTI_MAP = 'MULTI_MAP'
	ICAO = 'ICAO'

	ts_header = '''
MAP:
FOLDER:
LAYER:
ACTIVE:1
COLOR:TWY
'''

	gr_header = '''MAP:
FOLDER:
ACTIVE:1
COLOR:TWY
AIRPORT:
'''

	gr_header_single = '''
MAP:
FOLDER:
AIRPORT:
'''

	def initAlgorithm(self, config=None):
		self.addParameter(
			QgsProcessingParameterFolderDestination(
				self.OUT_DIR,
				'Output Directory'
			)
		)

		self.addParameter(QgsProcessingParameterString(
			self.ICAO,
			'Airport ICAO Code'
		))

		self.addParameter(
			QgsProcessingParameterBoolean(
				self.MULTI_MAP,
				'Multi Map',
				defaultValue=False
			)
		)

	def decimal_degrees_dms(self, decimal_lat, decimal_lon):
		lat_degrees = math.floor(abs(decimal_lat))
		lat_minutes_dec = (abs(decimal_lat) - lat_degrees) * 60
		lat_minutes = math.floor(lat_minutes_dec)
		lat_seconds = math.floor((lat_minutes_dec - lat_minutes) * 60 * 1000) / 1000

		lon_degrees = math.floor(abs(decimal_lon))
		lon_minutes_dec = (abs(decimal_lon) - lon_degrees) * 60
		lon_minutes = math.floor(lon_minutes_dec)
		lon_seconds = math.floor((lon_minutes_dec - lon_minutes) * 60 * 1000) / 1000

		return f"{'S' if decimal_lat < 0 else 'N'}{str(lat_degrees).zfill(3)}.{str(lat_minutes).zfill(2)}.{lat_seconds:.3f}:{'W' if decimal_lon < 0 else 'E'}{str(lon_degrees).zfill(3)}.{lon_minutes:02}.{lon_seconds:.3f}"

	def convert_geojson_to_topsky(self, out_path, icao):
		content = ''
		layers = list(reversed(iface.mapCanvas().layers()))  # Access only checked layers
		
		for layer in layers:
			if not isinstance(layer, QgsVectorLayer):
				continue
			if 'STAND' in layer.name().upper():
				continue

			content += self.ts_header.replace('LAYER:', f'LAYER:{layer.id()}').replace(
				'MAP:', f'MAP:{icao} {layer.name().upper()}').replace(
				"FOLDER:", f"FOLDER:{icao}").replace(
				"AIRPORT:", f"AIRPORT:{icao}")

			for feature in layer.getFeatures():
				geom = feature.geometry()
				coords = []

				if geom.type() == QgsWkbTypes.PolygonGeometry:
					if geom.isMultipart():
						for poly in geom.asMultiPolygon()[0]:
							for pt in poly:
								coords.append(f'COORD:{self.decimal_degrees_dms(pt.y(), pt.x())}')
					else:
						for pt in geom.asPolygon()[0]:
							coords.append(f'COORD:{self.decimal_degrees_dms(pt.y(), pt.x())}')

					content += '\n'.join(coords) + '\nCOORDPOLY:100\n'

				elif geom.type() == QgsWkbTypes.LineGeometry:
					points = geom.asPolyline()
					for i in range(len(points) - 1):
						lon1, lat1 = points[i].x(), points[i].y()
						lon2, lat2 = points[i + 1].x(), points[i + 1].y()
						coords.append(f"LINE:{self.decimal_degrees_dms(lat1, lon1)}:{self.decimal_degrees_dms(lat2, lon2)}")

					content += '\n'.join(coords) + '\n'

				elif geom.type() == QgsWkbTypes.PointGeometry:
					# Check for TEXT attribute before adding points
					if 'TEXT' in feature.fields().names() and feature['TEXT']:
						pt = geom.asPoint()
						coords.append(f'TEXT:{self.decimal_degrees_dms(pt.y(), pt.x())}:{feature["TEXT"]}')
						content += '\n'.join(coords) + '\n'

			with open(out_path, 'w') as dest:
				dest.write(content)

	def convert_geojson_to_groundradar(self, out_path, multi_map, icao):
		content = '' if multi_map else self.gr_header_single.replace("MAP:", f"MAP:{icao}").replace("FOLDER:", f"FOLDER:{icao}").replace("AIRPORT:", f"AIRPORT:{icao}")
		
		layers = list(reversed(iface.mapCanvas().layers()))  # Access only checked layers in the map canvas
		
		for layer in layers:
			if not isinstance(layer, QgsVectorLayer):
				continue

			layer_name = layer.name().upper()
			if multi_map:
				content += self.gr_header.replace('MAP:', f'MAP:{icao} {layer_name}').replace("FOLDER:", f"FOLDER:{icao}").replace("AIRPORT:", f"AIRPORT:{icao}")
			else:
				if 'STAND' not in layer_name:
					content += f'\n// {layer_name}\nCOLOR:TWY\nCOORDTYPE:OTHER:REGION\n'
			
			for feature in layer.getFeatures():
				coords = []
				geom = feature.geometry()
				
				if geom.type() == QgsWkbTypes.PolygonGeometry:
					if geom.isMultipart():
						for poly in geom.asMultiPolygon()[0]:
							for pt in poly:
								coords.append(f'COORD:{self.decimal_degrees_dms(pt.y(), pt.x())}')
					else:
						for pt in geom.asPolygon()[0]:
							coords.append(f'COORD:{self.decimal_degrees_dms(pt.y(), pt.x())}')
					content += '\n'.join(coords) + '\nCOORDTYPE:OTHER:REGION\n'

				elif geom.type() == QgsWkbTypes.LineGeometry:
					points = geom.asPolyline()
					for i in range(len(points) - 1):
						lon1, lat1 = points[i].x(), points[i].y()
						lon2, lat2 = points[i + 1].x(), points[i + 1].y()
						coords.append(f"LINE:{self.decimal_degrees_dms(lat1, lon1)}:{self.decimal_degrees_dms(lat2, lon2)}")
					content += '\n'.join(coords) + '\n'

				elif geom.type() == QgsWkbTypes.PointGeometry:
					# Include point if it has a 'TEXT' attribute
					if 'TEXT' in feature.fields().names() and feature['TEXT']:
						pt = geom.asPoint()
						coords.append(f'TEXT:{self.decimal_degrees_dms(pt.y(), pt.x())}:{feature["TEXT"]}')
						content += '\n'.join(coords) + '\n'
    
		with open(out_path, 'w') as dest:
			dest.write(content)

	def convert_geojson_to_stands(self, out_path, icao, gr_maps_path):
		content = f'// {icao} Stands\n'
		content_grmaps = ''
		layers = list(reversed(iface.mapCanvas().layers()))  # Access only checked layers in the map canvas

		for layer in layers:
			if not isinstance(layer, QgsVectorLayer) or 'STAND' not in layer.name().upper():
				continue

			# Add the header for ground radar maps
			content_grmaps += self.gr_header.replace('MAP:', f'MAP:{icao} TWY LABELS').replace('FOLDER:', f'FOLDER:{icao}').replace("AIRPORT:", f"AIRPORT:{icao}").replace("COLOR:TWY", "COLOR:RMK") + '\n'

			for feature in layer.getFeatures():
				# Ensure the feature is a point and has the required 'STAND' attribute
				if feature.geometry().type() == QgsWkbTypes.PointGeometry and 'STAND' in feature.fields().names() and feature['STAND']:
					coordinate = feature.geometry().asPoint()

					# Add STAND line
					content += f'// Stand {feature["STAND"]}\n'
					content += f'STAND:{icao}:{feature["STAND"]}:{self.decimal_degrees_dms(coordinate.y(), coordinate.x())}:30\n'

					# Optional WTC property
					if 'WTC' in feature.fields().names() and feature['WTC'] is not None:
						content += f'WTC:{feature["WTC"]}\n'

					# Optional USE property
					if 'USE' in feature.fields().names() and feature['USE'] is not None:
						content += f'USE:{feature["USE"]}\n'

					# AREA property
					if 'AREA' in feature.fields().names() and feature['AREA']:
						content += 'AREA\n\n'

					# Add to ground radar maps content
					content_grmaps += f'TEXT:{self.decimal_degrees_dms(coordinate.y(), coordinate.x())}:{feature["STAND"]}\n'

		# Write the STAND content to the output file
		with open(out_path, 'w') as dest:
			dest.write(content)

		# Append the ground radar maps content to the existing file
		with open(gr_maps_path, 'a') as dest:
			dest.write(content_grmaps)

	def processAlgorithm(self, parameters, context, feedback):
		out_dir = self.parameterAsString(parameters, self.OUT_DIR, context)
		multi_map = self.parameterAsBool(parameters, self.MULTI_MAP, context)
		icao = self.parameterAsString(parameters, self.ICAO, context)
		ground_radar_path = os.path.join(out_dir, "GroundRadar.txt")


		# Run all conversion functions
		self.convert_geojson_to_topsky(os.path.join(out_dir, "TopSkyMaps.txt"), icao)
		self.convert_geojson_to_groundradar(ground_radar_path, multi_map, icao)
		self.convert_geojson_to_stands(os.path.join(out_dir, "Stands.txt"), icao, ground_radar_path)

		return {}

	def name(self):
		return 'geojsontotopskygroundradar'

	def displayName(self):
		return 'Convert GeoJSON to TS/GR'

	def group(self):
		return self.tr(self.groupId())

	def groupId(self):
		return ''

	def tr(self, string):
		return QCoreApplication.translate('Processing', string)

	def createInstance(self):
		return GeojsonToTopskyGroundradar()
