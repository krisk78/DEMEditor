# DEMEditor
# Copyright (C) 2026 Christophe Couaillet
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

from dataclasses import dataclass

from osgeo import gdal

from qgis.core import QgsRasterLayer, QgsCoordinateReferenceSystem

import numpy as np

@dataclass
class RasterData:
    array: np.ndarray
    geo_transform: tuple
    nodata: float

def save_geotiff(
        arr: np.ndarray,
        path:str,
        crs:QgsCoordinateReferenceSystem,
        geo_transform:tuple,
        nodata:float=-9999
):

    height, width = arr.shape

    driver = gdal.GetDriverByName("GTiff")

    ds = driver.Create(
        path,
        width,
        height,
        1,
        gdal.GDT_Float32
    )

    ds.SetGeoTransform(geo_transform)

    ds.SetProjection(crs.toWkt())

    band = ds.GetRasterBand(1)
    band.WriteArray(arr)
    band.SetNoDataValue(nodata)

    ds.FlushCache()
    ds = None


def read_raster_layer(layer:QgsRasterLayer) -> RasterData:

    with gdal.Open(layer.source()) as ds:
        band = ds.GetRasterBand(1)
        raster_data = RasterData(
            array=band.ReadAsArray(),
            geo_transform=ds.GetGeoTransform(),
            nodata=band.GetNoDataValue()
        )

    return raster_data
