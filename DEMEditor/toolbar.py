from .application_status import ApplicationStatus

from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsApplication


class DEMEditorToolbar:

    def __init__(self, plugin):

        self.plugin = plugin
        self.toolbar = None
        self.select_polygon_action = None
        self.actions = []


    def create(self):

        self.toolbar = self.plugin.iface.addToolBar("DEM Editor")
        self.toolbar.setObjectName("DEMEditorToolbar")

        self.select_polygon_action = self.add_action(
            "Select polygon",
            self.plugin.toggle_polygon_tool,
            "/mActionSelectPolygon.svg",
            checkable=True
        )

        self.elevation_correction_action = self.add_action(
            "Correct altitude",
            self.plugin.correct_altitude,
            ":/images/themes/default/propertyicons/elevationscale.svg",
            theme_icon=False
        )

        self.smooth_steps_action = self.add_action(
            "Smooth elevation steps",
            self.plugin.smooth_steps,
            "/algorithms/mAlgorithmRasterCalculator.svg"
        )

        self.undo_last_polygon_action = self.add_action(
            "Undo last polygon",
            self.plugin.undo_last_polygon,
            "/mActionUndo.svg"
        )

        # Séparation entre outils et validation
        assert self.toolbar is not None
        self.toolbar.addSeparator()

        self.finish_session_action = self.add_action(
            "Finish DEM editing",
            self.plugin.finish_session,
            ":/qt-project.org/styles/commonstyle/images/standardbutton-apply-128.png",
            theme_icon=False
        )

        self.cancel_session_action = self.add_action(
            "Cancel DEM editing",
            self.plugin.cancel_session,
            "/mTaskCancel.svg"
        )


    def add_action(
        self,
        text,
        callback,
        icon_path,
        checkable=False,
        theme_icon=True
    ):

        if theme_icon:
            icon = QgsApplication.getThemeIcon(icon_path)
        else:
            icon = QIcon(icon_path)

        action = QAction(
            icon,
            text,
            self.plugin.iface.mainWindow()
        )

        action.setCheckable(checkable)

        if checkable:
            action.toggled.connect(callback)
        else:
            action.triggered.connect(callback)

        assert self.toolbar is not None
        self.toolbar.addAction(action)

        self.actions.append(action)

        return action


    def remove(self):

        if self.toolbar is not None:

            for action in self.actions:
                self.toolbar.removeAction(action)

            self.plugin.iface.mainWindow().removeToolBar(
                self.toolbar
            )

            self.toolbar = None

        self.actions.clear()


    def update_actions(self, application_status: ApplicationStatus):
        
        if self.select_polygon_action is None:
            return
        
        self.select_polygon_action.setEnabled(
            not application_status.operation_in_progress
        )

        self.elevation_correction_action.setEnabled(
            not application_status.selection_in_progress
            and application_status.has_selection
        )

        self.smooth_steps_action.setEnabled(
            not application_status.selection_in_progress
            and application_status.has_selection
        )

        self.undo_last_polygon_action.setEnabled(
            application_status.has_selection
        )

        self.finish_session_action.setEnabled(
            application_status.has_result_layer
        )
