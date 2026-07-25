from .edit_context import DEMEditContext

from typing import Protocol

from qgis.core import QgsRasterLayer


class DEMOperation(Protocol):

    def run(self, context: DEMEditContext) -> QgsRasterLayer | None:
        ...