# DEMEditor
# Copyright (C) 2026 Christophe Couaillet
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

from dataclasses import dataclass


@dataclass
class ApplicationStatus:
    
    polygon_tool_active: bool = False
    selection_in_progress: bool = False
    operation_in_progress: bool = False
    has_selection: bool = False
    has_result_layer: bool = False
    syncing_tool_action: bool = False
