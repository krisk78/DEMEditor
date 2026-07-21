from .dem_tool import DEMPolygonTool
from .toolbar import DEMEditorToolbar
from .application_status import ApplicationStatus

from enum import Enum, auto
from dataclasses import dataclass
from qgis.core import QgsProject


class ElevationMode(Enum):
    OFFSET = auto()
    VALUE = auto()


class SmoothMode(Enum):
    LINEAR = auto()
    PARABOLIC = auto()
    COSINE = auto()


@dataclass
class DEMOperation:

    elevation_mode: ElevationMode = ElevationMode.OFFSET

    elevation_offset: float = 0.0
    elevation_value: float = 0.0

    elevation_min: float | None = None
    elevation_max: float | None = None

    elevation_threshold: float = 1.0

    smooth_mode: SmoothMode = SmoothMode.LINEAR


class DEMEditor:

    def __init__(self, iface):

        self.iface = iface

        self.toolbar: DEMEditorToolbar | None = None

        self.current_layer = None
        self.source_layer = None
        
        self.selected_geometries = []
        self.canvas_tool: DEMPolygonTool | None = None

        self.dem_operation = DEMOperation()

        self.application_status: ApplicationStatus = ApplicationStatus()


    def initGui(self):

        self.toolbar = DEMEditorToolbar(self)
        self.toolbar.create()
        self.toolbar.update_actions(self.application_status)


    def unload(self):

        if self.canvas_tool is not None:
            self.canvas_tool.reset()

            self.iface.mapCanvas().unsetMapTool(
                self.canvas_tool
            )

            self.canvas_tool = None

        if self.toolbar is not None:
            self.toolbar.remove()


    def toggle_polygon_tool(self, active):

        if self.application_status.syncing_tool_action:
            return
        
        if active:
            self.activate_polygon_tool()
        else:
            self.deactivate_polygon_tool()
        
        
    def activate_polygon_tool(self):

        self.canvas_tool = DEMPolygonTool(
            self.iface.mapCanvas(),
            self.add_polygon
        )

        self.iface.mapCanvas().setMapTool(
            self.canvas_tool
        )

        self.application_status.polygon_tool_active = True
        self.application_status.selection_in_progress = True
        if self.toolbar is not None:
            self.toolbar.update_actions(self.application_status)


    def deactivate_polygon_tool(self):

        if self.canvas_tool is not None:
            self.iface.mapCanvas().unsetMapTool(
            self.canvas_tool
        )
        
    
    def add_polygon(self, geometry):

        self.selected_geometries.append(geometry)

        self.application_status.has_selection = True
        if self.toolbar is not None:
            self.toolbar.update_actions(self.application_status)



    def correct_altitude(self):
        pass


    def smooth_steps(self):
        pass


    def undo_last_polygon(self):
        
        if self.selected_geometries:
            self.selected_geometries.pop()

        if not self.selected_geometries:
            self.application_status.has_selection = False
            if self.toolbar is not None:
                self.toolbar.update_actions(self.application_status)

        if self.canvas_tool is not None:
            self.canvas_tool.remove_last_selection()


    def reset_step(self):

        self.selected_geometries.clear()
        self.application_status.has_selection = False

        # reset the canvas tool
        if self.canvas_tool is not None:
            self.canvas_tool.reset()

            # unset the map tool
            self.iface.mapCanvas().unsetMapTool(
                self.canvas_tool
            )

            self.canvas_tool = None
        
        self.dem_operation = DEMOperation()


    def reset_session(self):

        self.reset_step()
        self.source_layer = None
        self.current_layer = None

        self.application_status = ApplicationStatus()

        if self.toolbar is not None:
            self.toolbar.update_actions(self.application_status)
            if self.toolbar.select_polygon_action is not None:
                self.toolbar.select_polygon_action.setChecked(False)



    def finish_session(self):
        self.reset_session()        


    def cancel_session(self):

        instance = QgsProject.instance()

        if  instance is not None and self.current_layer is not None:
            instance.removeMapLayer(
                self.current_layer.id()
            )
        
        self.reset_session()


    def on_map_tool_changed(self, tool):

        active = tool == self.canvas_tool
        self.application_status.polygon_tool_active = active

        if (self.toolbar is not None
                and self.toolbar.select_polygon_action is not None):
            self.application_status.syncing_tool_action = True
            self.toolbar.select_polygon_action.setChecked(active)
            self.application_status.syncing_tool_action = False
