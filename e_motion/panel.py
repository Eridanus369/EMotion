import bpy
from .driver import get_cache
from .language import _


class GRAPH_OT_emo_jump_to_endpoint(bpy.types.Operator):
    bl_idname = "graph.emo_jump_to_endpoint"
    bl_label = "Jump to Endpoint"
    bl_description = "Jump to start or end of animation"
    bl_options = {'REGISTER'}
    
    end: bpy.props.BoolProperty(
        name="End",
        default=False,
        description="Jump to end if True, start if False"
    )
    
    def execute(self, context):
        bpy.ops.screen.frame_jump(end=self.end)
        return {'FINISHED'}


class GRAPH_PT_EMotionPanel(bpy.types.Panel):
    bl_label = _("E_Motion")
    bl_idname = "GRAPH_PT_e_motion"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = "E_Motion"
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        if space and space.type == 'GRAPH_EDITOR':
            if hasattr(space, 'mode') and space.mode == 'DRIVERS':
                return True
        return False
    
    def draw(self, context):
        cache = get_cache()
        layout = self.layout
        scene = context.scene
        
        obj = context.active_object
        
        if not obj:
            layout.label(text=_('No active object'))
            return
        
        if not obj.animation_data or not obj.animation_data.drivers:
            layout.label(text=_('Object has no drivers'))
            return
        
        obj_name = obj.name
        layout.label(text=_('Object') + f": {obj_name}", icon='OBJECT_DATA')
        
        saved_expr = cache["obj_expr"].get(obj_name, "")
        if saved_expr:
            layout.label(text=_('Expr') + f": {saved_expr}", icon='TIME')
        
        layout.separator()
        
        if obj_name not in cache["var_cache"]:
            layout.operator("graph.refresh_driver_vars", icon='FILE_REFRESH')
            return
        
        variables = cache["var_cache"].get(obj_name, [])
        if not variables:
            layout.operator("graph.refresh_driver_vars", icon='FILE_REFRESH')
            return
        
        layout.label(text=_('Variables') + f" ({len(variables)}):")
        
        for var in variables:
            col = layout.column(align=True)
            row = col.row(align=True)
            
            if var.curve and var.curve.keyframes:
                row.label(text=var.name, icon='ANIM')
                row.label(text=f"[{var.VARIABLE_TYPES.get(var.var_type, var.var_type)}]")
                
                t_min = var.curve.keyframes[0][0]
                t_max = var.curve.keyframes[-1][0]
                col.label(text=_('Range') + f": {t_min:.0f} - {t_max:.0f}")
            else:
                row.label(text=var.name, icon='DOT')
                row.label(text=f"[{var.VARIABLE_TYPES.get(var.var_type, var.var_type)}]")
        
        layout.separator()
        
        layout.label(text=_('Time Expression:'), icon='TIME')
        row = layout.row(align=True)
        row.prop(scene, "e_motion_time_expr", text="")
        
        layout.separator()
        
        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator("graph.apply_to_driver", text=_('Apply'), icon='PLAY')
        row.operator("graph.reset_driver", text=_('Reset'), icon='X')
        
        layout.separator()
        
        layout.operator("graph.refresh_driver_vars", icon='FILE_REFRESH')


class GRAPH_PT_EMotionCurvePanel(bpy.types.Panel):
    bl_label = _("E_Motion Tools")
    bl_idname = "GRAPH_PT_e_motion_curve"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = "E_Motion"
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        if space and space.type == 'GRAPH_EDITOR':
            if hasattr(space, 'mode') and space.mode == 'FCURVES':
                return True
        return False
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        layout.label(text=_("Curve Glow"), icon='PARTICLES')
        row = layout.row(align=True)
        
        glow_text = _("Disable Glow") if scene.e_motion_curve_glow else _("Enable Glow")
        row.operator("graph.toggle_curve_glow", text=glow_text, 
                     icon='PLAY' if not scene.e_motion_curve_glow else 'PAUSE')
        
        layout.separator()
        
        layout.label(text=_("Curve Tools"), icon='CURVE_DATA')
        col = layout.column(align=True)
        col.operator("graph.delete_empty_curves", text=_("Delete Empty Curves"), icon='X')
        col.operator("graph.delete_all_modifiers", text=_("Delete All Modifiers"), icon='X')
        
        layout.separator()
        
        # 帧控制
        layout.label(text=_("Frame Control"), icon='TIME')
        
        # 输入帧
        row = layout.row(align=True)
        row.prop(context.scene, "frame_current", text=_("Current Frame"))
        
        # 跳转到端点位置
        row = layout.row(align=True)
        row.operator("graph.emo_jump_to_endpoint", text=_("Jump to Start"), icon='TRIA_LEFT').end = False
        row.operator("graph.emo_jump_to_endpoint", text=_("Jump to End"), icon='TRIA_RIGHT').end = True


class PREFERENCES_PT_e_motion_language(bpy.types.AddonPreferences):
    bl_idname = "e_motion"
    
    def update_language(self, context):
        # 当语言更改时，触发界面刷新
        for area in context.screen.areas:
            area.tag_redraw()
    
    language: bpy.props.EnumProperty(
        name="Language",
        description="Select language for UI",
        items=[
            ('zh_CN', '中文', 'Chinese'),
            ('en_US', 'English', 'English'),
            ('ja_JP', '日本語', 'Japanese'),
            ('ru_RU', 'Русский', 'Russian'),
        ],
        default='zh_CN',
        update=update_language
    )
    
    def draw(self, context):
        layout = self.layout
        
        # 语言设置
        layout.label(text=_('Language Settings'), icon='PREFERENCES')
        layout.prop(self, "language", text=_('Language'))


classes = (
    GRAPH_OT_emo_jump_to_endpoint,
    GRAPH_PT_EMotionPanel,
    GRAPH_PT_EMotionCurvePanel,
    PREFERENCES_PT_e_motion_language,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
