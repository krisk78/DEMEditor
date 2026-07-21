from dataclasses import dataclass


@dataclass
class ApplicationStatus:
    
    polygon_tool_active: bool = False
    selection_in_progress: bool = False
    operation_in_progress: bool = False
    has_selection: bool = False
    has_result_layer: bool = False
    syncing_tool_action: bool = False
