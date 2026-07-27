from qgis.core import(
    QgsRasterLayer,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsProject
)

import numpy as np


def boolmask_to_vector(
        mask: np.ndarray,
        raster: QgsRasterLayer,
        layer_name: str = "mask"
) -> QgsVectorLayer:

    extent = raster.extent()
    pixel_x = raster.rasterUnitsPerPixelX()
    pixel_y = raster.rasterUnitsPerPixelY()

    layer = QgsVectorLayer(
        f"Point?crs={raster.crs().authid()}",
        layer_name,
        "memory"
    )

    provider = layer.dataProvider()
    assert provider is not None
    features = []
    rows, cols = np.nonzero(mask)

    for row, col in zip(rows, cols):

        x = extent.xMinimum() + (col + 0.5) * pixel_x
        y = extent.yMaximum() - (row + 0.5) * pixel_y

        f = QgsFeature()
        f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))
        features.append(f)

    provider.addFeatures(features)
    layer.updateExtents()

    instance = QgsProject.instance()
    assert instance is not None
    instance.addMapLayer(layer)

    return layer