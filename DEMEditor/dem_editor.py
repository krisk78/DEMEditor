from .dem_tool import DEMPolygonTool
from .toolbar import DEMEditorToolbar
from .application_status import ApplicationStatus
from .edit_context import DEMEditContext
from .geom_processor import DEMGeometryProcessor
from .dem_operation import DEMOperation
from .dem_adjust_elevation import DEMAdjustElevation

from qgis.core import QgsProject, QgsRasterLayer
from qgis.gui import QgisInterface, QgsMapCanvas


class DEMEditor:

    def __init__(self, iface: QgisInterface):

        self.iface = iface

        self.toolbar: DEMEditorToolbar | None = None

        self.current_layer: QgsRasterLayer | None = None
        
        self.selected_geometries = []
        self.canvas_tool: DEMPolygonTool | None = None

        self.application_status: ApplicationStatus = ApplicationStatus()

        map_canvas = self.iface.mapCanvas()
        assert map_canvas is not None
        self.map_canvas: QgsMapCanvas = map_canvas
        self.map_canvas.mapToolSet.connect(
            self.on_map_tool_changed
        )


    def initGui(self):

        self.toolbar = DEMEditorToolbar(self)
        self.toolbar.create()
        self.toolbar.update_actions(self.application_status)


    def unload(self):

        try:
            self.map_canvas.mapToolSet.disconnect(
                self.on_map_tool_changed
            )
        except TypeError:
            pass

        if self.canvas_tool is not None:
            self.canvas_tool.reset()

            self.map_canvas.unsetMapTool(
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

        if self.canvas_tool is None:
            self.canvas_tool = DEMPolygonTool(
                self.iface.mapCanvas(),
                self.add_polygon
            )

        self.map_canvas.setMapTool(
            self.canvas_tool
        )

        self.application_status.polygon_tool_active = True
        self.application_status.selection_in_progress = True
        if self.toolbar is not None:
            self.toolbar.update_actions(self.application_status)


    def deactivate_polygon_tool(self):

        if self.canvas_tool is not None:
            self.map_canvas.unsetMapTool(
            self.canvas_tool
        )
        
    
    def add_polygon(self, geometry):

        self.selected_geometries.append(geometry)

        self.application_status.has_selection = True
        if self.toolbar is not None:
            self.toolbar.update_actions(self.application_status)


    def prepare_operation(self) -> DEMEditContext:

        instance = QgsProject.instance()
        if (
            instance is not None
            and self.current_layer is not None
            and instance.mapLayer(self.current_layer.id()) is None
        ):
            self.current_layer = None

        context = DEMEditContext(
            input_layer=self.current_layer,
            geometries=DEMGeometryProcessor.prepare(
                self.selected_geometries
            )
        )
        return context
    

    def execute_operation(self, operation: DEMOperation):

        context = self.prepare_operation()
        new_layer = operation.run(context)
        self.end_operation(new_layer)
    

    def end_operation(self, new_layer: QgsRasterLayer | None):

        if new_layer is not None:
            instance = QgsProject.instance()
            if self.current_layer is not None and instance is not None:
                instance.removeMapLayer(self.current_layer.id())
            self.current_layer = new_layer

            self.application_status.has_result_layer = True
            self.reset_step()


    def adjust_elevations(self):
        self.execute_operation(DEMAdjustElevation())


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
        if self.toolbar is not None:
            self.toolbar.update_actions(self.application_status)

        # reset the canvas tool
        if self.canvas_tool is not None:
            self.canvas_tool.reset()

            # unset the map tool
            self.map_canvas.unsetMapTool(
                self.canvas_tool
            )

            self.canvas_tool = None


    def reset_session(self):

        self.reset_step()
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
