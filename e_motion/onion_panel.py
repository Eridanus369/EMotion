import bpy
from bpy.types import Panel
from .language import _


class ONION_PT_MainPanel(Panel):
    bl_label = _("Onion Skin")
    bl_idname = "ONION_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'E_Motion'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.e_motion_onion_settings
        
        row = layout.row()
        row.prop(settings, "enabled", text=_('Enable Onion Skin'))
        
        if not settings.enabled:
            return
        
        box = layout.box()
        box.label(text=_('Frame Range (from current)'), icon='TIME')
        
        row = box.row(align=True)
        row.prop(settings, "frame_start", text=_('Before'))
        row.prop(settings, "frame_end", text=_('After'))
        
        row = box.row()
        row.prop(settings, "frame_step", text=_('Step'))
        
        box = layout.box()
        box.label(text=_('Display Options'), icon='VIS_SEL_11')
        
        row = box.row()
        row.prop(settings, "use_wireframe", text=_('Wireframe'))
        
        row = box.row()
        row.prop(settings, "include_children", text=_('Include Children'))
        
        box = layout.box()
        row = box.row()
        row.template_list(
            "UI_UL_list",
            "onion_objects",
            scene,
            "e_motion_onion_objects",
            scene,
            "e_motion_onion_active_index",
            rows=4
        )
        
        col = row.column(align=True)
        col.operator("e_motion.onion_add_object", icon='ADD', text="")
        col.operator("e_motion.onion_remove_selected", icon='REMOVE', text="")
        col.operator("e_motion.onion_clear_all", icon='X', text="")
        
        row = box.row()
        row.operator("e_motion.onion_refresh", icon='FILE_REFRESH', text=_('Refresh Cache'))
        
        if scene.e_motion_onion_objects:
            active_index = scene.e_motion_onion_active_index
            if 0 <= active_index < len(scene.e_motion_onion_objects):
                item = scene.e_motion_onion_objects[active_index]
                if item.object:
                    box = layout.box()
                    box.label(text=_('Selected') + f": {item.object.name}", icon='OBJECT_DATA')
                    row = box.row()
                    row.prop(item, "visible", text=_('Visible'))


classes = (
    ONION_PT_MainPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
