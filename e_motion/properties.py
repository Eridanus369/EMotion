import bpy


def register():
    bpy.types.Scene.e_motion_obj_name = bpy.props.StringProperty(
        name="Object Name",
        default=""
    )
    
    bpy.types.Scene.e_motion_time_expr = bpy.props.StringProperty(
        name="Time Expression",
        description="Time expression for variable remapping",
        default=""
    )
    
    bpy.types.Scene.e_motion_result_var = bpy.props.StringProperty(
        name="Result Variable",
        default=""
    )
    
    bpy.types.Scene.e_motion_result_time = bpy.props.IntProperty(
        name="Result Time",
        default=0
    )
    
    bpy.types.Scene.e_motion_result_value = bpy.props.FloatProperty(
        name="Result Value",
        default=0.0
    )
    
    bpy.types.Scene.e_motion_curve_glow = bpy.props.BoolProperty(
        name="Curve Glow",
        description="Enable rainbow glow effect for selected curves",
        default=False
    )
    



def unregister():
    del bpy.types.Scene.e_motion_obj_name
    del bpy.types.Scene.e_motion_time_expr
    del bpy.types.Scene.e_motion_result_var
    del bpy.types.Scene.e_motion_result_time
    del bpy.types.Scene.e_motion_result_value
    del bpy.types.Scene.e_motion_curve_glow
