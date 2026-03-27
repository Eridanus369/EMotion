import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from .language import _

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

_trajectory_cache = {}
_point_cache = {}
_line_shader = None
_point_shader = None

TRAJECTORY_COLORS = [
    (1.0, 0.4, 0.7),
    (0.3, 0.8, 0.4),
    (0.4, 0.6, 1.0),
    (1.0, 0.8, 0.2),
    (0.8, 0.4, 1.0),
    (0.2, 0.9, 0.9),
    (1.0, 0.5, 0.2),
    (0.6, 0.9, 0.3),
]


def get_line_shader():
    global _line_shader
    if _line_shader is None:
        _line_shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    return _line_shader


def get_point_shader():
    global _point_shader
    _point_shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    return _point_shader


def clear_trajectory_cache():
    global _trajectory_cache, _point_cache
    _trajectory_cache = {}
_point_cache = {}


def get_object_position_at_frame(obj, depsgraph, trajectory_type, vgroup_name=""):
    obj_eval = obj.evaluated_get(depsgraph)
    
    if trajectory_type == 'ORIGIN':
        return obj_eval.matrix_world.translation.copy()
    
    elif trajectory_type == 'CENTER':
        mesh = obj_eval.to_mesh()
        if not mesh or len(mesh.vertices) == 0:
            obj_eval.to_mesh_clear()
            return obj_eval.matrix_world.translation.copy()
        
        if HAS_NUMPY:
            num_verts = len(mesh.vertices)
            verts_co = np.empty(num_verts * 3, dtype=np.float32)
            mesh.vertices.foreach_get('co', verts_co)
            verts_co = verts_co.reshape(-1, 3)
            center = np.mean(verts_co, axis=0)
            obj_eval.to_mesh_clear()
            return obj_eval.matrix_world @ Vector(center)
        else:
            total = Vector((0, 0, 0))
            count = 0
            for v in mesh.vertices:
                total += v.co
                count += 1
            obj_eval.to_mesh_clear()
            if count > 0:
                return obj_eval.matrix_world @ (total / count)
            return obj_eval.matrix_world.translation.copy()
    
    elif trajectory_type == 'VERTEX_GROUP' and vgroup_name:
        mesh = obj_eval.to_mesh()
        if not mesh or len(mesh.vertices) == 0:
            obj_eval.to_mesh_clear()
            return None
        
        vgroup_index = None
        for vg in obj.vertex_groups:
            if vg.name == vgroup_name:
                vgroup_index = vg.index
                break
        
        if vgroup_index is None:
            obj_eval.to_mesh_clear()
            return None
        
        total = Vector((0, 0, 0))
        count = 0
        for v in mesh.vertices:
            for g in v.groups:
                if g.group == vgroup_index and g.weight > 0.001:
                    total += v.co
                    count += 1
                    break
        
        obj_eval.to_mesh_clear()
        if count > 0:
            return obj_eval.matrix_world @ (total / count)
        return None
    
    return None


def calculate_trajectory(scene, obj, item_settings, global_settings):
    import bpy
    
    start_frame = global_settings.trajectory_start
    end_frame = global_settings.trajectory_end
    point_step = global_settings.trajectory_point_step
    
    trajectory_type = item_settings.trajectory_type
    vgroup_name = item_settings.trajectory_vgroup if trajectory_type == 'VERTEX_GROUP' else ""
    
    points = []
    point_frames = []
    
    original_frame = scene.frame_current
    
    for frame in range(start_frame, end_frame + 1):
        scene.frame_set(frame, subframe=0.0)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        
        pos = get_object_position_at_frame(obj, depsgraph, trajectory_type, vgroup_name)
        if pos:
            points.append((frame, pos))
            if point_step > 0 and (frame - start_frame) % point_step == 0:
                point_frames.append((frame, pos))
    
    scene.frame_set(original_frame, subframe=0.0)
    
    return points, point_frames


def build_trajectory_cache(scene):
    if not hasattr(scene, 'e_motion_trajectory_settings'):
        return
    
    settings = scene.e_motion_trajectory_settings
    if not settings.enabled:
        return
    
    if not scene.e_motion_trajectory_objects:
        return
    
    clear_trajectory_cache()
    
    color_index = 0
    
    for item in scene.e_motion_trajectory_objects:
        obj = item.object
        if not obj or not item.visible:
            continue
        
        if obj.type not in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'ARMATURE'}:
            continue
        
        points, point_frames = calculate_trajectory(scene, obj, item, settings)
        
        if points:
            color = TRAJECTORY_COLORS[color_index % len(TRAJECTORY_COLORS)]
            _trajectory_cache[obj.name] = {
                'points': points,
                'point_frames': point_frames,
                'color': color
            }
            color_index += 1


