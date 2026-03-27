import bpy
from bpy.types import Operator
from .properties import get_grid_cache, cell_to_frame
from .generator import ModifierPresetGenerator


class GRAPH_OT_emo_quick_constant(Operator):
    bl_idname = "graph.emo_quick_constant"
    bl_label = "Quick Constant"
    bl_description = "Apply constant modifier to selected cells"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        cache = get_grid_cache()
        selected_cells = cache.get('selected_cells', [])
        
        if not selected_cells:
            self.report({'WARNING'}, "No cells selected")
            return {'CANCELLED'}
        
        obj = context.active_object
        if not obj or not obj.animation_data or not obj.animation_data.action:
            self.report({'WARNING'}, "No active object with animation")
            return {'CANCELLED'}
        
        preset = context.scene.emo_modifier_preset
        preset.preset_type = 'CONSTANT'
        
        props = context.scene.emo_grid_props
        
        min_x = min(cell[0] for cell in selected_cells)
        max_x = max(cell[0] for cell in selected_cells)
        
        start_frame = cell_to_frame(min_x, props)
        end_frame = cell_to_frame(max_x + 1, props)
        cell_range = (start_frame, end_frame)
        
        fcurves = [fcu for fcu in obj.animation_data.action.fcurves if fcu.select]
        if not fcurves:
            fcurves = obj.animation_data.action.fcurves
        
        for fcu in fcurves:
            ModifierPresetGenerator.remove_overlapping_modifiers(fcu, start_frame, end_frame)
            ModifierPresetGenerator.apply_preset(fcu, preset, cell_range)
            ModifierPresetGenerator.remove_zero_range_modifiers(fcu)
        
        context.area.tag_redraw()
        self.report({'INFO'}, f"Applied constant to frames {start_frame:.0f}-{end_frame:.0f}")
        return {'FINISHED'}


class GRAPH_OT_emo_quick_linear_pos(Operator):
    bl_idname = "graph.emo_quick_linear_pos"
    bl_label = "Quick Linear Positive"
    bl_description = "Apply positive linear modifier to selected cells"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        cache = get_grid_cache()
        selected_cells = cache.get('selected_cells', [])
        
        if not selected_cells:
            self.report({'WARNING'}, "No cells selected")
            return {'CANCELLED'}
        
        obj = context.active_object
        if not obj or not obj.animation_data or not obj.animation_data.action:
            self.report({'WARNING'}, "No active object with animation")
            return {'CANCELLED'}
        
        preset = context.scene.emo_modifier_preset
        preset.preset_type = 'LINEAR_POS'
        
        props = context.scene.emo_grid_props
        
        min_x = min(cell[0] for cell in selected_cells)
        max_x = max(cell[0] for cell in selected_cells)
        
        start_frame = cell_to_frame(min_x, props)
        end_frame = cell_to_frame(max_x + 1, props)
        cell_range = (start_frame, end_frame)
        
        fcurves = [fcu for fcu in obj.animation_data.action.fcurves if fcu.select]
        if not fcurves:
            fcurves = obj.animation_data.action.fcurves
        
        for fcu in fcurves:
            ModifierPresetGenerator.remove_overlapping_modifiers(fcu, start_frame, end_frame)
            ModifierPresetGenerator.apply_preset(fcu, preset, cell_range)
            ModifierPresetGenerator.remove_zero_range_modifiers(fcu)
        
        context.area.tag_redraw()
        self.report({'INFO'}, f"Applied positive linear to frames {start_frame:.0f}-{end_frame:.0f}")
        return {'FINISHED'}


class GRAPH_OT_emo_quick_linear_neg(Operator):
    bl_idname = "graph.emo_quick_linear_neg"
    bl_label = "Quick Linear Negative"
    bl_description = "Apply negative linear modifier to selected cells"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        cache = get_grid_cache()
        selected_cells = cache.get('selected_cells', [])
        
        if not selected_cells:
            self.report({'WARNING'}, "No cells selected")
            return {'CANCELLED'}
        
        obj = context.active_object
        if not obj or not obj.animation_data or not obj.animation_data.action:
            self.report({'WARNING'}, "No active object with animation")
            return {'CANCELLED'}
        
        preset = context.scene.emo_modifier_preset
        preset.preset_type = 'LINEAR_NEG'
        
        props = context.scene.emo_grid_props
        
        min_x = min(cell[0] for cell in selected_cells)
        max_x = max(cell[0] for cell in selected_cells)
        
        start_frame = cell_to_frame(min_x, props)
        end_frame = cell_to_frame(max_x + 1, props)
        cell_range = (start_frame, end_frame)
        
        fcurves = [fcu for fcu in obj.animation_data.action.fcurves if fcu.select]
        if not fcurves:
            fcurves = obj.animation_data.action.fcurves
        
        for fcu in fcurves:
            ModifierPresetGenerator.remove_overlapping_modifiers(fcu, start_frame, end_frame)
            ModifierPresetGenerator.apply_preset(fcu, preset, cell_range)
            ModifierPresetGenerator.remove_zero_range_modifiers(fcu)
        
        context.area.tag_redraw()
        self.report({'INFO'}, f"Applied negative linear to frames {start_frame:.0f}-{end_frame:.0f}")
        return {'FINISHED'}


