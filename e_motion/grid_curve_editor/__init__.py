import bpy
from .properties import register as register_properties, unregister as unregister_properties
from .generator import register as register_generator, unregister as unregister_generator
from .draw import register as register_draw, unregister as unregister_draw
from .operators import register as register_operators, unregister as unregister_operators
from .quick_operators import register as register_quick_ops, unregister as unregister_quick_ops
from .ui import register as register_ui, unregister as unregister_ui
from .bezier_editor import register as register_bezier, unregister as unregister_bezier


def register():
    register_properties()
    register_generator()
    register_draw()
    register_operators()
    register_quick_ops()
    register_ui()
    register_bezier()
    print("[E_Motion] Grid curve editor registered")


def unregister():
    unregister_bezier()
    unregister_ui()
    unregister_quick_ops()
    unregister_operators()
    unregister_draw()
    unregister_generator()
    unregister_properties()
    print("[E_Motion] Grid curve editor unregistered")
