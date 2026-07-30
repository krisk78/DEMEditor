# DEMEditor
# Copyright (C) 2026 Christophe Couaillet
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

from qgis.core import QgsProject, QgsGeometry, QgsRasterLayer


class DEMGeometryException(Exception):
    pass


class DEMGeometryProcessor:

    @staticmethod
    def validate_raster_context(raster_layer: QgsRasterLayer):

        instance = QgsProject.instance()
        assert instance is not None

        if raster_layer.crs() != instance.crs():
            raise DEMGeometryException("Raster CRS must be the same as the project one.")


    @staticmethod
    def merge_geometries(geometries: list[QgsGeometry]) -> list[QgsGeometry]:

        valid = []

        for geom in geometries:

            if geom.isEmpty():
                continue

            fixed = geom.makeValid()

            if fixed.isEmpty():
                continue

            valid.append(fixed)

        if not valid:
            return []

        # fusion des intersections uniquement
        merged = QgsGeometry.unaryUnion(valid)

        if merged.isEmpty():
            return []

        if merged.isMultipart():
            return [
                QgsGeometry.fromPolygonXY(p)
                for p in merged.asMultiPolygon()
            ]

        return [merged]


    @staticmethod
    def clip_geometries(
        geometries: list[QgsGeometry],
        raster_layer: QgsRasterLayer
    ) -> list[QgsGeometry]:

        raster_geom = QgsGeometry.fromRect(
            raster_layer.extent()
        )

        result = []

        for geom in geometries:

            clipped = geom.intersection(raster_geom)

            if not clipped.isEmpty():
                result.append(clipped)

        return result