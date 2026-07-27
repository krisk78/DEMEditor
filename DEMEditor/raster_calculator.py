# DEMEditor
# Copyright (C) 2026 Christophe Couaillet
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

from qgis.core import (
    QgsProcessingAlgorithm, 
    QgsProcessingContext, 
    QgsProcessingException
)
from qgis.PyQt.QtCore import QCoreApplication


class RasterCalculatorAlgorithm(QgsProcessingAlgorithm):

    def __init__(self):

        super().__init__()


    def name(self):
        return "rastercalculator"


    def displayName(self):
        return self.tr("Raster calculator")


    def group(self):
        return self.tr("DEM Editor")


    def groupId(self):
        return "dem_editor"


    def tr(self, string):

        return QCoreApplication.translate(
            "RasterCalculatorAlgorithm",
            string
        )


    def createInstance(self):
        return RasterCalculatorAlgorithm()


    def initAlgorithm(self, configuration=None):
        raise QgsProcessingException("Not yet implemented")


    def processAlgorithm(self, parameters, context: QgsProcessingContext, feedback):
        raise QgsProcessingException("Not yet implemented")
    