import bpy
from bpy.types import Operator
from bpy.props import IntProperty
from . import onion_cache, onion_drawing


class ONION_OT_AddObject(Operator):
    bl_idname = "e_motion.onion_add_object"
    bl_label = "Add Selected"
    bl_description = "Add selected objects to onion skin list"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.selected_objects
    
    def execute(self, context):
        existing = {item.object for item in context.scene.e_motion_onion_objects if item.object}
        added = 0
        
        for obj in context.selected_objects:
            if obj.type in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'ARMATURE'} and obj not in existing:
                item = context.scene.e_motion_onion_objects.add()
                item.object = obj
                item.name = obj.name
                added += 1
        
        if added > 0:
            onion_drawing.precache_frames_for_scene(context.scene)
        
        self.report({'INFO'}, f"Added {added} object(s)")
        return {'FINISHED'}


class ONION_OT_RemoveObject(Operator):
    bl_idname = "e_motion.onion_remove_object"
    bl_label = "Remove"
    bl_description = "Remove object from list"
    bl_options = {'REGISTER', 'UNDO'}
    
    index: IntProperty()
    
    def execute(self, context):
        if 0 <= self.index < len(context.scene.e_motion_onion_objects):
            context.scene.e_motion_onion_objects.remove(self.index)
            onion_cache.clear_cache()
        
        return {'FINISHED'}


class ONION_OT_RemoveSelected(Operator):
    bl_idname = "e_motion.onion_remove_selected"
    bl_label = "Remove Selected"
    bl_description = "Remove active object from list"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return len(context.scene.e_motion_onion_objects) > 0
    
    def execute(self, context):
        scene = context.scene
        index = scene.e_motion_onion_active_index
        
        if 0 <= index < len(scene.e_motion_onion_objects):
            scene.e_motion_onion_objects.remove(index)
            if index >= len(scene.e_motion_onion_objects) and len(scene.e_motion_onion_objects) > 0:
                scene.e_motion_onion_active_index = len(scene.e_motion_onion_objects) - 1
            onion_cache.clear_cache()
        
        return {'FINISHED'}


class ONION_OT_ClearAll(Operator):
    bl_idname = "e_motion.onion_clear_all"
    bl_label = "Clear All"
    bl_description = "Remove all objects from list"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        context.scene.e_motion_onion_objects.clear()
        onion_cache.clear_cache()
        return {'FINISHED'}


class ONION_OT_RefreshCache(Operator):
    bl_idname = "e_motion.onion_refresh"
    bl_label = "Refresh"
    bl_description = "Refresh onion skin cache"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        onion_drawing.precache_frames_for_scene(context.scene)
        self.report({'INFO'}, "Cache refreshed")
        return {'FINISHED'}


classes = (
    ONION_OT_AddObject,
    ONION_OT_RemoveObject,
    ONION_OT_RemoveSelected,
    ONION_OT_ClearAll,
    ONION_OT_RefreshCache,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