def draw_trajectories():
    context = bpy.context
    
    if not context.area or context.area.type != 'VIEW_3D':
        return
    
    scene = context.scene
    if not hasattr(scene, 'e_motion_trajectory_settings'):
        return
    
    settings = scene.e_motion_trajectory_settings
    if not settings.enabled:
        return
    
    if not _trajectory_cache:
        return
    
    shader = get_line_shader()
    gpu.state.blend_set('ALPHA')
    gpu.state.depth_test_set('LESS_EQUAL')
    gpu.state.depth_mask_set(False)
    
    shader.bind()
    
    for obj_name, data in _trajectory_cache.items():
        points = data['points']
        color = data['color']
        point_frames = data['point_frames']
        
        if len(points) < 2:
            continue
        
        sorted_points = sorted(points, key=lambda x: x[0])
        
        line_verts = []
        for i in range(len(sorted_points) - 1):
            line_verts.append(sorted_points[i][1][:])
            line_verts.append(sorted_points[i + 1][1][:])
        
        if line_verts:
            batch = batch_for_shader(shader, 'LINES', {"pos": line_verts})
            shader.uniform_float("color", (color[0], color[1], color[2], 0.9))
            batch.draw(shader)
        
        if point_frames and settings.show_points:
            point_shader = get_point_shader()
            point_shader.bind()
            gpu.state.point_size_set(6.0)
            
            point_verts = [p[1][:] for p in point_frames]
            point_batch = batch_for_shader(point_shader, 'POINTS', {"pos": point_verts})
            point_shader.uniform_float("color", (1.0, 1.0, 0.2, 1.0))
            point_batch.draw(point_shader)
    
    gpu.state.blend_set('NONE')
    gpu.state.depth_test_set('LESS_EQUAL')
    gpu.state.depth_mask_set(True)
    gpu.state.point_size_set(1.0)


class TrajectoryObjectItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name", default="")
    
    object: bpy.props.PointerProperty(
        name="Object",
        type=bpy.types.Object,
        description="Object to track trajectory for"
    )
    
    visible: bpy.props.BoolProperty(
        name="Visible",
        description="Show trajectory for this object",
        default=True
    )
    
    trajectory_type: bpy.props.EnumProperty(
        name="Type",
        description="Type of trajectory point",
        items=[
            ('ORIGIN', "Origin", "Object origin point"),
            ('CENTER', "Geometry Center", "Center of geometry"),
            ('VERTEX_GROUP', "Vertex Group", "Center of vertex group"),
        ],
        default='ORIGIN'
    )
    
    trajectory_vgroup: bpy.props.StringProperty(
        name="Vertex Group",
        description="Vertex group for trajectory",
        default=""
    )


class TrajectorySettings(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(
        name="Enable Trajectory",
        description="Toggle trajectory display",
        default=False
    )
    
    trajectory_start: bpy.props.IntProperty(
        name="Start",
        description="Start frame for trajectory",
        default=1,
        min=0
    )
    
    trajectory_end: bpy.props.IntProperty(
        name="End",
        description="End frame for trajectory",
        default=250,
        min=0
    )
    
    trajectory_point_step: bpy.props.IntProperty(
        name="Point Step",
        description="Show points every N frames (0 = no points)",
        default=10,
        min=0
    )
    
    show_points: bpy.props.BoolProperty(
        name="Show Points",
        description="Display trajectory points",
        default=True
    )


class TRAJECTORY_OT_AddObject(bpy.types.Operator):
    bl_idname = "e_motion.trajectory_add_object"
    bl_label = "Add Selected"
    bl_description = "Add selected objects to trajectory list"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.selected_objects
    
    def execute(self, context):
        existing = {item.object for item in context.scene.e_motion_trajectory_objects if item.object}
        added = 0
        
        for obj in context.selected_objects:
            if obj.type in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'ARMATURE'} and obj not in existing:
                item = context.scene.e_motion_trajectory_objects.add()
                item.object = obj
                item.name = obj.name
                added += 1
        
        if added > 0:
            build_trajectory_cache(context.scene)
        
        self.report({'INFO'}, f"Added {added} object(s)")
        return {'FINISHED'}


class TRAJECTORY_OT_RemoveSelected(bpy.types.Operator):
    bl_idname = "e_motion.trajectory_remove_selected"
    bl_label = "Remove"
    bl_description = "Remove selected object from list"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return len(context.scene.e_motion_trajectory_objects) > 0
    
    def execute(self, context):
        scene = context.scene
        index = scene.e_motion_trajectory_active_index
        
        if 0 <= index < len(scene.e_motion_trajectory_objects):
            scene.e_motion_trajectory_objects.remove(index)
            if index >= len(scene.e_motion_trajectory_objects) and len(scene.e_motion_trajectory_objects) > 0:
                scene.e_motion_trajectory_active_index = len(scene.e_motion_trajectory_objects) - 1
            clear_trajectory_cache()
        
        return {'FINISHED'}


class TRAJECTORY_OT_ClearAll(bpy.types.Operator):
    bl_idname = "e_motion.trajectory_clear_all"
    bl_label = "Clear All"
    bl_description = "Remove all objects from list"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        context.scene.e_motion_trajectory_objects.clear()
        clear_trajectory_cache()
        return {'FINISHED'}