class GRAPH_OT_emo_quick_full_sine(Operator):
    bl_idname = "graph.emo_quick_full_sine"
    bl_label = "Quick Full Sine"
    bl_description = "Apply full sine wave modifier to selected cells"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        cache = get_grid_cache()
        selected_cells = cache.get('selected_cells', [])
        
        if not selected_cells:
            self.report({'WARNING'}, "No cells selected")
            return {'CANCELLED'}
        
        obj = context.active_object
        if not obj or not obj.animation_data or not obj.animation_data.action:
            self.report({'WARNING'}, "No active object with animation")
            return {'CANCELLED'}
        
        preset = context.scene.emo_modifier_preset
        preset.preset_type = 'SINE_FULL'
        preset.amplitude = 1.0
        preset.phase = 0.0
        
        props = context.scene.emo_grid_props
        
        min_x = min(cell[0] for cell in selected_cells)
        max_x = max(cell[0] for cell in selected_cells)
        
        start_frame = cell_to_frame(min_x, props)
        end_frame = cell_to_frame(max_x + 1, props)
        cell_range = (start_frame, end_frame)
        
        fcurves = [fcu for fcu in obj.animation_data.action.fcurves if fcu.select]
        if not fcurves:
            fcurves = obj.animation_data.action.fcurves
        
        for fcu in fcurves:
            ModifierPresetGenerator.remove_overlapping_modifiers(fcu, start_frame, end_frame)
            ModifierPresetGenerator.apply_preset(fcu, preset, cell_range)
            ModifierPresetGenerator.remove_zero_range_modifiers(fcu)
        
        context.area.tag_redraw()
        self.report({'INFO'}, f"Applied full sine to frames {start_frame:.0f}-{end_frame:.0f}")
        return {'FINISHED'}


class GRAPH_OT_emo_quick_sine_bottom(Operator):
    bl_idname = "graph.emo_quick_sine_bottom"
    bl_label = "Quick Half Sine Bottom"
    bl_description = "Apply bottom half sine modifier to selected cells"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        cache = get_grid_cache()
        selected_cells = cache.get('selected_cells', [])
        
        if not selected_cells:
            self.report({'WARNING'}, "No cells selected")
            return {'CANCELLED'}
        
        obj = context.active_object
        if not obj or not obj.animation_data or not obj.animation_data.action:
            self.report({'WARNING'}, "No active object with animation")
            return {'CANCELLED'}
        
        preset = context.scene.emo_modifier_preset
        preset.preset_type = 'SINE_BOTTOM'
        preset.amplitude = 1.0
        
        props = context.scene.emo_grid_props
        
        min_x = min(cell[0] for cell in selected_cells)
        max_x = max(cell[0] for cell in selected_cells)
        
        start_frame = cell_to_frame(min_x, props)
        end_frame = cell_to_frame(max_x + 1, props)
        cell_range = (start_frame, end_frame)
        
        fcurves = [fcu for fcu in obj.animation_data.action.fcurves if fcu.select]
        if not fcurves:
            fcurves = obj.animation_data.action.fcurves
        
        for fcu in fcurves:
            ModifierPresetGenerator.remove_overlapping_modifiers(fcu, start_frame, end_frame)
            ModifierPresetGenerator.apply_preset(fcu, preset, cell_range)
            ModifierPresetGenerator.remove_zero_range_modifiers(fcu)
        
        context.area.tag_redraw()
        self.report({'INFO'}, f"Applied half sine bottom to frames {start_frame:.0f}-{end_frame:.0f}")
        return {'FINISHED'}


class GRAPH_OT_emo_quick_sine_top(Operator):
    bl_idname = "graph.emo_quick_sine_top"
    bl_label = "Quick Half Sine Top"
    bl_description = "Apply top half sine modifier to selected cells"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        cache = get_grid_cache()
        selected_cells = cache.get('selected_cells', [])
        
        if not selected_cells:
            self.report({'WARNING'}, "No cells selected")
            return {'CANCELLED'}
        
        obj = context.active_object
        if not obj or not obj.animation_data or not obj.animation_data.action:
            self.report({'WARNING'}, "No active object with animation")
            return {'CANCELLED'}
        
        preset = context.scene.emo_modifier_preset
        preset.preset_type = 'SINE_TOP'
        preset.amplitude = 1.0
        
        props = context.scene.emo_grid_props
        
        min_x = min(cell[0] for cell in selected_cells)
        max_x = max(cell[0] for cell in selected_cells)
        
        start_frame = cell_to_frame(min_x, props)
        end_frame = cell_to_frame(max_x + 1, props)
        cell_range = (start_frame, end_frame)
        
        fcurves = [fcu for fcu in obj.animation_data.action.fcurves if fcu.select]
        if not fcurves:
            fcurves = obj.animation_data.action.fcurves
        
        for fcu in fcurves:
            ModifierPresetGenerator.remove_overlapping_modifiers(fcu, start_frame, end_frame)
            ModifierPresetGenerator.apply_preset(fcu, preset, cell_range)
            ModifierPresetGenerator.remove_zero_range_modifiers(fcu)
        
        context.area.tag_redraw()
        self.report({'INFO'}, f"Applied half sine top to frames {start_frame:.0f}-{end_frame:.0f}")
        return {'FINISHED'}


classes = (
    GRAPH_OT_emo_quick_constant,
    GRAPH_OT_emo_quick_linear_pos,
    GRAPH_OT_emo_quick_linear_neg,
    GRAPH_OT_emo_quick_full_sine,
    GRAPH_OT_emo_quick_sine_bottom,
    GRAPH_OT_emo_quick_sine_top,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
