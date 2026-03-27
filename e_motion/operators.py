import bpy
from .driver import get_cache, refresh_driver_cache, apply_driver_expression, reset_driver_expression
from . import draw


class OBJECT_OT_RefreshVariables(bpy.types.Operator):
    bl_idname = "graph.refresh_driver_vars"
    bl_label = "Refresh Variables"
    bl_description = "Refresh driver variables from active object"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        
        if not obj:
            self.report({'WARNING'}, "No active object")
            return {'CANCELLED'}
        
        if not obj.animation_data:
            self.report({'WARNING'}, "Object has no animation data")
            return {'CANCELLED'}
        
        drivers = list(obj.animation_data.drivers)
        if not drivers:
            self.report({'WARNING'}, "Object has no drivers")
            return {'CANCELLED'}
        
        variables = refresh_driver_cache(obj)
        context.scene.e_motion_obj_name = obj.name
        
        if variables:
            animated_count = sum(1 for v in variables if v.curve and v.curve.keyframes)
            self.report({'INFO'}, f"Found {len(variables)} vars, {animated_count} animated")
        else:
            self.report({'WARNING'}, "No driver variables found")
            return {'CANCELLED'}
        
        return {'FINISHED'}


class OBJECT_OT_ApplyTimeExpr(bpy.types.Operator):
    bl_idname = "graph.apply_time_expr"
    bl_label = "Apply"
    bl_description = "Apply time expression to variable"
    bl_options = {'REGISTER', 'UNDO'}
    
    var_name: bpy.props.StringProperty(default="")
    
    def execute(self, context):
        cache = get_cache()
        scene = context.scene
        obj_name = scene.e_motion_obj_name
        
        if not obj_name or obj_name not in cache["var_cache"]:
            self.report({'WARNING'}, "Please refresh variables first")
            return {'CANCELLED'}
        
        variables = cache["var_cache"][obj_name]
        
        target_var = None
        for var in variables:
            if var.name == self.var_name:
                target_var = var
                break
        
        if not target_var:
            self.report({'WARNING'}, f"Variable '{self.var_name}' not found")
            return {'CANCELLED'}
        
        if not target_var.curve:
            self.report({'WARNING'}, f"Variable '{self.var_name}' has no animation curve")
            return {'CANCELLED'}
        
        if not target_var.curve.keyframes or len(target_var.curve.keyframes) == 0:
            self.report({'WARNING'}, f"Variable '{self.var_name}' curve has no keyframes")
            return {'CANCELLED'}
        
        time_expr = scene.e_motion_time_expr
        if not time_expr:
            self.report({'WARNING'}, "Please enter a time expression")
            return {'CANCELLED'}
        
        frame = context.scene.frame_current
        from .driver import TimeExpressionParser
        new_time = TimeExpressionParser.parse(time_expr, frame)
        
        new_value = target_var.curve.get_value(float(new_time))
        
        scene.e_motion_result_var = self.var_name
        scene.e_motion_result_time = new_time
        scene.e_motion_result_value = new_value
        
        self.report({'INFO'}, f"{self.var_name} @ frame {new_time} = {new_value:.4f}")
        
        return {'FINISHED'}


class OBJECT_OT_ApplyToDriver(bpy.types.Operator):
    bl_idname = "graph.apply_to_driver"
    bl_label = "Apply to Driver"
    bl_description = "Modify driver expression to use em_time function"
    bl_options = {'REGISTER', 'UNDO'}
    
    var_name: bpy.props.StringProperty(default="")
    
    def execute(self, context):
        scene = context.scene
        obj_name = scene.e_motion_obj_name
        
        if not obj_name:
            self.report({'WARNING'}, "Please refresh variables first")
            return {'CANCELLED'}
        
        obj = bpy.data.objects.get(obj_name)
        if not obj or not obj.animation_data:
            self.report({'WARNING'}, "Object not found or no animation data")
            return {'CANCELLED'}
        
        time_expr = scene.e_motion_time_expr
        if not time_expr:
            self.report({'WARNING'}, "Please enter a time expression")
            return {'CANCELLED'}
        
        modified_count = apply_driver_expression(obj, time_expr)
        
        if modified_count > 0:
            self.report({'INFO'}, f"Modified {modified_count} driver expression(s)")
        else:
            self.report({'WARNING'}, "No drivers modified")
            return {'CANCELLED'}
        
        return {'FINISHED'}


