VSCode configuration:
- venv with python.exe from OSGeo4W/apps/Python312
- a folder typings/PyQt6 at the root of the project with all .pyi copied from OSGeo4W/apps/Python312/Lib/site-packages/PyQt6
- extra paths added to .vscode/settings.json:
    "python.analysis.extraPaths": [
        "C:/OSGeo4W/apps/qgis/python",
        "C:/OSGeo4W/apps/Python312/Lib/site-packages"
    ]
