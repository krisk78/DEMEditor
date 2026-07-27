# DEMEditor

QGIS plugin for editing and correcting Digital Elevation Model (DEM) data.

DEMEditor is designed for local and controlled raster modifications while preserving the surrounding DEM structure.
It provides tools to edit raster layers through multi-polygon selections, allowing users to apply transformations only to the areas of interest.

A typical workflow to achieve the same result without DEMEditor is:
- create a vector layer containing the required polygons;
- rasterize the polygons;
- use the resulting raster as an input mask in the raster calculator to apply transformations.

With DEMEditor you can open an editing session and:
- directly draw the polygon selections in the QGIS main window;
- apply the desired transformation to the selected area;
- repeat this workflow to perform multiple transformations.

---

## Installation

### From QGIS Plugin Manager

Available soon...

1. Open QGIS.
2. Go to:
    Plugins → Manage and Install Plugins
3. Search for:
    DEMEditor
4. Install the plugin.

---

### Manual installation

Clone this repository into your QGIS plugin directory:

Linux:

    ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
Windows:

    %APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\

Restart QGIS and enable the plugin.

---

## Requirements

- QGIS 4.x
- Python 3
- NumPy

Earlier QGIS versions may work, but they are not tested and compatibility is not guaranteed.

---

## Usage

1. Load your DEM raster into QGIS.
2. Use the polygon selection tool to delimit the working area.

Use the mouse left button to add a point. The polygon being edited is displayed in red.
Use the mouse right button to end the polygon. It is displayed in green.
You can draw several polygons.
The button Undo removes the last drawn polygon.
   
3. Select the processing algorithm.
4. Configure the algorithm parameters.
5. Run the algorithm.

The output raster is generated as a temporary layer.
Each new processing result replaces the previous one and becomes the input raster for subsequent transformations.

6. Repeat the process for next transformations.

7. Validate or cancel the session when finished.

The validation ends the editing session:
- existing selection polygons are removed;
- the last output raster is detached from the editing session;
- it remains loaded in the project as a temporary layer.

The cancellation ends the editing session:
- existing selection polygons are removed;
- the last temporary output raster is detached from the editing session;
- it is removed from the project and the temporary file is automatically deleted by QGIS.

There is no complete history or multi-step undo mechanism.
Validate your session to preserve your work after significant transformations.
Even once the session is closed, the corrected DEM is stored as a temporary raster.
Do not forget to save it (right-click, then Export...) as permanent file.
Otherwise, the temporary raster may be lost when closing QGIS.

### Adjust elevation

Apply a relative or absolute elevation to the selection.
Additionally, you can filter the selection on an elevation range.

### Smooth steps transitions

Creates smooth elevation transitions around detected terrain fronts.

The tool automatically:
- detects the transition area around each front point;
- evaluates the surrounding elevation reference;
- computes the transition direction from neighbouring terrain structure;
- applies a progressive correction over a configurable radius and angle.

The correction is constrained by the selected edge priority to preserve existing terrain features while reducing abrupt elevation discontinuities.

The transition can be controlled through:
- transition radius;
- transition angle;
- interpolation profile;
- elevation priority mode.

---

## Development

Bug reports and feature requests:
    https://github.com/krisk78/DEMEditor/issues

Contributions are welcome.


