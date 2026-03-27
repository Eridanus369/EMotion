import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from bpy.app.handlers import persistent
from . import onion_cache

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


def get_mesh_objects(context):
    settings = context.scene.e_motion_onion_settings
    meshes = []
    seen = set()
    geo_types = {'MESH', 'CURVE', 'SURFACE', 'FONT'}
    
    for item in context.scene.e_motion_onion_objects:
        obj = item.object
        if not obj or obj.name in seen or not item.visible:
            continue
        if obj.type in geo_types:
            meshes.append(obj)
            seen.add(obj.name)
        elif obj.type == 'ARMATURE' and settings.include_children:
            for child in obj.children:
                if child.type in geo_types and child.name not in seen:
                    meshes.append(child)
                    seen.add(child.name)
    
    return meshes


def extract_mesh_data(objects, depsgraph, wireframe=False):
    if not HAS_NUMPY:
        return extract_mesh_data_simple(objects, depsgraph, wireframe)
    
    all_verts = []
    all_indices = []
    vertex_offset = 0
    
    for obj in objects:
        try:
            eval_obj = obj.evaluated_get(depsgraph)
            mesh = eval_obj.to_mesh()
            if not mesh or len(mesh.vertices) == 0:
                continue
            
            num_verts = len(mesh.vertices)
            mat = eval_obj.matrix_world
            
            verts_co = np.empty(num_verts * 3, dtype=np.float32)
            mesh.vertices.foreach_get('co', verts_co)
            verts_co = verts_co.reshape(-1, 3)
            
            mat_np = np.array(mat.to_3x3(), dtype=np.float32)
            loc_np = np.array(mat.translation, dtype=np.float32)
            verts_world = verts_co @ mat_np.T + loc_np
            
            all_verts.append(verts_world)
            
            if wireframe:
                num_edges = len(mesh.edges)
                if num_edges > 0:
                    edge_data = np.empty(num_edges * 2, dtype=np.int32)
                    mesh.edges.foreach_get('vertices', edge_data)
                    edge_data += vertex_offset
                    all_indices.append(edge_data.reshape(-1, 2))
            else:
                mesh.calc_loop_triangles()
                num_tris = len(mesh.loop_triangles)
                if num_tris > 0:
                    tri_data = np.empty(num_tris * 3, dtype=np.int32)
                    mesh.loop_triangles.foreach_get('vertices', tri_data)
                    tri_data += vertex_offset
                    all_indices.append(tri_data.reshape(-1, 3))
            
            vertex_offset += num_verts
            eval_obj.to_mesh_clear()
        except Exception:
            continue
    
    if not all_verts or not all_indices:
        return None, None, None
    
    merged_verts = np.vstack(all_verts)
    merged_indices = np.vstack(all_indices)
    verts_list = [tuple(v) for v in merged_verts]
    indices_list = [tuple(idx) for idx in merged_indices]
    prim_type = 'LINES' if wireframe else 'TRIS'
    
    return verts_list, indices_list, prim_type


def extract_mesh_data_simple(objects, depsgraph, wireframe=False):
    all_verts = []
    all_indices = []
    vertex_offset = 0
    
    for obj in objects:
        try:
            eval_obj = obj.evaluated_get(depsgraph)
            mesh = eval_obj.to_mesh()
            if not mesh or len(mesh.vertices) == 0:
                continue
            
            mat = eval_obj.matrix_world
            for v in mesh.vertices:
                all_verts.append((mat @ v.co)[:])
            
            if wireframe:
                for e in mesh.edges:
                    all_indices.append((e.vertices[0] + vertex_offset, e.vertices[1] + vertex_offset))
            else:
                mesh.calc_loop_triangles()
                for t in mesh.loop_triangles:
                    all_indices.append((t.vertices[0] + vertex_offset, t.vertices[1] + vertex_offset, t.vertices[2] + vertex_offset))
            
            vertex_offset += len(mesh.vertices)
            eval_obj.to_mesh_clear()
        except Exception:
            continue
    
    if not all_verts or not all_indices:
        return None, None, None
    
    prim_type = 'LINES' if wireframe else 'TRIS'
    return all_verts, all_indices, prim_type


def cache_frame(context, frame):
    if onion_cache.is_frame_cached(frame):
        return True
    
    scene = context.scene
    settings = scene.e_motion_onion_settings
    objects = get_mesh_objects(context)
    
    if not objects:
        return False
    
    scene.frame_set(frame)
    depsgraph = context.evaluated_depsgraph_get()
    verts, indices, prim_type = extract_mesh_data(objects, depsgraph, settings.use_wireframe)
    
    if verts and indices:
        onion_cache.add_to_cache(frame, verts, indices, prim_type)
        return True
    
    return False


def get_frames_to_draw(current_frame, settings):
    frames_before = settings.frame_start
    frames_after = settings.frame_end
    step = settings.frame_step
    
    start_frame = max(0, current_frame - frames_before)
    end_frame = current_frame + frames_after
    
    frames = []
    
    for frame in range(start_frame, end_frame + 1, step):
        if frame == current_frame:
            continue
        
        distance = abs(frame - current_frame)
        max_distance = max(frames_before, frames_after)
        if max_distance == 0:
            max_distance = 1
        
        t = distance / max_distance
        
        if frame < current_frame:
            frames.append((frame, 'before', t, distance))
        else:
            frames.append((frame, 'after', t, distance))
    
    return frames


