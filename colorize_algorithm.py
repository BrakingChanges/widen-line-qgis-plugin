from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterColor,
    QgsProcessingParameterString,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsSingleSymbolRenderer,
    QgsMarkerSymbol,
    QgsLineSymbol,
    QgsFillSymbol
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QCoreApplication

class ColorizeAlgorithm(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    COLOR = 'COLOR'
    TS_COLOR = 'TS_COLOR'
    GR_COLOR = 'GR_COLOR'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT, 'Input Layer'))
        self.addParameter(QgsProcessingParameterColor(self.COLOR, 'Color'))
        self.addParameter(QgsProcessingParameterString(self.TS_COLOR, 'TopSky Color'))
        self.addParameter(QgsProcessingParameterString(self.GR_COLOR, 'GroundRadar Color'))

    def processAlgorithm(self, parameters, context: QgsProcessingContext, feedback: QgsProcessingFeedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        color = self.parameterAsColor(parameters, self.COLOR, context)
        ts_color = self.parameterAsString(parameters, self.TS_COLOR, context)
        gr_color = self.parameterAsString(parameters, self.GR_COLOR, context)

        # Store custom properties
        layer.setCustomProperty('color', f"{color.red()},{color.green()},{color.blue()}")
        layer.setCustomProperty('ts_color', ts_color)
        layer.setCustomProperty('gr_color', gr_color)

        # Determine the geometry type and apply color
        if layer.geometryType() == 0:  # Point
            symbol = QgsMarkerSymbol.createSimple({'color': color.name()})
        elif layer.geometryType() == 1:  # Line
            symbol = QgsLineSymbol.createSimple({'color': color.name(), 'width': '0.26'})
        elif layer.geometryType() == 2:  # Polygon
            symbol = QgsFillSymbol.createSimple({'color': color.name(), 'outline_color': 'black'})
        else:
            feedback.reportError("Unsupported layer type!")
            return {}

        # Apply new symbology
        layer.setRenderer(QgsSingleSymbolRenderer(symbol))
        layer.triggerRepaint()

        return {self.OUTPUT: layer}

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
