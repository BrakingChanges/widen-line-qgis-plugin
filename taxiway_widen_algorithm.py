# -*- coding: utf-8 -*-

"""
/***************************************************************************
 TaxiwayWidener
                                 A QGIS plugin
 Widens taxiways fetched from OSM
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

__author__ = 'Aiden Omondi'
__date__ = '2024-09-08'
__copyright__ = '(C) 2024 by Aiden Omondi'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import QCoreApplication
from qgis import processing
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterCrs,
                       QgsCoordinateReferenceSystem,
                       QgsVectorLayer,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterBoolean,
                       QgsProject
                       )


class TaxiwayWidenerAlgorithm(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT = 'INPUT'
    BUFFER_DISTANCE = 'BUFFER_DISTANCE'
    OUTPUT = 'OUTPUT'
    BUFFER_CAP_STYLE = 'BUFFER_CAP_STYLE'
    DISSOLVE = 'DISSOLVE'
    AUTO_POLY_LINESTRING = 'AUTO_POLY_LINESTRING'



    def initAlgorithm(self, config=None):
        # Parameter for the input layer
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT, 'Input Layer'))
        self.addParameter(QgsProcessingParameterNumber(self.BUFFER_DISTANCE, 'Buffer Distance', defaultValue=100))
        self.addParameter(QgsProcessingParameterEnum(self.BUFFER_CAP_STYLE, 'Buffer Cap Style', options=['Round', 'Flat', 'Square'], defaultValue=0))
        self.addParameter(QgsProcessingParameterBoolean(self.AUTO_POLY_LINESTRING, 'Convert result to linestring'))
        self.addParameter(QgsProcessingParameterBoolean(self.DISSOLVE, 'Dissolve result'))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, 'Output Layer'))

    def processAlgorithm(self, parameters, context, feedback):
        # Retrieve the input layer from parameters
        layer = self.parameterAsSource(parameters, self.INPUT, context)
        
        if layer is None:
            feedback.reportError('Could not load input layer!')
            return {}
        
        feedback.pushInfo(f'Input layer loaded: {layer.sourceName()}')

        # Calculate the centroid of the layer's extent
        extent = layer.sourceExtent()
        centroid = extent.center()

        # Calculate the UTM zone
        longitude = centroid.x()
        utm_zone = int((longitude + 180) / 6) + 1

        QgsProject.instance().setCrs(QgsCoordinateReferenceSystem('ESPG:4322'))


        # Determine the hemisphere (Northern/Southern)
        hemisphere = '322' if centroid.y() >= 0 else '323'  # EPSG:326xx for Northern, EPSG:327xx for Southern
        epsg_code = int(f'{hemisphere}{utm_zone}')

        feedback.pushInfo(f'Calculated UTM zone: {utm_zone}, EPSG: {epsg_code}')
        layer_source = self.parameterAsString(parameters, self.INPUT, context)

        # Reproject to the calculated UTM CRS
        feedback.pushInfo('Reprojecting to calculated UTM CRS...')
        reprojected_layer = processing.run("qgis:reprojectlayer", {
            'INPUT': layer_source,
            'TARGET_CRS': QgsCoordinateReferenceSystem(f'EPSG:{epsg_code}'),
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)['OUTPUT']
        
        if reprojected_layer is None:
            feedback.reportError('Reprojection failed!')
            return {}
        
        # Buffer the reprojected layer
        feedback.pushInfo('Buffering the reprojected layer...')
        buffer_distance = self.parameterAsDouble(parameters, self.BUFFER_DISTANCE, context)
        dissolve = self.parameterAsBoolean(parameters, self.DISSOLVE, context)

        buffered_layer: QgsVectorLayer = processing.run("qgis:buffer", {
            'INPUT': reprojected_layer,
            'DISTANCE': buffer_distance,
            'DISSOLVE': dissolve,
            'OUTPUT': 'TEMPORARY_OUTPUT'
        }, context=context, feedback=feedback)['OUTPUT']
        
        if buffered_layer is None:
            feedback.reportError('Buffering failed!')
            return {}
        
        # Reproject back to the original CRS
        feedback.pushInfo('Reprojecting back to the original CRS...')
        
        # Incase you needed WGS72
        auto_poly_linestring = self.parameterAsBoolean(parameters, self.AUTO_POLY_LINESTRING, context)

        if auto_poly_linestring: 
            QgsProject.instance().addMapLayer(buffered_layer)

            final_layer = processing.run("twywiden:polygontosinglepart", {
                'INPUT': buffered_layer.id(),
                'OUTPUT':'memory:'
            })['OUTPUT']

            QgsProject.instance().removeMapLayer(buffered_layer)

        else:
            final_layer = buffered_layer
        


        if final_layer is None:
            feedback.reportError('Final reprojection failed!')
            return {}

        # Output the final layer
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                               layer.fields(), final_layer.wkbType(), final_layer.sourceCrs())
        
        for feature in final_layer.getFeatures():
            sink.addFeature(feature, QgsFeatureSink.FastInsert)

        QgsProject.instance().setCrs(QgsCoordinateReferenceSystem('ESPG:4326'))
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
        return 'taxiwaywidener'

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
        return TaxiwayWidenerAlgorithm()
