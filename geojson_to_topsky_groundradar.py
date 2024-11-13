from qgis.PyQt.QtCore import QCoreApplication

from qgis.core import (
	QgsProcessingAlgorithm, 
	QgsProcessingParameterFolderDestination, 
	QgsProcessingParameterBoolean,
	QgsProcessingParameterString
)
import math
import json
import os

class GeojsonToTopskyGroundradar(QgsProcessingAlgorithm):

	SEARCH_DIR = 'SEARCH_DIR'
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
				self.SEARCH_DIR,
				'GeoJSON Directory'
			)
		)

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

	def convert_geojson_to_topsky(self, search_dir, out_path, icao):
		content = ''
		for (dirpath, _dirname, files) in os.walk(search_dir):
			for name in files:
				file_name, ext = os.path.splitext(os.path.join(dirpath, name))
				if 'STAND' in name:
					continue
				if ext == '.geojson':
					with open(os.path.join(dirpath, name), 'r') as source:
						data = json.load(source)
						content += self.ts_header.replace('LAYER:', f'LAYER:{int(name.split("_")[0])}').replace('MAP:', f'MAP:{icao} {' '.join(file_name.split("_")[1:-1]).upper()}').replace("FOLDER:", f"FOLDER:{icao}").replace("AIRPORT:", f"AIRPORT:{icao}")
						for i, feature in enumerate(data["features"]):
							coords = []
							if any(n in name for n in ['POLIGON', 'POLY']):
								if i != 0:
									content += 'COORDLINE\n'
								for coordinate in feature["geometry"]["coordinates"]:
									coords.append(f'COORD:{self.decimal_degrees_dms(coordinate[1], coordinate[0])}')
							elif 'TEXT' in name:
								coordinate = feature["geometry"]["coordinates"]
								coords.append(f'TEXT:{self.decimal_degrees_dms(coordinate[1], coordinate[0])}:{feature["properties"]["TEXT"]}')
							elif 'LINE' in name:
								for i in range(len(feature["geometry"]["coordinates"]) - 1):
									lon1, lat1 = feature["geometry"]["coordinates"][i]
									lon2, lat2 = feature["geometry"]["coordinates"][i + 1]
									coords.append(f"LINE:{self.decimal_degrees_dms(lat1, lon1)}:{self.decimal_degrees_dms(lat2, lon2)}")
							content += '\n'.join(coords)
							if any(n in name for n in ['POLIGON', 'POLY']):
								content += '\nCOORDPOLY:100\n'
							else:
								content += '\n'

		with open(out_path, 'w') as dest:
			dest.write(content)

	def convert_geojson_to_groundradar(self, search_dir, out_path, multi_map, icao):
		content = '' if multi_map else self.gr_header_single.replace("MAP:",f"MAP:{icao}").replace("FOLDER:",f"FOLDER:{icao}").replace("AIRPORT:", f"AIRPORT:{icao}")
		for (dirpath, _dirname, files) in os.walk(search_dir):
			for name in files:
				file_name, ext = os.path.splitext(os.path.join(dirpath, name))
				if ext == '.geojson':
					with open(os.path.join(dirpath, name), 'r') as source:
						data = json.load(source)
						if multi_map:
							content += self.gr_header.replace('MAP:', f'MAP:{icao} {'_'.join(name.split("_")[1:])}').replace("FOLDER:", f"FOLDER:{icao}").replace("AIRPORT:", f"AIRPORT:{icao}")
						else:
							if 'STAND' not in file_name:
								content += f'\n// {' '.join(file_name.split('_')[1:-1]).capitalize()}\nCOLOR:TWY\nCOORDTYPE:OTHER:REGION\n'
						for feature in data["features"]:
							coords = []
							if any(n in name for n in ['POLIGON', 'POLY']):
								for coordinate in feature["geometry"]["coordinates"]:
									coords.append(f'COORD:{self.decimal_degrees_dms(coordinate[1], coordinate[0])}')
							elif 'TEXT' in name:
								coordinate = feature["geometry"]["coordinates"]
								coords.append(f'TEXT:{self.decimal_degrees_dms(coordinate[1], coordinate[0])}:{feature["properties"]["TEXT"]}')
							elif 'LINE' in name:
								for i in range(len(feature["geometry"]["coordinates"]) - 1):
									lon1, lat1 = feature["geometry"]["coordinates"][i]
									lon2, lat2 = feature["geometry"]["coordinates"][i + 1]
									coords.append(f"LINE:{self.decimal_degrees_dms(lat1, lon1)}:{self.decimal_degrees_dms(lat2, lon2)}")
							content += '\n'.join(coords) + '\n'
							if any(n in name for n in ['POLIGON', 'POLY']):
								content += 'COORDTYPE:OTHER:REGION\n'

		with open(out_path, 'w') as dest:
			dest.write(content)

	def convert_geojson_to_stands(self, search_dir, out_path, icao, gr_maps_path):
		content = f'// {icao} Stands'
		content_grmaps = ''
		for (dirpath, _dirname, files) in os.walk(search_dir):
			for name in files:
				file_name, ext = os.path.splitext(os.path.join(dirpath, name))
				if ext == '.geojson' and 'STAND' in name:
					with open(os.path.join(dirpath, name), 'r') as source:
						data = json.load(source)
						content_grmaps += self.gr_header.replace('MAP:', f'MAP:{icao} TWY LABELS').replace('FOLDER:', f'FOLDER:{icao}').replace("AIRPORT:", f"AIRPORT:{icao}").replace("COLOR:TWY", "COLOR:RMK") + '\n'
						for feature in data["features"]:
							content += f'// Stand {feature["properties"]["STAND"]}\n'
							coordinate = feature["geometry"]["coordinates"]
							content += f'STAND:{icao}:{feature["properties"]["STAND"]}:{self.decimal_degrees_dms(coordinate[1], coordinate[0])}:30\n'
							content += f'WTC:{feature["properties"]["WTC"]}\n' if feature["properties"]["WTC"] is not None else ''
							content += f'USE:{feature["properties"]["USE"]}\n' if feature["properties"]["USE"] is not None else ''
							content += 'AREA\n\n' if feature["properties"]["AREA"] else ''

							content_grmaps += f'TEXT:{self.decimal_degrees_dms(coordinate[1], coordinate[0])}:{feature["properties"]["STAND"]}\n'

		with open(out_path, 'w') as dest:
			dest.write(content)
		
		with open(gr_maps_path, 'a') as dest:
			dest.write(content_grmaps)

	def processAlgorithm(self, parameters, context, feedback):
		search_dir = self.parameterAsString(parameters, self.SEARCH_DIR, context)
		out_dir = self.parameterAsString(parameters, self.OUT_DIR, context)
		multi_map = self.parameterAsBool(parameters, self.MULTI_MAP, context)
		icao = self.parameterAsString(parameters, self.ICAO, context)
		ground_radar_path = os.path.join(out_dir, "GroundRadar.txt")


		# Run all conversion functions
		self.convert_geojson_to_topsky(search_dir, os.path.join(out_dir, "TopSkyMaps.txt"), icao)
		self.convert_geojson_to_groundradar(search_dir,ground_radar_path, multi_map, icao)
		self.convert_geojson_to_stands(search_dir, os.path.join(out_dir, "Stands.txt"), icao, ground_radar_path)

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
