# DEMEditor
# Copyright (C) 2026 Christophe Couaillet
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

from .dem_tool import DEMPolygonTool
from .toolbar import DEMEditorToolbar
from .application_status import ApplicationStatus
from .edit_context import DEMEditContext
from .geom_processor import DEMGeometryProcessor
from .dem_algo_wrapper import DEMAlgorithmWrapper
from .adjust_elevation_algo import AdjustElevationAlgorithm
from .smooth_steps_algo import SmoothStepsAlgorithm
from .external_algo import ExternalAlgorithm
from .raster_calculator import RasterCalculatorAlgorithm
from .user_expression import UserExpressionAlgorithm

from typing import Type, cast

from qgis.core import QgsProject, QgsRasterLayer, QgsProcessingAlgorithm
from qgis.gui import QgisInterface, QgsMapCanvas


class DEMEditor:

    def __init__(self, iface: QgisInterface):

        self.iface = iface

        self.toolbar: DEMEditorToolbar | None = None

        self.current_layer_id: str | None = None
        
        self.selected_geometries = []
        self.canvas_tool: DEMPolygonTool | None = None

        self.application_status: ApplicationStatus = ApplicationStatus()

        map_canvas = self.iface.mapCanvas()
        assert map_canvas is not None
        self.map_canvas: QgsMapCanvas = map_canvas
        self.map_canvas.mapToolSet.connect(
            self.on_map_tool_changed
        )

        instance = QgsProject.instance()
        if instance is None:
            raise ValueError("Unable to retrieve project instance")
        self.instance: QgsProject = instance


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


    def prepare_operation(self, is_a_wrapper: bool=False) -> DEMEditContext:

        layer = None
        if self.current_layer_id:
            layer = self.instance.mapLayer(self.current_layer_id)
            if layer is None:
                self.current_layer_id = None

        context = DEMEditContext(
            input_layer=cast(QgsRasterLayer, layer),
            geometries=DEMGeometryProcessor.merge_geometries(
                self.selected_geometries
            ),
            wrapper_algo=is_a_wrapper
        )
        return context
    

    def execute_operation(
            self,
            algorithm_cls: Type[QgsProcessingAlgorithm],
            is_a_wrapper: bool=False
    ):

        context = self.prepare_operation(is_a_wrapper)
        new_layer = DEMAlgorithmWrapper().run(algorithm_cls, context)
        self.end_operation(new_layer)
    

    def end_operation(self, new_layer: QgsRasterLayer | None):

        if new_layer is not None:
            if self.current_layer_id is not None:
                layer = self.instance.mapLayer(self.current_layer_id)
                if layer:
                    self.instance.removeMapLayer(self.current_layer_id)
                    self.map_canvas.refresh()
            self.current_layer_id = new_layer.id()

            self.application_status.has_result_layer = True
            self.reset_step()


    def adjust_elevations(self):
        self.execute_operation(AdjustElevationAlgorithm)


    def smooth_steps(self):
        self.execute_operation(SmoothStepsAlgorithm)


    def external_algorithm(self):
        self.execute_operation(ExternalAlgorithm, is_a_wrapper=True)


    def raster_calculator(self):
        self.execute_operation(RasterCalculatorAlgorithm, is_a_wrapper=True)


    def user_expression(self):
        self.execute_operation(UserExpressionAlgorithm, is_a_wrapper=True)


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
        self.current_layer_id = None

        self.application_status = ApplicationStatus()

        if self.toolbar is not None:
            self.toolbar.update_actions(self.application_status)
            if self.toolbar.select_polygon_action is not None:
                self.toolbar.select_polygon_action.setChecked(False)


    def finish_session(self):
        self.reset_session()        


    def cancel_session(self):

        if self.current_layer_id:
            layer = self.instance.mapLayer(self.current_layer_id)
            if layer:
                self.instance.removeMapLayer(self.current_layer_id)
                self.map_canvas.refresh()
        
        self.reset_session()


    def on_map_tool_changed(self, tool):

        active = tool == self.canvas_tool
        self.application_status.polygon_tool_active = active

        if (self.toolbar is not None
                and self.toolbar.select_polygon_action is not None):
            self.application_status.syncing_tool_action = True
            self.toolbar.select_polygon_action.setChecked(active)
            self.application_status.syncing_tool_action = False
