import processing
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
	QgsProcessingAlgorithm, 
	QgsProcessingParameterFeatureSource, 
	QgsProcessingParameterFeatureSink,
	QgsFeatureSink,
	QGsProcessingParam
)

class PolygonToSinglePartLinesAlgorithm(QgsProcessingAlgorithm):

	INPUT = 'INPUT'
	OUTPUT = 'OUTPUT'

	def initAlgorithm(self, config=None):
		# Parameter for the input polygon layer
		self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT, 'Input Polygon Layer'))
		# Parameter for the output line layer
		self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, 'Output Line Layer'))

	def processAlgorithm(self, parameters, context, feedback):
		# Retrieve the input layer
		layer = self.parameterAsSource(parameters, self.INPUT, context)
		
		if layer is None:
			feedback.reportError('Could not load input layer!')
			return {}
		
		feedback.pushInfo(f'Input layer loaded: {layer.sourceName()}')

		layer_source = self.parameterAsString(parameters, self.INPUT, context)
		# Convert polygons to lines
		feedback.pushInfo('Converting polygons to lines...')
		lines_layer = processing.run("qgis:polygonstolines", {
			'INPUT': layer_source,
			'OUTPUT': 'memory:'
		}, context=context, feedback=feedback)['OUTPUT']
		
		if lines_layer is None:
			feedback.reportError('Polygon to line conversion failed!')
			return {}
		
		# Convert multipart lines to single parts
		feedback.pushInfo('Converting multipart geometries to single parts...')
		single_parts_layer = processing.run("qgis:multiparttosingleparts", {
			'INPUT': lines_layer,
			'OUTPUT': 'memory:'
		}, context=context, feedback=feedback)['OUTPUT']
		
		if single_parts_layer is None:
			feedback.reportError('Multipart to single-part conversion failed!')
			return {}

		# Output the final single-part line layer
		(sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
											   single_parts_layer.fields(), single_parts_layer.wkbType(), single_parts_layer.sourceCrs())

		for feature in single_parts_layer.getFeatures():
			sink.addFeature(feature, QgsFeatureSink.FastInsert)

		feedback.pushInfo('Algorithm completed successfully.')
		return {self.OUTPUT: dest_id}
	
	def name(self):
		"""
		Returns the algorithm name, used for identifying the algorithm. This
		string should be fixed for the algorithm, and must not be localised.
		The name should be unique within each provider. Names should contain
		lowercase alphanumeric characters only and no spaces or other
		formatting characters.
		"""
		return 'polygontosinglepart'

	def displayName(self):
		"""
		Returns the translated algorithm name, which should be used for any
		user-visible display of the algorithm name.
		"""
		return self.tr(self.name())

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
		return PolygonToSinglePartLinesAlgorithm()
