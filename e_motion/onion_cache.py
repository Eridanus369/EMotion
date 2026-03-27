from collections import OrderedDict
import gpu
from gpu_extras.batch import batch_for_shader

_shader = None
_frame_cache = OrderedDict()
_batch_cache = {}
_max_cache_size = 100
_settings_cache = {}


def get_shader():
    global _shader
    if _shader is None:
        _shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    return _shader


def clear_cache():
    _frame_cache.clear()
    _batch_cache.clear()


def get_settings_cache():
    return _settings_cache


def set_settings_cache(key, value):
    _settings_cache[key] = value


def is_frame_cached(frame):
    return frame in _frame_cache


def add_to_cache(frame, verts, indices, prim_type):
    if not verts or not indices:
        return
    _frame_cache[frame] = (verts, indices, prim_type)
    _frame_cache.move_to_end(frame)
    _batch_cache.pop(frame, None)
    
    while len(_frame_cache) > _max_cache_size:
        old_frame = next(iter(_frame_cache))
        del _frame_cache[old_frame]
        _batch_cache.pop(old_frame, None)


def get_batch(frame):
    if frame in _batch_cache:
        return _batch_cache[frame]
    
    data = _frame_cache.get(frame)
    if data is None:
        return None
    
    verts, indices, prim_type = data
    batch = batch_for_shader(get_shader(), prim_type, {"pos": verts}, indices=indices)
    _batch_cache[frame] = batch
    return batch


def get_cached_frames():
    return list(_frame_cache.keys())


def cleanup():
    global _shader
    _shader = None
    clear_cache()
    _settings_cache.clear()


def register():
    pass


def unregister():
    cleanup()
