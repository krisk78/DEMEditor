from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsApplication


class DEMEditorToolbar:

    def __init__(self, plugin):

        self.plugin = plugin
        self.toolbar = None
        self.actions = []


    def create(self):

        self.toolbar = self.plugin.iface.addToolBar("DEM Editor")
        self.toolbar.setObjectName("DEMEditorToolbar")

        self.add_action(
            "Select polygon",
            self.plugin.activate_polygon_tool,
            "/mActionSelectPolygon.svg"
        )

        self.add_action(
            "Correct altitude",
            self.plugin.correct_altitude,
            "/propertyicons/elevationscale.svg",
            theme_icon=False
        )

        self.add_action(
            "Smooth elevation steps",
            self.plugin.smooth_steps,
            "/algorithms/mAlgorithmRasterCalculator.svg"
        )

        # Séparation entre outils et validation
        assert self.toolbar is not None
        self.toolbar.addSeparator()

        self.add_action(
            "Apply modifications",
            self.plugin.apply_changes,
            "/mActionSaveAllEdits.svg"
        )

        self.add_action(
            "Cancel all edits",
            self.plugin.cancel_changes,
            "/mActionCancelAllEdits.svg"
        )


    def add_action(
        self,
        text,
        callback,
        icon_path,
        theme_icon=True
    ):

        if theme_icon:
            icon = QgsApplication.getThemeIcon(icon_path)
        else:
            icon = QIcon(
                ":/images/themes/default" + icon_path
            )

        action = QAction(
            icon,
            text,
            self.plugin.iface.mainWindow()
        )

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
        