def calculate_alpha(distance, max_distance, base_alpha=0.5):
    if max_distance == 0:
        max_distance = 1
    
    t = distance / max_distance
    
    alpha = base_alpha * (1.0 - t * 0.9)
    alpha = max(0.1, min(base_alpha, alpha))
    
    return alpha


def ensure_frames_cached(context):
    scene = context.scene
    settings = scene.e_motion_onion_settings
    current = scene.frame_current
    
    if not settings.enabled or not scene.e_motion_onion_objects:
        return
    
    frames = get_frames_to_draw(current, settings)
    
    for frame, _, _, _ in frames:
        cache_frame(context, frame)


def precache_frames_for_scene(scene):
    global _is_caching
    if _is_caching:
        return
    
    import bpy
    context = bpy.context
    
    if not hasattr(scene, 'e_motion_onion_settings'):
        return
    
    settings = scene.e_motion_onion_settings
    if not settings.enabled or not scene.e_motion_onion_objects:
        return
    
    _is_caching = True
    try:
        onion_cache.clear_cache()
        
        current = scene.frame_current
        frames = get_frames_to_draw(current, settings)
        
        original_frame = current
        for frame, _, _, _ in frames:
            scene.frame_set(frame)
            depsgraph = context.evaluated_depsgraph_get()
            objects = get_mesh_objects(context)
            
            if objects:
                verts, indices, prim_type = extract_mesh_data(objects, depsgraph, settings.use_wireframe)
                if verts and indices:
                    onion_cache.add_to_cache(frame, verts, indices, prim_type)
        
        scene.frame_set(original_frame)
    finally:
        _is_caching = False


def draw_onion_skins():
    context = bpy.context
    
    if not context.area or context.area.type != 'VIEW_3D':
        return
    
    scene = context.scene
    if not hasattr(scene, 'e_motion_onion_settings'):
        return
    
    settings = scene.e_motion_onion_settings
    if not settings.enabled:
        return
    
    objects = scene.e_motion_onion_objects
    if not objects or len(objects) == 0:
        return
    
    valid_objects = [item for item in objects if item.object is not None and item.visible]
    if not valid_objects:
        return
    
    frames_to_draw = get_frames_to_draw(scene.frame_current, settings)
    
    if not frames_to_draw:
        return
    
    shader = onion_cache.get_shader()
    gpu.state.blend_set('ALPHA')
    gpu.state.depth_test_set('LESS_EQUAL')
    gpu.state.depth_mask_set(False)
    
    if settings.use_wireframe:
        gpu.state.line_width_set(1.5)
    
    shader.bind()
    
    frames_to_draw.sort(key=lambda x: -x[3])
    
    color_before = (1.0, 0.3, 0.2)
    color_after = (0.2, 0.5, 1.0)
    
    max_distance = max(settings.frame_start, settings.frame_end)
    
    for frame, direction, t, distance in frames_to_draw:
        batch = onion_cache.get_batch(frame)
        if batch is None:
            continue
        
        base_color = color_before if direction == 'before' else color_after
        alpha = calculate_alpha(distance, max_distance)
        
        shader.uniform_float("color", (base_color[0], base_color[1], base_color[2], alpha))
        batch.draw(shader)
    
    gpu.state.blend_set('NONE')
    gpu.state.depth_test_set('LESS_EQUAL')
    gpu.state.depth_mask_set(True)
    
    if settings.use_wireframe:
        gpu.state.line_width_set(1.0)


_draw_handler = None
_is_caching = False


@persistent
def _on_frame_change(scene, depsgraph):
    precache_frames_for_scene(scene)


@persistent
def _on_depsgraph_update(scene, depsgraph):
    if not hasattr(scene, 'e_motion_onion_settings'):
        return
    
    settings = scene.e_motion_onion_settings
    if not settings.enabled or not scene.e_motion_onion_objects:
        return
    
    for update in depsgraph.updates:
        if isinstance(update.id, bpy.types.Object) and update.is_updated_geometry:
            tracked = set()
            for item in scene.e_motion_onion_objects:
                obj = item.object
                if obj:
                    tracked.add(obj.name)
                    if obj.type == 'ARMATURE' and settings.include_children:
                        for child in obj.children:
                            tracked.add(child.name)
            
            if update.id.name in tracked:
                onion_cache.clear_cache()
                return


def register():
    global _draw_handler
    _draw_handler = bpy.types.SpaceView3D.draw_handler_add(
        draw_onion_skins, (), 'WINDOW', 'POST_VIEW'
    )
    bpy.app.handlers.frame_change_post.append(_on_frame_change)
    bpy.app.handlers.depsgraph_update_post.append(_on_depsgraph_update)


def unregister():
    global _draw_handler
    if _draw_handler:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handler, 'WINDOW')
        _draw_handler = None
    
    if _on_frame_change in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(_on_frame_change)
    if _on_depsgraph_update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_on_depsgraph_update)
    
    onion_cache.cleanup()
