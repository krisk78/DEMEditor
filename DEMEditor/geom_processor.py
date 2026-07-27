# DEMEditor
# Copyright (C) 2026 Christophe Couaillet
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

from qgis.core import QgsGeometry


class DEMGeometryProcessor:

    @staticmethod
    def prepare(
        geometries: list[QgsGeometry]
    ) -> list[QgsGeometry]:

        valid = []

        for geom in geometries:

            if geom.isEmpty():
                continue

            fixed = geom.makeValid()

            if fixed.isEmpty():
                continue

            valid.append(fixed)


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
    