import bpy
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, IntProperty, PointerProperty, StringProperty


def update_settings(self, context):
    from . import onion_drawing
    onion_drawing.precache_frames_for_scene(context.scene)


class ONION_ObjectItem(PropertyGroup):
    name: StringProperty(
        name="Name",
        default=""
    )
    
    object: PointerProperty(
        name="Object",
        type=bpy.types.Object,
        description="Object to display onion skin for"
    )
    visible: BoolProperty(
        name="Visible",
        description="Show onion skin for this object",
        default=True,
        update=update_settings
    )


class ONION_Settings(PropertyGroup):
    enabled: BoolProperty(
        name="Enable",
        description="Toggle onion skin display",
        default=False,
        update=update_settings
    )
    
    frame_start: IntProperty(
        name="Before",
        description="Number of frames before current frame (past frames, shown in red)",
        default=10,
        min=0,
        update=update_settings
    )
    
    frame_end: IntProperty(
        name="After",
        description="Number of frames after current frame (future frames, shown in blue)",
        default=10,
        min=0,
        update=update_settings
    )
    
    frame_step: IntProperty(
        name="Step",
        description="Frame interval between onion skins",
        default=5,
        min=1,
        soft_max=20,
        update=update_settings
    )
    
    use_wireframe: BoolProperty(
        name="Wireframe",
        description="Draw onion skins as wireframe",
        default=False,
        update=update_settings
    )
    
    include_children: BoolProperty(
        name="Include Children",
        description="Include mesh children of armatures",
        default=True,
        update=update_settings
    )


def register():
    bpy.utils.register_class(ONION_ObjectItem)
    bpy.utils.register_class(ONION_Settings)
    
    bpy.types.Scene.e_motion_onion_settings = PointerProperty(type=ONION_Settings)
    bpy.types.Scene.e_motion_onion_objects = bpy.props.CollectionProperty(type=ONION_ObjectItem)
    bpy.types.Scene.e_motion_onion_active_index = bpy.props.IntProperty(name="Active Index")


def unregister():
    del bpy.types.Scene.e_motion_onion_active_index
    del bpy.types.Scene.e_motion_onion_objects
    del bpy.types.Scene.e_motion_onion_settings
    
    bpy.utils.unregister_class(ONION_Settings)
    bpy.utils.unregister_class(ONION_ObjectItem)
