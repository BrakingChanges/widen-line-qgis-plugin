from qgis.core import (
	QgsProcessingAlgorithm,
	QgsProcessingParameterVectorLayer,
	QgsProcessingParameterFeatureSink,
	QgsProcessingContext,
	QgsProcessingFeedback,
	QgsVectorLayer,
	QgsGeometry,
	QgsPointXY,
	QgsFeature,
	QgsWkbTypes,
	QgsFields,
	QgsField,
	QgsFeatureSink,
)
from qgis.PyQt.QtCore import QMetaType, QCoreApplication, QVariant


class AutoLabelTaxiwayAlgorithm(QgsProcessingAlgorithm):
	TAXIWAY_CENTERLINE = 'TAXIWAY_CENTERLINE'
	OUTPUT = 'OUTPUT'

	def initAlgorithm(self, config=None):
		self.addParameter(
			QgsProcessingParameterVectorLayer(
				self.TAXIWAY_CENTERLINE,
				'Taxiway Centerline Layer',
			)
		)

		self.addParameter(
			QgsProcessingParameterFeatureSink(
				self.OUTPUT,
				'Output Layer',
			)
		)

	def processAlgorithm(self, parameters, context: QgsProcessingContext, feedback: QgsProcessingFeedback):
		taxiway_layer: QgsVectorLayer = self.parameterAsVectorLayer(
			parameters, self.TAXIWAY_CENTERLINE, context)

		features: list[QgsFeature] = []
		fields = QgsFields()
		fields.append(QgsField("TEXT", QVariant.String))

		(sink, dest_id) = self.parameterAsSink(
			parameters,
			self.OUTPUT,
			context,
			fields,
			QgsWkbTypes.Point,
			taxiway_layer.sourceCrs()
		)

		for feature in taxiway_layer.getFeatures():
			geometry: QgsGeometry = feature.geometry()
			if geometry is None or geometry.isEmpty():
				continue

			midpoint: QgsPointXY = self.get_midpoint_on_line(geometry)

			point_feature = QgsFeature()
			point_feature.setGeometry(QgsGeometry.fromPointXY(midpoint))
			point_feature.setAttributes(
				[feature["ref"] if "ref" in feature.fields().names() else ""])
			sink.addFeature(point_feature, QgsFeatureSink.FastInsert)

		return {self.OUTPUT: dest_id}

	def get_midpoint_on_line(self, line_geometry: QgsGeometry) -> QgsPointXY:
		"""
		Returns the midpoint along the actual length of a QgsGeometry line.
		"""
		if line_geometry.isMultipart():
			line = line_geometry.asMultiPolyline()[0]
		else:
			line = line_geometry.asPolyline()

		total_length = line_geometry.length()
		midpoint_distance = total_length / 2
		midpoint = line_geometry.interpolate(midpoint_distance).asPoint()
		return midpoint

	def name(self):
		return 'autolabeltaxiway'

	def displayName(self):
		return 'Auto Label Taxiways'

	def group(self):
		return self.tr(self.groupId())

	def groupId(self):
		return ''

	def tr(self, string):
		return QCoreApplication.translate('Processing', string)

	def createInstance(self):
		return AutoLabelTaxiwayAlgorithm()
