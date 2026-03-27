bl_info = {
    "name": "E Motion",
    "author": "Eridanus",
    "version": (0, 0, 4),
    "blender": (3, 0, 0),
    "location": "Graph Editor > N Panel",
    "description": "Driver variable time remapping tool with curve glow effect and grid curve editor",
    "category": "Animation",
    "support": "COMMUNITY",
    "translations": [
        ("zh_CN", "Chinese"),
        ("ja_JP", "Japanese"),
        ("en_US", "English"),
        ("ru_RU", "Russian"),
    ],
}

from . import interpolation
from . import curve
from . import driver
from . import operators
from . import panel
from . import properties
from . import draw
from . import onion_cache
from . import onion_properties
from . import onion_operators
from . import onion_panel
from . import onion_drawing
from . import trajectory
from . import grid_curve_editor
from . import language


def register():
    interpolation.register()
    curve.register()
    driver.register()
    operators.register()
    panel.register()
    properties.register()
    draw.register()
    onion_cache.register()
    onion_properties.register()
    onion_operators.register()
    onion_panel.register()
    onion_drawing.register()
    trajectory.register()
    grid_curve_editor.register()
    
    import bpy
    bpy.app.driver_namespace['em_time'] = driver.em_time
    bpy.app.driver_namespace['em_eval'] = driver.em_eval


def unregister():
    grid_curve_editor.unregister()
    trajectory.unregister()
    onion_drawing.unregister()
    onion_panel.unregister()
    onion_operators.unregister()
    onion_properties.unregister()
    onion_cache.unregister()
    draw.unregister()
    properties.unregister()
    panel.unregister()
    operators.unregister()
    driver.unregister()
    curve.unregister()
    interpolation.unregister()
    
    import bpy
    if 'em_time' in bpy.app.driver_namespace:
        del bpy.app.driver_namespace['em_time']
    if 'em_eval' in bpy.app.driver_namespace:
        del bpy.app.driver_namespace['em_eval']


if __name__ == "__main__":
    register()
