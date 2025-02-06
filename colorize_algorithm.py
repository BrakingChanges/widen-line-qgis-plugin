from qgis.core import (
	QgsProcessingAlgorithm,
	QgsProcessingParameterFeatureSource,
	QgsProcessingParameterColor,
	QgsProcessingParameterString,
	QgsProcessingParameterFeatureSink,
	QgsProcessingContext,
	QgsProcessingFeedback,
	QgsProcessingUtils
)
from PyQt5.QtCore import QCoreApplication

class ColorizeAlgorithm(QgsProcessingAlgorithm):
	INPUT = 'INPUT'
	OUTPUT = 'OUTPUT'
	COLOR = 'COLOR'
	TS_COLOR = 'TS_COLOR'
	GR_COLOR = 'GR_COLOR'

	def initAlgorithm(self, config=None):
		self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT, 'Input Layer'))
		self.addParameter(QgsProcessingParameterColor(self.COLOR, 'Color'))
		self.addParameter(QgsProcessingParameterString(self.TS_COLOR, 'TopSky Color'))
		self.addParameter(QgsProcessingParameterString(self.GR_COLOR, 'GroundRadar Color'))
		self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, 'Output Layer'))
	
	def processAlgorithm(self, parameters, context: QgsProcessingContext, feedback: QgsProcessingFeedback):
		layer = self.parameterAsSource(parameters, self.INPUT, context)
		color = self.parameterAsColor(parameters, self.COLOR, context)
		ts_color = self.parameterAsString(parameters, self.TS_COLOR, context)
		gr_color = self.parameterAsString(parameters, self.GR_COLOR, context)

		(sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, layer.fields(), layer.wkbType(), layer.sourceCrs())

		sink.addFeatures(layer.getFeatures())

		output_layer = QgsProcessingUtils.mapLayerFromString(dest_id, context)
		
		if output_layer:
			output_layer.setCustomProperty('color', f"{color.red()},{color.green()},{color.blue()}")
			output_layer.setCustomProperty('ts_color', ts_color)
			output_layer.setCustomProperty('gr_color', gr_color)
			output_layer.renderer().symbol().setColor(color)
		
		return {self.OUTPUT: dest_id}

	def name(self):
		return 'colorize'

	def displayName(self):
		return 'Colorize'

	def group(self):
		return self.tr(self.groupId())

	def groupId(self):
		return ''

	def tr(self, string):
		return QCoreApplication.translate('Processing', string)

	def createInstance(self):
		return ColorizeAlgorithm()