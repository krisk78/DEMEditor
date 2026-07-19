from .dem_tool import DEMPolygonTool
from .toolbar import DEMEditorToolbar


class DEMEditor:

    def __init__(self, iface):

        self.iface = iface

        self.toolbar: DEMEditorToolbar | None = None
        self.canvas_tool: DEMPolygonTool | None = None


    def initGui(self):

        self.toolbar = DEMEditorToolbar(self)
        self.toolbar.create()


    def unload(self):

        if self.canvas_tool is not None:
            self.canvas_tool.reset()

            self.iface.mapCanvas().unsetMapTool(
                self.canvas_tool
            )

            self.canvas_tool = None

        if self.toolbar is not None:
            self.toolbar.remove()


    def activate_polygon_tool(self):

        self.canvas_tool = DEMPolygonTool(
            self.iface.mapCanvas()
        )

        self.iface.mapCanvas().setMapTool(
            self.canvas_tool
        )
        