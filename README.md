# DEMEditor

QGIS plugin for editing and correcting Digital Elevation Models (DEM) for coastal and harbour environments.

DEMEditor provides tools to detect elevation discontinuities, identify terrain fronts, and apply controlled elevation transitions while preserving the original DEM structure.

The main objective is to simplify the correction of coastal DEM artefacts such as:

- harbour edges,
- quays,
- docks,
- artificial shore structures,
- bathymetric transitions,
- terrain discontinuities caused by DEM resolution or source data merging.

---

## Features

### Front detection

Detects terrain fronts based on local elevation differences.

The detection algorithm analyses neighbouring cells and identifies pixels where the elevation difference exceeds a user-defined threshold.

Supported cases:

- lower elevation fronts (land → water / bathymetry transitions),
- higher elevation fronts (water → structure / embankment transitions).

---

### Front direction estimation

For each detected front point, DEMEditor computes a local transition direction.

The direction estimation is based on neighbouring cells matching the selected elevation threshold, allowing the correction direction to follow the actual DEM structure rather than relying on a purely geometric assumption.

---

### Smooth elevation transitions

Applies a controlled transition from a reference elevation towards the target elevation.

Features:

- configurable transition radius;
- configurable angular diffusion sector;
- multiple interpolation profiles;
- conflict handling when several transitions overlap.

The algorithm keeps the original DEM values as a reference and only applies corrections according to the selected edge priority.

---

## Installation

### From QGIS Plugin Manager

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


