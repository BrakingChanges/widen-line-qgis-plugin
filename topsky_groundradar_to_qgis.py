from qgis.PyQt.QtCore import QCoreApplication
from PyQt5.QtCore import QVariant

from qgis.core import (
	QgsProcessingAlgorithm, 
	QgsProcessingParameterFile,
	QgsProcessingParameterEnum,
	QgsProcessingParameterFolderDestination,
	QgsVectorFileWriter,
	QgsProject,
    QgsVectorLayer,
    QgsFields,
    QgsField,
    QgsFeature,
    QgsPointXY,
    QgsGeometry
)

class TopskyGroundRadarToQGIS(QgsProcessingAlgorithm):
	INPUT_FILE = 'INPUT_FILE'
	TS_GR = 'TS_GR'
	OUTPUT_FOLDER = 'OUTPUT_FOLDER'
	
	def initAlgorithm(self, config=None):
		self.addParameter(QgsProcessingParameterFile(self.INPUT_FILE, 'Input File'))
		self.addParameter(QgsProcessingParameterEnum(self.TS_GR, 'File Type', options=['TopSky', 'GroundRadar']))
		# self.addParameter(QgsProcessingParameterFolderDestination(self.OUTPUT_FOLDER, 'Output Folder'))

	def dms_decimal_degrees(self, part: str):
		# Parse the input part (latitude or longitude)
		direction = part[0]  # 'N', 'S', 'E', or 'W'
		degrees, minutes, seconds, milliseconds = map(float, part[1:].split('.'))
		seconds += milliseconds / 1000  # Convert milliseconds to fractional seconds
		decimal = degrees + (minutes / 60) + (seconds / 3600)
		if direction in ['S', 'W']:
			decimal = -decimal

		return decimal

	def processAlgorithm(self, parameters, context, feedback):
		input_file = self.parameterAsFile(parameters, self.INPUT_FILE, context)
		file_type = self.parameterAsEnum(parameters, self.TS_GR, context)
		# output_folder = self.parameterAsString(parameters, self.OUTPUT_FOLDER, context)


		if file_type == 1:
			with open(input_file, 'r') as f:
				data = f.read()

			elements = data.split('MAP')
			new_el: list[str] = []

			text_layer = QgsVectorLayer('Point?crs=espg:4326', 'Text', 'memory')
			line_layer = QgsVectorLayer('LineString?crs=espg:4326', 'Lines', 'memory')
			text_layer_provider = text_layer.dataProvider()
			line_layer_provider = line_layer.dataProvider()

			text_fields = QgsFields()
			text_fields.append(QgsField('TEXT', QVariant.String))
			
			text_layer.startEditing()
			text_layer_provider.addAttributes(text_fields)
			text_layer.updateFields()




			for el in elements:
				new_el.append('MAP' + el)

			for el in new_el:

				sub_elements = el.split('\n')
				for element in sub_elements:

					parts = element.split(':')

					if parts[0] == 'MAP':
						feedback.pushInfo(f'Map: {element[4:]}')
					if parts[0] == 'TEXT':
						lat = self.dms_decimal_degrees(parts[1])
						lon = self.dms_decimal_degrees(parts[2])
						feedback.pushInfo(f'Text [Coordinates: {lat} {lon} Text:{parts[3]}]')
						feature = QgsFeature()
						point = QgsPointXY(lon, lat)
						feature.setGeometry(QgsGeometry.fromPointXY(point))
						feature.setAttributes([parts[3]])
						text_layer_provider.addFeature(feature)
						text_layer.updateExtents()

					if parts[0] == 'LINE':
						feedback.pushInfo(f'Line [Start point: {parts[1]} End point: {parts[2]}]')
				feedback.pushInfo('\n')
			
			text_layer.commitChanges()
			
			QgsProject.instance().addMapLayer(text_layer)

		return {}


	def name(self):
		return 'topskygroundradartoqgis'

	def displayName(self):
		return 'Convert TS/GR to QGIS'

	def group(self):
		return self.tr(self.groupId())

	def groupId(self):
		return ''

	def tr(self, string):
		return QCoreApplication.translate('Processing', string)

	def createInstance(self):
		return TopskyGroundRadarToQGIS()