class OBJECT_OT_ResetDriver(bpy.types.Operator):
    bl_idname = "graph.reset_driver"
    bl_label = "Reset Driver"
    bl_description = "Reset driver expression to use original variable"
    bl_options = {'REGISTER', 'UNDO'}
    
    var_name: bpy.props.StringProperty(default="")
    
    def execute(self, context):
        scene = context.scene
        obj_name = scene.e_motion_obj_name
        
        if not obj_name:
            self.report({'WARNING'}, "No object selected")
            return {'CANCELLED'}
        
        obj = bpy.data.objects.get(obj_name)
        if not obj or not obj.animation_data:
            self.report({'WARNING'}, "Object not found or no animation data")
            return {'CANCELLED'}
        
        reset_count = reset_driver_expression(obj)
        
        if reset_count > 0:
            self.report({'INFO'}, f"Reset {reset_count} driver expression(s)")
        else:
            self.report({'WARNING'}, "No drivers to reset")
            return {'CANCELLED'}
        
        return {'FINISHED'}


class OBJECT_OT_ToggleCurveGlow(bpy.types.Operator):
    bl_idname = "graph.toggle_curve_glow"
    bl_label = "Toggle Curve Glow"
    bl_description = "Toggle rainbow glow effect for selected curves"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        scene = context.scene
        scene.e_motion_curve_glow = not scene.e_motion_curve_glow
        
        if scene.e_motion_curve_glow:
            draw.register_glow()
            self.report({'INFO'}, "Curve glow enabled")
        else:
            draw.unregister_glow()
            self.report({'INFO'}, "Curve glow disabled")
        
        return {'FINISHED'}


class OBJECT_OT_DeleteEmptyCurves(bpy.types.Operator):
    bl_idname = "graph.delete_empty_curves"
    bl_label = "Delete Empty Curves"
    bl_description = "Delete animation curves with constant values"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        def delete_nonuse(fcu, epsilon=1e-6):
            # 检查曲线是否有修改器，如果有则保留
            if hasattr(fcu, 'modifiers') and fcu.modifiers:
                return False
            if not fcu.keyframe_points:
                return True
            constant_val = fcu.keyframe_points[0].co[1]
            for kp in fcu.keyframe_points:
                if abs(kp.co[1] - constant_val) > epsilon:
                    return False
            return True
        
        obj = context.active_object
        if not obj or not obj.animation_data:
            self.report({'WARNING'}, "No animation data")
            return {'CANCELLED'}
        
        deleted_count = 0
        
        if obj.animation_data.action:
            action = obj.animation_data.action
            curves_to_delete = [fcu for fcu in action.fcurves if delete_nonuse(fcu)]
            for fcu in reversed(curves_to_delete):
                action.fcurves.remove(fcu)
                deleted_count += 1
        
        drivers_to_delete = [fcu for fcu in obj.animation_data.drivers if delete_nonuse(fcu)]
        for fcu in reversed(drivers_to_delete):
            obj.animation_data.drivers.remove(fcu)
            deleted_count += 1
        
        self.report({'INFO'}, f"Deleted {deleted_count} empty curves")
        return {'FINISHED'}


class OBJECT_OT_DeleteAllModifiers(bpy.types.Operator):
    bl_idname = "graph.delete_all_modifiers"
    bl_label = "Delete All Modifiers"
    bl_description = "Delete all modifiers from selected animation curves"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        if not obj or not obj.animation_data:
            self.report({'WARNING'}, "No animation data")
            return {'CANCELLED'}
        
        deleted_count = 0
        
        if obj.animation_data.action:
            action = obj.animation_data.action
            for fcu in action.fcurves:
                if hasattr(fcu, 'modifiers'):
                    while fcu.modifiers:
                        fcu.modifiers.remove(fcu.modifiers[-1])
                        deleted_count += 1
        
        self.report({'INFO'}, f"Deleted {deleted_count} modifiers")
        return {'FINISHED'}


classes = (
    OBJECT_OT_RefreshVariables,
    OBJECT_OT_ApplyTimeExpr,
    OBJECT_OT_ApplyToDriver,
    OBJECT_OT_ResetDriver,
    OBJECT_OT_ToggleCurveGlow,
    OBJECT_OT_DeleteEmptyCurves,
    OBJECT_OT_DeleteAllModifiers,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
