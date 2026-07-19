from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QToolBar

from .dem_tool import DEMPolygonTool


class DEMEditor:

    def __init__(self, iface):

        self.iface = iface

        self.action = None
        self.toolbar = None

        self.tool = None


    def initGui(self):

        # Toolbar creation
        self.toolbar = QToolBar(
            "DEMEditor",
            self.iface.mainWindow()
        )

        self.toolbar.setObjectName(
            "DEMEditorToolbar"
        )

        self.iface.mainWindow().addToolBar(
            self.toolbar
        )

        # Action button
        self.action = QAction(
            "Draw a DEM area",
            self.iface.mainWindow()
        )

        self.action.triggered.connect(
            self.activate_polygon_tool
        )


        # Add button in toolbar
        self.toolbar.addAction(
            self.action
        )


        # For now we maintain toolbar menu
        self.iface.addPluginToMenu(
            "&DEM Editor",
            self.action
        )


    def unload(self):

        if self.tool:
            self.tool.reset()

            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.tool = None
            
        if self.toolbar:
            self.iface.mainWindow().removeToolBar(
                self.toolbar
            )
            self.toolbar = None

        if self.action:
            self.iface.removePluginMenu(
                "&DEM Editor",
                self.action
            )


    def activate_polygon_tool(self):

        self.tool = DEMPolygonTool(
            self.iface.mapCanvas()
        )

        self.iface.mapCanvas().setMapTool(
            self.tool
        )