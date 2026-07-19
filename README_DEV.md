# VSCode development configuration

The recommended development environment is:

- Create a virtual environment using the Python interpreter shipped with QGIS/OSGeo4W:
  `OSGeo4W/apps/Python312/python.exe`

- Add QGIS Python paths to the virtual environment.

  Create the file:

      .venv/Lib/site-packages/qgis.pth

  with the following content (adapt paths to your QGIS installation):

      C:\OSGeo4W\apps\qgis\python
      C:\OSGeo4W\apps\Python312\Lib\site-packages

- For PyQt6 static analysis, install or provide PyQt6 stubs if required by your IDE.

- If using VSCode/Pylance, add the QGIS Python paths to:
  
      .vscode/settings.json

  Example:

      "python.analysis.extraPaths": [
          "C:/OSGeo4W/apps/qgis/python",
          "C:/OSGeo4W/apps/Python312/Lib/site-packages"
      ]

## Compatibility

The plugin has been tested on a QGIS 4 environment.
No compatibility with previous QGIS versions is guaranteed.