class TRAJECTORY_OT_Refresh(bpy.types.Operator):
    bl_idname = "e_motion.trajectory_refresh"
    bl_label = "Refresh"
    bl_description = "Refresh trajectory cache"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        build_trajectory_cache(context.scene)
        self.report({'INFO'}, "Trajectory refreshed")
        return {'FINISHED'}


class TRAJECTORY_PT_MainPanel(bpy.types.Panel):
    bl_label = _("Trajectory")
    bl_idname = "TRAJECTORY_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'E_Motion'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.e_motion_trajectory_settings
        
        row = layout.row()
        row.prop(settings, "enabled", text=_('Enable Trajectory'))
        
        if not settings.enabled:
            return
        
        box = layout.box()
        box.label(text=_('Frame Range'), icon='TIME')
        
        row = box.row(align=True)
        row.prop(settings, "trajectory_start", text=_('Start'))
        row.prop(settings, "trajectory_end", text=_('End'))
        
        row = box.row()
        row.prop(settings, "trajectory_point_step", text=_('Point Step'))
        
        row = box.row()
        row.prop(settings, "show_points", text=_('Show Points'))
        
        box = layout.box()
        row = box.row()
        row.template_list(
            "UI_UL_list",
            "trajectory_objects",
            scene,
            "e_motion_trajectory_objects",
            scene,
            "e_motion_trajectory_active_index",
            rows=4
        )
        
        col = row.column(align=True)
        col.operator("e_motion.trajectory_add_object", icon='ADD', text="")
        col.operator("e_motion.trajectory_remove_selected", icon='REMOVE', text="")
        col.operator("e_motion.trajectory_clear_all", icon='X', text="")
        
        row = box.row()
        row.operator("e_motion.trajectory_refresh", icon='FILE_REFRESH', text=_('Refresh'))
        
        if scene.e_motion_trajectory_objects:
            active_index = scene.e_motion_trajectory_active_index
            if 0 <= active_index < len(scene.e_motion_trajectory_objects):
                item = scene.e_motion_trajectory_objects[active_index]
                if item.object:
                    box = layout.box()
                    box.label(text=_('Selected') + f": {item.object.name}", icon='OBJECT_DATA')
                    
                    row = box.row()
                    row.prop(item, "visible", text=_('Visible'))
                    
                    row = box.row()
                    row.prop(item, "trajectory_type", text=_('Type'))
                    
                    if item.trajectory_type == 'VERTEX_GROUP':
                        obj = item.object
                        if obj and obj.type == 'MESH' and obj.vertex_groups:
                            row = box.row()
                            row.prop_search(item, "trajectory_vgroup", obj, "vertex_groups", text=_('Vertex Group'))
                        else:
                            row = box.row()
                            row.label(text=_('No vertex groups available'), icon='ERROR')


_draw_handler = None


def register():
    bpy.utils.register_class(TrajectoryObjectItem)
    bpy.utils.register_class(TrajectorySettings)
    bpy.utils.register_class(TRAJECTORY_OT_AddObject)
    bpy.utils.register_class(TRAJECTORY_OT_RemoveSelected)
    bpy.utils.register_class(TRAJECTORY_OT_ClearAll)
    bpy.utils.register_class(TRAJECTORY_OT_Refresh)
    bpy.utils.register_class(TRAJECTORY_PT_MainPanel)
    
    bpy.types.Scene.e_motion_trajectory_settings = bpy.props.PointerProperty(type=TrajectorySettings)
    bpy.types.Scene.e_motion_trajectory_objects = bpy.props.CollectionProperty(type=TrajectoryObjectItem)
    bpy.types.Scene.e_motion_trajectory_active_index = bpy.props.IntProperty(name="Active Index")
    
    global _draw_handler
    _draw_handler = bpy.types.SpaceView3D.draw_handler_add(
        draw_trajectories, (), 'WINDOW', 'POST_VIEW'
    )


def unregister():
    global _draw_handler
    if _draw_handler:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handler, 'WINDOW')
        _draw_handler = None
    
    del bpy.types.Scene.e_motion_trajectory_active_index
    del bpy.types.Scene.e_motion_trajectory_objects
    del bpy.types.Scene.e_motion_trajectory_settings
    
    bpy.utils.unregister_class(TRAJECTORY_PT_MainPanel)
    bpy.utils.unregister_class(TRAJECTORY_OT_Refresh)
    bpy.utils.unregister_class(TRAJECTORY_OT_ClearAll)
    bpy.utils.unregister_class(TRAJECTORY_OT_RemoveSelected)
    bpy.utils.unregister_class(TRAJECTORY_OT_AddObject)
    bpy.utils.unregister_class(TrajectorySettings)
    bpy.utils.unregister_class(TrajectoryObjectItem)
    
    clear_trajectory_cache()
