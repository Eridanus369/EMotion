import bpy
import gpu
import blf
import math
import os
import json
from gpu_extras.batch import batch_for_shader
from bpy.types import Menu, Operator
from ..language import _

# 贝塞尔曲线编辑器核心功能

# 预设文件路径
PRESET_FILE = os.path.join(os.path.dirname(__file__), '..', 'bezier_presets.json')

# 预设缓存
_PRESET_CACHE = []
_PRESET_MTIME = -1.0

# 编辑模式状态存储（使用全局字典，因为Blender的WindowManager不支持动态属性）
_edit_mode_state = {
    'emo_active_modifier': None,
    'emo_active_curve': None,
}

def _get_edit_mode_state(key, default=None):
    """获取编辑模式状态"""
    return _edit_mode_state.get(key, default)

def _set_edit_mode_state(key, value):
    """设置编辑模式状态"""
    _edit_mode_state[key] = value

# 绘制辅助函数
def _draw_rect(x0, y0, x1, y1, color):
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    verts = [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]
    batch = batch_for_shader(shader, 'TRI_STRIP', {"pos": verts})
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)

def _draw_line_strip(points, color, width=1.0):
    if len(points) < 2:
        return
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": points})
    shader.bind()
    shader.uniform_float("color", color)
    try:
        gpu.state.line_width_set(width)
    except Exception:
        pass
    batch.draw(shader)
    try:
        gpu.state.line_width_set(1.0)
    except Exception:
        pass

# 抗锯齿线条绘制
def _get_aa_polyline_shader():
    try:
        return gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
    except Exception:
        return None

def _draw_aa_line_strip(points, color, width=1.0):
    if len(points) < 2:
        return
    shader = _get_aa_polyline_shader()
    if shader is None:
        _draw_line_strip(points, color, width=width)
        return

    try:
        vp = gpu.state.viewport_get()
        if len(vp) >= 4:
            viewport_size = (float(vp[2]), float(vp[3]))
        else:
            viewport_size = (1920.0, 1080.0)
    except Exception:
        viewport_size = (1920.0, 1080.0)

    batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": points})
    shader.bind()
    shader.uniform_float("viewportSize", viewport_size)
    shader.uniform_float("lineWidth", max(1.0, float(width)))
    shader.uniform_float("color", color)
    batch.draw(shader)

# 圆形绘制
def _draw_filled_circle(x, y, r, color, steps=24):
    verts = [(x, y)]
    for i in range(steps + 1):
        t = (i / steps) * 6.28318530718
        verts.append((
            x + r * math.cos(t),
            y + r * math.sin(t),
        ))
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'TRI_FAN', {"pos": verts})
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)

def _draw_circle(x, y, r, color, steps=24, width=1.0):
    pts = []
    for i in range(steps + 1):
        t = (i / steps) * 6.28318530718
        pts.append((
            x + r * math.cos(t),
            y + r * math.sin(t),
        ))
    _draw_aa_line_strip(pts, color, width=width)

def _draw_aa_circle(x, y, r, fill_color, outline_color, steps=28):
    step_count = max(24, int(steps))
    _draw_filled_circle(x, y, max(1.0, r - 0.8), fill_color, steps=step_count)
    _draw_circle(x, y, r, outline_color, steps=step_count, width=1.0)

# 文本绘制
def _draw_text(x, y, text, size=12, color=(1, 1, 1, 1)):
    font_id = 0
    blf.size(font_id, size)
    blf.color(font_id, *color)
    blf.position(font_id, x, y, 0)
    blf.draw(font_id, text)

def _draw_text_centered(x0, y0, x1, y1, text, size=10, color=(1, 1, 1, 1), truncate=False, pad=4):
    font_id = 0
    blf.size(font_id, size)
    tw, th = blf.dimensions(font_id, text)
    tx = x0 + ((x1 - x0) - tw) * 0.5
    ty = y0 + ((y1 - y0) - th) * 0.5 + 1.0
    _draw_text(tx, ty, text, size=size, color=color)

# 文本截断
def _truncate_text_to_width(text, max_width, size=10):
    if max_width <= 1.0:
        return ""
    font_id = 0
    blf.size(font_id, size)
    if blf.dimensions(font_id, text)[0] <= max_width:
        return text

    ellipsis = "..."
    ell_w = blf.dimensions(font_id, ellipsis)[0]
    if ell_w >= max_width:
        return ""

    lo = 0
    hi = len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        candidate = text[:mid] + ellipsis
        if blf.dimensions(font_id, candidate)[0] <= max_width:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo] + ellipsis

def _draw_text_clipped_left(x, y, max_width, text, size=10, color=(1, 1, 1, 1), pad=0):
    clipped = _truncate_text_to_width(str(text), max(1.0, max_width - pad), size=size)
    if not clipped:
        return
    _draw_text(x, y, clipped, size=size, color=color)

# 贝塞尔曲线计算
def _bezier_point(t, p0, p1, p2, p3):
    u = 1.0 - t
    b0 = u * u * u
    b1 = 3.0 * u * u * t
    b2 = 3.0 * u * t * t
    b3 = t * t * t
    return (
        b0 * p0[0] + b1 * p1[0] + b2 * p2[0] + b3 * p3[0],
        b0 * p0[1] + b1 * p1[1] + b2 * p2[1] + b3 * p3[1],
    )

# 坐标转换
def _editor_to_screen(nx, ny, sx0, sy0, sx1, sy1, zoom, pan_x, pan_y):
    vx = (nx - 0.5) * zoom + 0.5 + pan_x
    vy = (ny - 0.5) * zoom + 0.5 + pan_y
    return (
        sx0 + vx * (sx1 - sx0),
        sy0 + vy * (sy1 - sy0),
    )

def _screen_to_editor(px, py, sx0, sy0, sx1, sy1, zoom, pan_x, pan_y):
    vx = (px - sx0) / max(1e-8, (sx1 - sx0))
    vy = (py - sy0) / max(1e-8, (sy1 - sy0))
    nx = ((vx - 0.5 - pan_x) / max(1e-8, zoom)) + 0.5
    ny = ((vy - 0.5 - pan_y) / max(1e-8, zoom)) + 0.5
    return nx, ny

# 约束处理
def _constrain_handle(which, x, y):
    return max(0.0, min(1.0, x)), y

# 吸附功能
def _snap_edge(x, y, threshold):
    sx, sy = x, y
    for edge in (0.0, 1.0):
        if abs(sx - edge) <= threshold:
            sx = edge
        if abs(sy - edge) <= threshold:
            sy = edge
    return sx, sy

def _snap_grid(x, y, subdiv):
    if subdiv <= 0:
        return x, y
    step = 1.0 / float(subdiv)
    return round(x / step) * step, round(y / step) * step

# 矩形检测
def _point_in_rect(px, py, rect):
    x0, y0, x1, y1 = rect
    return x0 <= px <= x1 and y0 <= py <= y1

# 按钮状态颜色
def _button_state_colors(kind, state):
    if kind == "apply":
        base = (0.72, 0.36, 0.15, 0.95)
        border = (0.84, 0.77, 0.66, 0.98)
    elif kind == "auto_on":
        base = (0.14, 0.48, 0.24, 0.95)
        border = (0.62, 0.88, 0.66, 0.98)
    elif kind == "auto_off":
        base = (0.34, 0.20, 0.20, 0.92)
        border = (0.84, 0.62, 0.62, 0.95)
    elif kind == "preset":
        base = (0.22, 0.26, 0.32, 0.90)
        border = (0.66, 0.71, 0.81, 0.95)
    else:
        base = (0.24, 0.28, 0.36, 0.88)
        border = (0.70, 0.74, 0.82, 0.95)

    if state == "hover":
        return _adjust_rgba(base, 0.08), _adjust_rgba(border, 0.07), (1.0, 1.0, 1.0, 1.0)
    if state == "pressed":
        return _adjust_rgba(base, -0.08), _adjust_rgba(border, -0.05), (0.93, 0.94, 0.96, 1.0)
    return base, border, (0.96, 0.97, 0.99, 1.0)

def _adjust_rgba(color, delta):
    return (
        max(0.0, min(1.0, color[0] + delta)),
        max(0.0, min(1.0, color[1] + delta)),
        max(0.0, min(1.0, color[2] + delta)),
        color[3],
    )

# 按钮令牌
def _button_token(op, kwargs):
    if op == "zoom":
        return f"zoom:{kwargs.get('mode', 'CENTER')}"
    if op == "interp":
        return f"interp:{kwargs.get('mode', 'LINEAR')}"
    if op == "preset_apply":
        return f"preset:{int(kwargs.get('idx', -1))}"
    return op

# 预设管理
def _load_presets(force=False):
    global _PRESET_CACHE, _PRESET_MTIME
    try:
        mtime = os.path.getmtime(PRESET_FILE)
    except Exception:
        _PRESET_CACHE = []
        _PRESET_MTIME = -1.0
        return []

    if not force and mtime == _PRESET_MTIME:
        return _PRESET_CACHE

    try:
        with open(PRESET_FILE, 'r', encoding="utf-8") as f:
            data = json.load(f)
        presets = []
        for p in data if isinstance(data, list) else []:
            presets.append({
                "name": str(p.get("name", "Preset")),
                "h1x": float(p.get("h1x", 0.333)),
                "h1y": float(p.get("h1y", 0.0)),
                "h2x": float(p.get("h2x", 0.667)),
                "h2y": float(p.get("h2y", 1.0)),
            })
        _PRESET_CACHE = presets
        _PRESET_MTIME = mtime
        return presets
    except Exception:
        _PRESET_CACHE = []
        _PRESET_MTIME = mtime
        return []

def _save_presets(presets):
    try:
        with open(PRESET_FILE, "w", encoding="utf-8") as f:
            json.dump(presets, f, indent=2)
    except Exception:
        return False
    _load_presets(force=True)
    return True

def _add_current_preset(h1x, h1y, h2x, h2y):
    presets = list(_load_presets())
    presets.append({
        "name": f"Curve",
        "h1x": float(h1x),
        "h1y": float(h1y),
        "h2x": float(h2x),
        "h2y": float(h2y),
    })
    return _save_presets(presets)

def _apply_preset_index(idx):
    presets = _load_presets()
    if idx < 0 or idx >= len(presets):
        return None
    return presets[idx]

def _delete_preset_index(idx):
    presets = list(_load_presets())
    if idx < 0 or idx >= len(presets):
        return False
    presets.pop(idx)
    return _save_presets(presets)

# 绘制预设 tile
def _draw_preset_tile(x0, y0, x1, y1, preset, size_scale):
    _draw_rect(x0, y0, x1, y1, (0.18, 0.20, 0.24, 0.92))
    _draw_aa_line_strip([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], (0.70, 0.74, 0.82, 0.95), width=1.0)
    pad = max(4, int(5 * size_scale))
    ix0 = x0 + pad
    iy0 = y0 + pad + 10
    ix1 = x1 - pad
    iy1 = y1 - pad
    _draw_rect(ix0, iy0, ix1, iy1, (0.08, 0.09, 0.11, 0.8))
    _draw_aa_line_strip([(ix0, iy0), (ix1, iy0), (ix1, iy1), (ix0, iy1), (ix0, iy0)], (0.42, 0.45, 0.52, 0.95), width=1.0)

    h1x = max(0.0, float(preset["h1x"]))
    h1y = float(preset["h1y"])
    h2x = min(1.0, float(preset["h2x"]))
    h2y = float(preset["h2y"])
    p0 = (0.0, 0.0)
    p1 = (h1x, h1y)
    p2 = (h2x, h2y)
    p3 = (1.0, 1.0)
    pts = []
    preview_steps = 32
    for i in range(preview_steps):
        t = i / (preview_steps - 1.0)
        bx, by = _bezier_point(t, p0, p1, p2, p3)
        pts.append((ix0 + bx * (ix1 - ix0), iy0 + by * (iy1 - iy0)))
    _draw_aa_line_strip(pts, (0.95, 0.62, 0.18, 1.0), width=1.5)
    _draw_text_centered(x0, y0, x1, y0 + 12, preset.get("name", "P"), size=max(8, int(9 * size_scale)), color=(0.92, 0.94, 0.98, 1.0), truncate=True, pad=4)

# 应用曲线到关键帧
def _apply_editor_curve_to_segment(k0, k1, h1x, h1y, h2x, h2y):
    f0, v0 = k0.co[0], k0.co[1]
    f1, v1 = k1.co[0], k1.co[1]
    df = f1 - f0
    dv = v1 - v0
    if abs(df) < 1e-8:
        return False

    k0.interpolation = 'BEZIER'
    k1.interpolation = 'BEZIER'
    k0.handle_right_type = 'FREE'
    k1.handle_left_type = 'FREE'
    h1x, h1y = _constrain_handle("h1", h1x, h1y)
    h2x, h2y = _constrain_handle("h2", h2x, h2y)
    k0.handle_right = (f0 + h1x * df, v0 + h1y * dv)
    k1.handle_left = (f0 + h2x * df, v0 + h2y * dv)
    return True

# 收集选中的关键帧段
def _iter_selected_segments(context):
    selected_items = _selected_fcurves_with_selected_keys(context)
    for fc, sel_keys, all_keys in selected_items:
        key_sorted = sorted(all_keys, key=lambda kp: kp.co[0])
        if sel_keys:
            # 如果有关键帧被选中，只处理选中的关键帧段
            selected_ids = {id(kp) for kp in sel_keys}
            for i, kp in enumerate(key_sorted[:-1]):
                if id(kp) in selected_ids:
                    nxt = key_sorted[i + 1]
                    if nxt.co[0] > kp.co[0]:
                        yield fc, kp, nxt
        else:
            # 如果没有关键帧被选中但曲线被选中，处理所有关键帧段
            for i, kp in enumerate(key_sorted[:-1]):
                nxt = key_sorted[i + 1]
                if nxt.co[0] > kp.co[0]:
                    yield fc, kp, nxt

def _selected_fcurves_with_selected_keys(context):
    candidates = []
    for attr in ("selected_editable_fcurves", "selected_visible_fcurves", "visible_fcurves"):
        fcurves = getattr(context, attr, None)
        if fcurves:
            candidates = list(fcurves)
            break
    if not candidates:
        obj = context.active_object
        if obj and obj.animation_data:
            candidates = _collect_action_fcurves(obj.animation_data)

    out = []
    seen = set()
    for fc in candidates:
        fc_id = id(fc)
        if fc_id in seen:
            continue
        seen.add(fc_id)

        all_keys = list(fc.keyframe_points)
        sel_keys = []
        for kp in all_keys:
            if kp.select_control_point or kp.select_left_handle or kp.select_right_handle:
                sel_keys.append(kp)

        if sel_keys or getattr(fc, "select", False):
            out.append((fc, sel_keys, all_keys))
    return out

def _collect_action_fcurves(anim_data):
    action = getattr(anim_data, "action", None) if anim_data else None
    if action is None:
        return []

    direct = getattr(action, "fcurves", None)
    if direct is not None:
        try:
            return list(direct)
        except Exception:
            return []

    out = []
    seen = set()
    layers = getattr(action, "layers", None)
    if not layers:
        return out

    slot_candidates = []
    active_slot = getattr(anim_data, "action_slot", None)
    if active_slot is not None:
        slot_candidates.append(active_slot)
    slots = getattr(action, "slots", None)
    if slots:
        try:
            slot_candidates.extend(list(slots))
        except Exception:
            pass

    for layer in layers:
        strips = getattr(layer, "strips", None)
        if not strips:
            continue
        for strip in strips:
            channelbag_fn = getattr(strip, "channelbag", None)
            if not callable(channelbag_fn):
                continue
            for slot in slot_candidates:
                try:
                    bag = channelbag_fn(slot)
                except Exception:
                    continue
                if not bag:
                    continue
                bag_fcurves = getattr(bag, "fcurves", None)
                if not bag_fcurves:
                    continue
                try:
                    for fc in bag_fcurves:
                        fc_id = id(fc)
                        if fc_id in seen:
                            continue
                        seen.add(fc_id)
                        out.append(fc)
                except Exception:
                    continue
    return out

# 获取焦点曲线信息
def _focused_curve_info(context, selected_items):
    if not selected_items:
        return None
    active_fc = getattr(context, "active_editable_fcurve", None)
    if active_fc is not None:
        for item in selected_items:
            if item[0] == active_fc:
                fc, sel_keys, all_keys = item
                break
        else:
            fc, sel_keys, all_keys = selected_items[0]
    else:
        fc, sel_keys, all_keys = selected_items[0]

    key_source = sel_keys if sel_keys else all_keys
    frames = [kp.co[0] for kp in key_source]
    values = [kp.co[1] for kp in key_source]
    frame_now = context.scene.frame_current
    try:
        eval_now = fc.evaluate(frame_now)
    except Exception:
        eval_now = None

    return {
        "name": f"{fc.data_path}[{fc.array_index}]",
        "group": fc.group.name if fc.group else "None",
        "keys_total": len(all_keys),
        "keys_selected": len(sel_keys),
        "frame_span": (min(frames), max(frames)) if frames else None,
        "value_span": (min(values), max(values)) if values else None,
        "eval_now": eval_now,
        "modifiers": len(fc.modifiers),
        "extrapolation": fc.extrapolation,
    }

# 按钮定义
def _overlay_buttons():
    return [
        [
            {"label": "Zoom +", "op": "zoom", "kwargs": {"mode": "IN"}},
            {"label": "Zoom -", "op": "zoom", "kwargs": {"mode": "OUT"}},
            {"label": "Center", "op": "zoom", "kwargs": {"mode": "CENTER"}},
        ],
        [
            {"label": "Mirror", "op": "mirror", "kwargs": {}},
            {"label": "Reset", "op": "reset", "kwargs": {}},
            {"label": "Save", "op": "preset_save", "kwargs": {}},
        ],
        [
            {"label": "Linear", "op": "interp", "kwargs": {"mode": "LINEAR"}},
            {"label": "Constant", "op": "interp", "kwargs": {"mode": "CONSTANT"}},
        ],
    ]

# 调用按钮操作
def _invoke_overlay_button(context, op, kwargs, shift=False):
    try:
        if op == "zoom":
            mode = kwargs.get("mode", "CENTER")
            if mode == "IN":
                bezier_editor.zoom = min(6.0, bezier_editor.zoom * 1.2)
            elif mode == "OUT":
                bezier_editor.zoom = max(0.2, bezier_editor.zoom / 1.2)
            else:
                bezier_editor.zoom = 1.0
                bezier_editor.pan_x = 0.0
                bezier_editor.pan_y = 0.0
        elif op == "preset_save":
            bezier_editor.save_preset()
        elif op == "preset_apply":
            idx = int(kwargs.get("idx", -1))
            if shift:
                _delete_preset_index(idx)
            else:
                preset = _apply_preset_index(idx)
                if preset:
                    bezier_editor.h1x = preset["h1x"]
                    bezier_editor.h1y = preset["h1y"]
                    bezier_editor.h2x = preset["h2x"]
                    bezier_editor.h2y = preset["h2y"]
        elif op == "mirror":
            bezier_editor.mirror_curve()
        elif op == "reset":
            bezier_editor.reset_curve()
        elif op == "interp":
            mode = kwargs.get("mode", "LINEAR")
            for fc, sel_keys, _ in _selected_fcurves_with_selected_keys(context):
                for kp in sel_keys:
                    kp.interpolation = mode
    except Exception:
        pass

# 贝塞尔曲线编辑器类
class BezierCurveEditor:
    def __init__(self):
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.is_editing = False
        self.drag_handle = None
        self.ui_data = {}
        self.preview_area = None
        self.draw_handler = None
    
    def get_h1x(self, context):
        return context.window_manager.emo_bezier_h1x
    
    def get_h1y(self, context):
        return context.window_manager.emo_bezier_h1y
    
    def get_h2x(self, context):
        return context.window_manager.emo_bezier_h2x
    
    def get_h2y(self, context):
        return context.window_manager.emo_bezier_h2y
    
    def set_h1x(self, context, value):
        context.window_manager.emo_bezier_h1x = value
    
    def set_h1y(self, context, value):
        context.window_manager.emo_bezier_h1y = value
    
    def set_h2x(self, context, value):
        context.window_manager.emo_bezier_h2x = value
    
    def set_h2y(self, context, value):
        context.window_manager.emo_bezier_h2y = value
    
    def draw(self, context):
        # 获取当前区域
        region = context.region
        if not region:
            return
        
        # 从窗口管理器获取贝塞尔参数
        h1x = self.get_h1x(context)
        h1y = self.get_h1y(context)
        h2x = self.get_h2x(context)
        h2y = self.get_h2y(context)
        
        size_scale = 1.5
        alpha = 1.0
        
        # 计算预览区域大小
        width = 300
        height = 200
        
        # 绘制面板背景和边框
        x0, y0, x1, y1 = 0, 0, width, height
        bg = (0.08, 0.09, 0.11, alpha)
        border = (0.65, 0.68, 0.74, min(1.0, alpha + 0.2))
        _draw_rect(x0, y0, x1, y1, bg)
        _draw_aa_line_strip([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], border, width=1.0)
        
        # 绘制贝塞尔曲线编辑器
        pad = 12
        sx0 = x0 + pad
        sx1_limit = x1 - pad
        sy1 = y1 - pad
        max_h = max(60, height - pad * 2)
        sq = min(max_h, sx1_limit - sx0)
        sx1 = sx0 + sq
        sy0 = sy1 - sq
        
        # 保存预览区域信息
        self.preview_area = (sx0, sy0, sx1, sy1)
        
        # 绘制背景
        _draw_rect(sx0, sy0, sx1, sy1, (0.03, 0.035, 0.045, 0.7))
        _draw_aa_line_strip([(sx0, sy0), (sx1, sy0), (sx1, sy1), (sx0, sy1), (sx0, sy0)], (0.42, 0.45, 0.52, 0.95), width=1.0)
        
        # 绘制网格
        subdiv = 4
        for i in range(subdiv + 1):
            g = i / float(subdiv)
            va = _editor_to_screen(g, 0.0, sx0, sy0, sx1, sy1, self.zoom, self.pan_x, self.pan_y)
            vb = _editor_to_screen(g, 1.0, sx0, sy0, sx1, sy1, self.zoom, self.pan_x, self.pan_y)
            ha = _editor_to_screen(0.0, g, sx0, sy0, sx1, sy1, self.zoom, self.pan_x, self.pan_y)
            hb = _editor_to_screen(1.0, g, sx0, sy0, sx1, sy1, self.zoom, self.pan_x, self.pan_y)
            col = (0.30, 0.33, 0.39, 0.9) if i in (0, subdiv) else (0.24, 0.26, 0.31, 0.65)
            _draw_aa_line_strip([va, vb], col, width=1.0)
            _draw_aa_line_strip([ha, hb], col, width=1.0)
        
        # 绘制贝塞尔曲线
        p0 = (0.0, 0.0)
        p1 = (h1x, h1y)
        p2 = (h2x, h2y)
        p3 = (1.0, 1.0)
        p0s = _editor_to_screen(p0[0], p0[1], sx0, sy0, sx1, sy1, self.zoom, self.pan_x, self.pan_y)
        p1s = _editor_to_screen(p1[0], p1[1], sx0, sy0, sx1, sy1, self.zoom, self.pan_x, self.pan_y)
        p2s = _editor_to_screen(p2[0], p2[1], sx0, sy0, sx1, sy1, self.zoom, self.pan_x, self.pan_y)
        p3s = _editor_to_screen(p3[0], p3[1], sx0, sy0, sx1, sy1, self.zoom, self.pan_x, self.pan_y)
        
        # 绘制控制柄
        _draw_aa_line_strip([p0s, p1s], (0.64, 0.66, 0.72, 0.85), width=1.0)
        _draw_aa_line_strip([p3s, p2s], (0.64, 0.66, 0.72, 0.85), width=1.0)
        
        # 绘制曲线预览
        curve_pts = []
        samples = 32
        n = max(48, samples * 2)
        for i in range(n):
            t = i / (n - 1)
            bx, by = _bezier_point(t, p0, p1, p2, p3)
            curve_pts.append(_editor_to_screen(bx, by, sx0, sy0, sx1, sy1, self.zoom, self.pan_x, self.pan_y))
        _draw_aa_line_strip(curve_pts, (0.95, 0.62, 0.18, 1.0), width=2.0)
        
        # 绘制控制点
        _draw_aa_circle(p1s[0], p1s[1], 5.4 * size_scale, (0.22, 0.84, 0.96, 1.0), (1.0, 1.0, 1.0, 0.92))
        _draw_aa_circle(p2s[0], p2s[1], 5.4 * size_scale, (0.96, 0.48, 0.24, 1.0), (1.0, 1.0, 1.0, 0.92))
        
        # 保存UI数据用于鼠标交互
        self.ui_data = {
            "area": context.area.as_pointer() if context.area else 0,
            "region": region.as_pointer(),
            "panel_rect_abs": (region.x + x0, region.y + y0, region.x + x1, region.y + y1),
            "rect": (sx0, sy0, sx1, sy1),
            "rect_abs": (region.x + sx0, region.y + sy0, region.x + sx1, region.y + sy1),
            "h1": p1s,
            "h2": p2s,
            "h1_abs": (region.x + p1s[0], region.y + p1s[1]),
            "h2_abs": (region.x + p2s[0], region.y + p2s[1]),
            "buttons_abs": [],
        }
    
    def handle_mouse_event(self, context, event):
        if not self.ui_data:
            return False
        
        mx_abs = event.mouse_x
        my_abs = event.mouse_y
        panel_rect = self.ui_data.get("panel_rect_abs")
        if not panel_rect:
            return False
        
        rx0, ry0, rx1, ry1 = self.ui_data["rect_abs"]
        inside = (rx0 <= mx_abs <= rx1 and ry0 <= my_abs <= ry1)
        sx0, sy0, sx1, sy1 = self.ui_data["rect"]
        mx = mx_abs - rx0 + sx0
        my = my_abs - ry0 + sy0
        
        # 处理鼠标按下
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            h1 = self.ui_data["h1_abs"]
            h2 = self.ui_data["h2_abs"]
            d1 = (mx_abs - h1[0]) * (mx_abs - h1[0]) + (my_abs - h1[1]) * (my_abs - h1[1])
            d2 = (mx_abs - h2[0]) * (mx_abs - h2[0]) + (my_abs - h2[1]) * (my_abs - h2[1])
            if d1 <= 196:
                self.drag_handle = "h1"
                return True
            if d2 <= 196:
                self.drag_handle = "h2"
                return True
            
            # 检查按钮点击
            for btn in self.ui_data.get("buttons_abs", []):
                if _point_in_rect(mx_abs, my_abs, btn["rect"]):
                    if btn["op"] == "apply":
                        self.apply_curve(context)
                    else:
                        _invoke_overlay_button(context, btn["op"], btn.get("kwargs", {}), shift=event.shift)
                    return True
        
        # 处理鼠标释放
        if event.type in {'LEFTMOUSE', 'MIDDLEMOUSE'} and event.value == 'RELEASE':
            self.drag_handle = None
            return True
        
        # 处理鼠标移动
        if event.type == 'MOUSEMOVE' and self.drag_handle in {"h1", "h2"}:
            nx, ny = _screen_to_editor(mx, my, sx0, sy0, sx1, sy1, self.zoom, self.pan_x, self.pan_y)
            nx, ny = _constrain_handle(self.drag_handle, nx, ny)
            
            if event.ctrl:
                nx, ny = _snap_grid(nx, ny, 4)
                nx, ny = _constrain_handle(self.drag_handle, nx, ny)
            if event.shift:
                nx, ny = _snap_edge(nx, ny, 0.1)
                nx, ny = _constrain_handle(self.drag_handle, nx, ny)
            
            if self.drag_handle == "h1":
                self.set_h1x(context, nx)
                self.set_h1y(context, ny)
            else:
                self.set_h2x(context, nx)
                self.set_h2y(context, ny)
            
            # 重绘区域
            if context.area:
                context.area.tag_redraw()
            return True
        
        # 处理中键平移
        if event.type == 'MIDDLEMOUSE' and event.value == 'PRESS':
            if inside:
                self.drag_handle = "pan"
                self.pan_start_x = mx_abs
                self.pan_start_y = my_abs
                self.pan_origin_x = self.pan_x
                self.pan_origin_y = self.pan_y
                return True
        
        if event.type == 'MOUSEMOVE' and self.drag_handle == "pan":
            dx = mx_abs - self.pan_start_x
            dy = my_abs - self.pan_start_y
            rw = max(1.0, sx1 - sx0)
            rh = max(1.0, sy1 - sy0)
            self.pan_x = self.pan_origin_x + (dx / rw)
            self.pan_y = self.pan_origin_y + (dy / rh)
            if context.area:
                context.area.tag_redraw()
            return True
        
        return False
    
    def apply_curve(self, context):
        h1x = self.get_h1x(context)
        h1y = self.get_h1y(context)
        h2x = self.get_h2x(context)
        h2y = self.get_h2y(context)
        
        pairs = 0
        curves = set()
        for fc, k0, k1 in _iter_selected_segments(context):
            if _apply_editor_curve_to_segment(k0, k1, h1x, h1y, h2x, h2y):
                fc.update()
                pairs += 1
                curves.add(id(fc))
        return pairs, len(curves)
    
    def mirror_curve(self, context):
        h1x = self.get_h1x(context)
        h1y = self.get_h1y(context)
        h2x = self.get_h2x(context)
        h2y = self.get_h2y(context)
        
        nh1x, nh1y = 1.0 - h2x, 1.0 - h2y
        nh2x, nh2y = 1.0 - h1x, 1.0 - h1y
        nh1x, nh1y = _constrain_handle("h1", nh1x, nh1y)
        nh2x, nh2y = _constrain_handle("h2", nh2x, nh2y)
        
        self.set_h1x(context, nh1x)
        self.set_h1y(context, nh1y)
        self.set_h2x(context, nh2x)
        self.set_h2y(context, nh2y)
    
    def reset_curve(self, context):
        self.set_h1x(context, 0.333)
        self.set_h1y(context, 0.00)
        self.set_h2x(context, 0.667)
        self.set_h2y(context, 1.00)
    
    def save_preset(self, context):
        h1x = self.get_h1x(context)
        h1y = self.get_h1y(context)
        h2x = self.get_h2x(context)
        h2y = self.get_h2y(context)
        return _add_current_preset(h1x, h1y, h2x, h2y)

# 全局贝塞尔编辑器实例
bezier_editor = BezierCurveEditor()

# 操作符类
class GRAPH_OT_emo_bezier_editor(bpy.types.Operator):
    bl_idname = "graph.emo_bezier_editor"
    bl_label = "Bezier Editor"
    bl_description = "Open Bezier curve editor"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        return {'FINISHED'}

class GRAPH_OT_emo_apply_bezier_curve(bpy.types.Operator):
    bl_idname = "graph.emo_apply_bezier_curve"
    bl_label = "Apply Bezier Curve"
    bl_description = "Apply Bezier curve to selected keyframes"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        pairs, curves = bezier_editor.apply_curve(context)
        if pairs == 0:
            self.report({'WARNING'}, "No selected keyframe pairs found to apply")
            return {'CANCELLED'}
        # 重绘区域，确保修改被显示
        if context.area:
            context.area.tag_redraw()
        # 确保所有修改都被应用
        if context.view_layer:
            context.view_layer.update()
        # 强制更新所有场景数据
        for scene in bpy.data.scenes:
            scene.update_tag()
        # 再次重绘以确保所有更改都被显示
        if context.area:
            context.area.tag_redraw()
        self.report({'INFO'}, f"Applied curve to {pairs} segment(s) on {curves} F-curve(s)")
        return {'FINISHED'}

class GRAPH_OT_emo_mirror_bezier_curve(bpy.types.Operator):
    bl_idname = "graph.emo_mirror_bezier_curve"
    bl_label = "Mirror Bezier Curve"
    bl_description = "Mirror Bezier curve handles"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        bezier_editor.mirror_curve(context)
        return {'FINISHED'}

class GRAPH_OT_emo_reset_bezier_curve(bpy.types.Operator):
    bl_idname = "graph.emo_reset_bezier_curve"
    bl_label = "Reset Bezier Curve"
    bl_description = "Reset Bezier curve to default"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        bezier_editor.reset_curve(context)
        return {'FINISHED'}

class GRAPH_OT_emo_save_bezier_preset(bpy.types.Operator):
    bl_idname = "graph.emo_save_bezier_preset"
    bl_label = "Save Bezier Preset"
    bl_description = "Save current Bezier curve as preset"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        ok = bezier_editor.save_preset(context)
        if not ok:
            self.report({'WARNING'}, "Failed to save preset")
            return {'CANCELLED'}
        self.report({'INFO'}, "Preset saved")
        return {'FINISHED'}

class GRAPH_OT_emo_bezier_mouse_edit(bpy.types.Operator):
    bl_idname = "graph.emo_bezier_mouse_edit"
    bl_label = "Bezier Mouse Edit"
    bl_description = "Edit Bezier curve handles with mouse"
    bl_options = {'REGISTER'}
    
    def invoke(self, context, event):
        # 初始化UI数据以便鼠标交互
        region = context.region
        if region:
            # 模拟绘制以初始化UI数据
            bezier_editor.draw(context)
        
        # 添加绘制处理器
        bezier_editor.draw_handler = bpy.types.SpaceGraphEditor.draw_handler_add(
            bezier_editor.draw, (context,), 'WINDOW', 'POST_PIXEL'
        )
        
        bezier_editor.is_editing = True
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        if not bezier_editor.is_editing:
            # 清理绘制处理器
            if bezier_editor.draw_handler:
                bpy.types.SpaceGraphEditor.draw_handler_remove(bezier_editor.draw_handler, 'WINDOW')
                bezier_editor.draw_handler = None
            return {'CANCELLED'}
        
        if event.type == 'ESC' and event.value == 'PRESS':
            bezier_editor.is_editing = False
            bezier_editor.drag_handle = None
            # 清理绘制处理器
            if bezier_editor.draw_handler:
                bpy.types.SpaceGraphEditor.draw_handler_remove(bezier_editor.draw_handler, 'WINDOW')
                bezier_editor.draw_handler = None
            return {'CANCELLED'}
        
        if event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
            return {'PASS_THROUGH'}
        
        # 处理鼠标事件
        if bezier_editor.handle_mouse_event(context, event):
            # 重绘以更新显示
            if context.area:
                context.area.tag_redraw()
            return {'RUNNING_MODAL'}
        
        return {'PASS_THROUGH'}

# 绘制回调
def draw_bezier_editor(self, context):
    # 对于N面板的预览操作符，我们需要特殊处理
    if hasattr(self, 'bl_idname') and self.bl_idname == 'graph.emo_bezier_preview':
        # 在N面板预览中绘制
        import gpu
        import blf
        from gpu_extras.batch import batch_for_shader
        
        # 获取当前区域
        region = context.region
        if not region:
            return
        
        # 绘制贝塞尔曲线预览
        bezier_editor.draw(context, region)
    else:
        # 对于其他情况，保持原有逻辑
        region = context.region
        if region.type == 'WINDOW':
            bezier_editor.draw(context, region)

# N面板贝塞尔编辑器
class GRAPH_PT_emo_bezier_editor(bpy.types.Panel):
    bl_label = _("Bezier Editor")
    bl_idname = "GRAPH_PT_emo_bezier_editor"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'E_Motion'
    
    @classmethod
    def poll(cls, context):
        # 在编辑模式下不显示
        edit_mode = getattr(context.window_manager, "emo_edit_mode", False)
        if edit_mode:
            return False
        
        # 只在选中一条动画曲线时显示
        if context.space_data and context.space_data.type == 'GRAPH_EDITOR':
            obj = context.active_object
            if obj and obj.animation_data and obj.animation_data.action:
                selected_fcurves = [fcu for fcu in obj.animation_data.action.fcurves if fcu.select]
                return len(selected_fcurves) == 1
        return False
    
    def draw(self, context):
        layout = self.layout
        
        # 绘制贝塞尔曲线编辑器
        col = layout.column()
        
        # 显示当前贝塞尔曲线参数
        col.separator()
        col.label(text=_("Control Points Parameters:"))
        row = col.row()
        row.prop(context.window_manager, "emo_bezier_h1x", text="H1 X")
        row.prop(context.window_manager, "emo_bezier_h1y", text="H1 Y")
        
        row = col.row()
        row.prop(context.window_manager, "emo_bezier_h2x", text="H2 X")
        row.prop(context.window_manager, "emo_bezier_h2y", text="H2 Y")
        
        # 手动编辑按钮
        col.separator()
        col.operator("graph.emo_bezier_mouse_edit", text=_("Manual Edit Control Points"))
        
        # 插值类型控制
        col.separator()
        col.label(text=_("Interpolation Type:"))
        row = col.row(align=True)
        row.operator("graph.emo_open_interpolation_pie", text=_("Interpolation"), icon='IPO_LINEAR')
        row.operator("graph.emo_open_easing_pie", text=_("Easing"), icon='IPO_EASE_IN')
        row.operator("graph.emo_open_dynamic_pie", text=_("Dynamic Effects"), icon='IPO_BOUNCE')
        
        # 操作按钮
        col.separator()
        
        row = col.row(align=True)
        row.operator("graph.emo_apply_bezier_curve", text=_("Apply Curve"))
        row.operator("graph.emo_reset_bezier_curve", text=_("Reset"))
        
        row = col.row(align=True)
        row.operator("graph.emo_mirror_bezier_curve", text=_("Mirror"))
        row.operator("graph.emo_save_bezier_preset", text=_("Save Preset"))
        
        # 缩放控制
        row = col.row(align=True)
        row.operator("graph.emo_bezier_zoom", text=_("Zoom In")).mode = "IN"
        row.operator("graph.emo_bezier_zoom", text=_("Zoom Out")).mode = "OUT"
        row.operator("graph.emo_bezier_zoom", text=_("Center")).mode = "CENTER"
        
        # 提示信息
        col.separator()
        col.label(text=_("Operation Tips:"))
        col.label(text=_("Click to enter edit mode"))
        col.label(text=_("Drag blue (H1) and orange (H2) control points"))
        col.label(text=_("Press ESC to exit edit mode"))
        col.label(text=_("Adjust parameters and click Apply Curve"))
        col.label(text=_("Click interpolation type buttons to open pie menu"))

# 时间线N面板贝塞尔编辑器
class DOPESHEET_PT_emo_bezier_editor(bpy.types.Panel):
    bl_label = _("Bezier Editor")
    bl_idname = "DOPESHEET_PT_emo_bezier_editor"
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'E_Motion'
    
    @classmethod
    def poll(cls, context):
        # 在时间线模式下显示
        return context.space_data.mode == 'TIMELINE'
    
    def draw(self, context):
        layout = self.layout
        
        # 绘制贝塞尔曲线编辑器
        col = layout.column()
        
        # 显示当前贝塞尔曲线参数
        col.separator()
        col.label(text=_("Control Points Parameters:"))
        row = col.row()
        row.prop(context.window_manager, "emo_bezier_h1x", text="H1 X")
        row.prop(context.window_manager, "emo_bezier_h1y", text="H1 Y")
        
        row = col.row()
        row.prop(context.window_manager, "emo_bezier_h2x", text="H2 X")
        row.prop(context.window_manager, "emo_bezier_h2y", text="H2 Y")
        
        # 手动编辑按钮
        col.separator()
        col.operator("graph.emo_bezier_mouse_edit", text=_("Manual Edit Control Points"))
        
        # 操作按钮
        col.separator()
        
        row = col.row(align=True)
        row.operator("graph.emo_apply_bezier_curve", text=_("Apply Curve"))
        row.operator("graph.emo_reset_bezier_curve", text=_("Reset"))
        
        row = col.row(align=True)
        row.operator("graph.emo_mirror_bezier_curve", text=_("Mirror"))
        row.operator("graph.emo_save_bezier_preset", text=_("Save Preset"))
        
        # 提示信息
        col.separator()
        col.label(text=_("Operation Tips:"))
        col.label(text=_("Click to enter edit mode"))
        col.label(text=_("Drag blue (H1) and orange (H2) control points"))
        col.label(text=_("Press ESC to exit edit mode"))
        col.label(text=_("Adjust parameters and click Apply Curve"))

# 编辑模式N面板
class GRAPH_PT_emo_edit_mode(bpy.types.Panel):
    bl_label = _("Edit")
    bl_idname = "GRAPH_PT_emo_edit_mode"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'E_Motion'
    
    @classmethod
    def poll(cls, context):
        # 只在编辑模式下显示
        edit_mode = getattr(context.window_manager, "emo_edit_mode", False)
        return edit_mode
    
    def draw(self, context):
        layout = self.layout
        
        # 显示当前编辑模式状态
        layout.label(text=_("Edit Mode"), icon='EDITMODE_HLT')
        layout.separator()
        
        # 显示活动对象信息
        obj = context.active_object
        if obj and obj.animation_data and obj.animation_data.action:
            layout.label(text=_("Active Object") + f": {obj.name}")
            
            # 显示活动修改器或贝塞尔曲线信息
            active_mod = _get_edit_mode_state('emo_active_modifier')
            active_curve = _get_edit_mode_state('emo_active_curve')
            
            if active_mod:
                layout.label(text=_("Active Modifier") + f": {active_mod.name}")
                # 显示修改器参数
                col = layout.column(align=True)
                col.label(text=_("Modifier Parameters:"))
                # 这里需要根据修改器类型显示不同的参数
                col.label(text=_("Type") + f": {active_mod.type}")
                
                # 通用参数
                if hasattr(active_mod, 'use_restricted_range'):
                    col.prop(active_mod, 'use_restricted_range', text=_("Restrict Frame Range"))
                if hasattr(active_mod, 'frame_start') and hasattr(active_mod, 'frame_end'):
                    row = col.row(align=True)
                    row.prop(active_mod, 'frame_start', text=_("Frame Start"))
                    row.prop(active_mod, 'frame_end', text=_("Frame End"))
                if hasattr(active_mod, 'use_additive'):
                    col.prop(active_mod, 'use_additive', text=_("Additive Mode"))
                
                # 根据修改器类型显示不同的参数
                if active_mod.type == 'FNGENERATOR':
                    if hasattr(active_mod, 'function_type'):
                        col.prop(active_mod, 'function_type', text=_("Function Type"))
                    if hasattr(active_mod, 'amplitude'):
                        col.prop(active_mod, 'amplitude', text=_("Amplitude"))
                    if hasattr(active_mod, 'phase'):
                        col.prop(active_mod, 'phase', text=_("Phase"))
                    if hasattr(active_mod, 'frequency'):
                        col.prop(active_mod, 'frequency', text=_("Frequency"))
                    if hasattr(active_mod, 'offset'):
                        col.prop(active_mod, 'offset', text=_("Offset"))
                elif active_mod.type == 'NOISE':
                    if hasattr(active_mod, 'scale'):
                        col.prop(active_mod, 'scale', text=_("Scale"))
                    if hasattr(active_mod, 'strength'):
                        col.prop(active_mod, 'strength', text=_("Strength"))
                    if hasattr(active_mod, 'phase'):
                        col.prop(active_mod, 'phase', text=_("Phase"))
                    if hasattr(active_mod, 'offset'):
                        col.prop(active_mod, 'offset', text=_("Offset"))
                    if hasattr(active_mod, 'seed'):
                        col.prop(active_mod, 'seed', text=_("Seed"))
                    if hasattr(active_mod, 'noise_basis'):
                        col.prop(active_mod, 'noise_basis', text=_("Noise Basis"))
                    if hasattr(active_mod, 'noise_scale'):
                        col.prop(active_mod, 'noise_scale', text=_("Noise Scale"))
                elif active_mod.type == 'STEPPED':
                    if hasattr(active_mod, 'frame_step'):
                        col.prop(active_mod, 'frame_step', text=_("Frame Step"))
                    if hasattr(active_mod, 'interpolation'):
                        col.prop(active_mod, 'interpolation', text=_("Interpolation"))
                elif active_mod.type == 'LIMITS':
                    if hasattr(active_mod, 'min_x'):
                        col.prop(active_mod, 'min_x', text=_("Minimum X"))
                    if hasattr(active_mod, 'max_x'):
                        col.prop(active_mod, 'max_x', text=_("Maximum X"))
                    if hasattr(active_mod, 'min_y'):
                        col.prop(active_mod, 'min_y', text=_("Minimum Y"))
                    if hasattr(active_mod, 'max_y'):
                        col.prop(active_mod, 'max_y', text=_("Maximum Y"))
                    if hasattr(active_mod, 'use_min_x'):
                        col.prop(active_mod, 'use_min_x', text=_("Use Minimum X"))
                    if hasattr(active_mod, 'use_max_x'):
                        col.prop(active_mod, 'use_max_x', text=_("Use Maximum X"))
                    if hasattr(active_mod, 'use_min_y'):
                        col.prop(active_mod, 'use_min_y', text=_("Use Minimum Y"))
                    if hasattr(active_mod, 'use_max_y'):
                        col.prop(active_mod, 'use_max_y', text=_("Use Maximum Y"))
                elif active_mod.type == 'CYCLES':
                    if hasattr(active_mod, 'before'):
                        col.prop(active_mod, 'before', text=_("Before"))
                    if hasattr(active_mod, 'after'):
                        col.prop(active_mod, 'after', text=_("After"))
                    if hasattr(active_mod, 'offset'):
                        col.prop(active_mod, 'offset', text=_("Offset"))
                # 其他类型的修改器参数
                elif active_mod.type == 'ENVELOPE':
                    if hasattr(active_mod, 'points'):
                        col.label(text="控制点:")
                        for i, point in enumerate(active_mod.points):
                            box = col.box()
                            box.label(text=f"点 {i+1}")
                            if hasattr(point, 'frame'):
                                box.prop(point, 'frame', text="帧")
                            if hasattr(point, 'value'):
                                box.prop(point, 'value', text="值")
                # 显示所有其他可用参数
                col.separator()
                col.label(text="其他参数:")
                # 动态显示所有其他属性
                for attr in dir(active_mod):
                    # 跳过私有属性和方法
                    if not attr.startswith('_') and not callable(getattr(active_mod, attr)):
                        # 跳过已经显示过的属性
                        if attr not in ['name', 'type', 'use_restricted_range', 'frame_start', 'frame_end', 'use_additive', 
                                     'function_type', 'amplitude', 'phase', 'frequency', 'offset', 
                                     'scale', 'strength', 'seed', 'noise_basis', 'noise_scale', 
                                     'frame_step', 'interpolation', 
                                     'min_x', 'max_x', 'min_y', 'max_y', 'use_min_x', 'use_max_x', 'use_min_y', 'use_max_y', 
                                     'before', 'after', 'points']:
                            try:
                                col.prop(active_mod, attr)
                            except Exception:
                                pass
            elif active_curve:
                layout.label(text="活动贝塞尔曲线")
                # 显示贝塞尔曲线编辑器
                col = layout.column(align=True)
                col.label(text="控制点参数:")
                row = col.row()
                row.prop(context.window_manager, "emo_bezier_h1x", text="H1 X")
                row.prop(context.window_manager, "emo_bezier_h1y", text="H1 Y")
                row = col.row()
                row.prop(context.window_manager, "emo_bezier_h2x", text="H2 X")
                row.prop(context.window_manager, "emo_bezier_h2y", text="H2 Y")
                
                # 插值类型控制
                col.separator()
                col.label(text="插值类型:")
                row = col.row(align=True)
                row.operator("graph.emo_open_interpolation_pie", text="插值", icon='IPO_LINEAR')
                row.operator("graph.emo_open_easing_pie", text="缓动", icon='IPO_EASE_IN')
                row.operator("graph.emo_open_dynamic_pie", text="动态效果", icon='IPO_BOUNCE')
                
                col.operator("graph.emo_bezier_mouse_edit", text="手动编辑控制点 (点击后可拖拽控制点)")
                col.operator("graph.emo_apply_bezier_curve", text="应用曲线")
        else:
            layout.label(text="无活动动画数据")
        
        # 退出编辑模式按钮
        layout.separator()
        layout.operator("graph.emo_toggle_edit_mode", text="退出编辑模式", icon='X')

# 插值类型pie菜单
class GRAPH_MT_emo_interpolation_pie(Menu):
    bl_idname = "GRAPH_MT_emo_interpolation_pie"
    bl_label = "插值类型"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        
        # 常量
        op = pie.operator("graph.emo_set_interpolation", text="常量", icon='IPO_CONSTANT')
        op.mode = 'CONSTANT'
        
        # 线性
        op = pie.operator("graph.emo_set_interpolation", text="线性", icon='IPO_LINEAR')
        op.mode = 'LINEAR'
        
        # 贝塞尔
        op = pie.operator("graph.emo_set_interpolation", text="贝塞尔", icon='IPO_BEZIER')
        op.mode = 'BEZIER'

# 缓动类型pie菜单
class GRAPH_MT_emo_easing_pie(Menu):
    bl_idname = "GRAPH_MT_emo_easing_pie"
    bl_label = "缓动类型"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        
        # 正弦
        op = pie.operator("graph.emo_set_easing", text="正弦", icon='IPO_SINE')
        op.mode = 'SINE'
        
        # 二次型
        op = pie.operator("graph.emo_set_easing", text="二次型", icon='IPO_QUAD')
        op.mode = 'QUAD'
        
        # 三次型
        op = pie.operator("graph.emo_set_easing", text="三次型", icon='IPO_CUBIC')
        op.mode = 'CUBIC'
        
        # 四次型
        op = pie.operator("graph.emo_set_easing", text="四次型", icon='IPO_QUART')
        op.mode = 'QUART'
        
        # 五次型
        op = pie.operator("graph.emo_set_easing", text="五次型", icon='IPO_QUINT')
        op.mode = 'QUINT'
        
        # 指数型
        op = pie.operator("graph.emo_set_easing", text="指数型", icon='IPO_EXPO')
        op.mode = 'EXPO'
        
        # 圆状
        op = pie.operator("graph.emo_set_easing", text="圆状", icon='IPO_CIRC')
        op.mode = 'CIRC'

# 动态效果pie菜单
class GRAPH_MT_emo_dynamic_pie(Menu):
    bl_idname = "GRAPH_MT_emo_dynamic_pie"
    bl_label = "动态效果"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        
        # 回弹
        op = pie.operator("graph.emo_set_dynamic", text="回弹", icon='IPO_BACK')
        op.mode = 'BACK'
        
        # 弹跳
        op = pie.operator("graph.emo_set_dynamic", text="弹跳", icon='IPO_BOUNCE')
        op.mode = 'BOUNCE'
        
        # 弹性
        op = pie.operator("graph.emo_set_dynamic", text="弹性", icon='IPO_ELASTIC')
        op.mode = 'ELASTIC'

# 打开插值pie菜单的操作符
class GRAPH_OT_emo_open_interpolation_pie(Operator):
    bl_idname = "graph.emo_open_interpolation_pie"
    bl_label = "Open Interpolation Pie"
    bl_description = "Open interpolation pie menu"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name="GRAPH_MT_emo_interpolation_pie")
        return {'FINISHED'}

# 打开缓动pie菜单的操作符
class GRAPH_OT_emo_open_easing_pie(Operator):
    bl_idname = "graph.emo_open_easing_pie"
    bl_label = "Open Easing Pie"
    bl_description = "Open easing pie menu"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name="GRAPH_MT_emo_easing_pie")
        return {'FINISHED'}

# 打开动态效果pie菜单的操作符
class GRAPH_OT_emo_open_dynamic_pie(Operator):
    bl_idname = "graph.emo_open_dynamic_pie"
    bl_label = "Open Dynamic Pie"
    bl_description = "Open dynamic effects pie menu"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name="GRAPH_MT_emo_dynamic_pie")
        return {'FINISHED'}

# 设置缓动类型的操作符
class GRAPH_OT_emo_set_easing(Operator):
    bl_idname = "graph.emo_set_easing"
    bl_label = "Set Easing"
    bl_description = "Set easing type for selected keyframes"
    bl_options = {'REGISTER', 'UNDO'}
    
    mode: bpy.props.StringProperty()
    
    def execute(self, context):
        try:
            # 尝试使用Blender内置的插值类型操作符
            bpy.ops.graph.interpolation_type(type=self.mode)
        except RuntimeError:
            # 如果操作符失败（例如在编辑模式下），直接设置关键帧属性
            for fc, sel_keys, _ in _selected_fcurves_with_selected_keys(context):
                for kp in sel_keys:
                    kp.interpolation = self.mode
        return {'FINISHED'}

# 设置动态效果的操作符
class GRAPH_OT_emo_set_dynamic(Operator):
    bl_idname = "graph.emo_set_dynamic"
    bl_label = "Set Dynamic"
    bl_description = "Set dynamic effect for selected keyframes"
    bl_options = {'REGISTER', 'UNDO'}
    
    mode: bpy.props.StringProperty()
    
    def execute(self, context):
        try:
            # 尝试使用Blender内置的插值类型操作符
            bpy.ops.graph.interpolation_type(type=self.mode)
        except RuntimeError:
            # 如果操作符失败（例如在编辑模式下），直接设置关键帧属性
            for fc, sel_keys, _ in _selected_fcurves_with_selected_keys(context):
                for kp in sel_keys:
                    kp.interpolation = self.mode
        return {'FINISHED'}

# 曲线预览操作符
class GRAPH_OT_emo_bezier_preview(bpy.types.Operator):
    bl_idname = "graph.emo_bezier_preview"
    bl_label = "Bezier Preview"
    bl_options = {'INTERNAL'}
    
    def execute(self, context):
        return {'FINISHED'}
    
    def draw(self, context):
        # 绘制贝塞尔曲线预览
        # 这里我们使用一个简单的方法，通过绘制一个曲线的可视化表示
        layout = self.layout
        
        # 创建一个大的预览区域
        preview_box = layout.box()
        preview_box.scale_y = 3.0
        
        # 获取贝塞尔参数
        h1x = context.window_manager.emo_bezier_h1x
        h1y = context.window_manager.emo_bezier_h1y
        h2x = context.window_manager.emo_bezier_h2x
        h2y = context.window_manager.emo_bezier_h2y
        
        # 显示当前参数
        col = layout.column()
        col.label(text=f"H1: ({h1x:.3f}, {h1y:.3f})")
        col.label(text=f"H2: ({h2x:.3f}, {h2y:.3f})")

# 绘制回调函数用于N面板
def draw_bezier_in_panel(self, context):
    # 检查是否是我们的贝塞尔编辑器面板
    if self.bl_idname not in ['GRAPH_PT_emo_bezier_editor', 'DOPESHEET_PT_emo_bezier_editor']:
        return
    
    # 获取贝塞尔参数
    h1x = context.window_manager.emo_bezier_h1x
    h1y = context.window_manager.emo_bezier_h1y
    h2x = context.window_manager.emo_bezier_h2x
    h2y = context.window_manager.emo_bezier_h2y
    
    # 绘制贝塞尔曲线预览
    # 注意：在Blender的面板绘制中，我们不能直接使用GPU绘制
    # 所以我们使用布局来创建一个可视化表示
    layout = self.layout
    
    # 创建预览区域
    preview_box = layout.box()
    preview_box.scale_y = 3.0
    
    # 显示曲线参数
    col = layout.column()
    col.label(text="曲线参数:")
    row = col.row()
    row.prop(context.window_manager, "emo_bezier_h1x", text="H1 X")
    row.prop(context.window_manager, "emo_bezier_h1y", text="H1 Y")
    row = col.row()
    row.prop(context.window_manager, "emo_bezier_h2x", text="H2 X")
    row.prop(context.window_manager, "emo_bezier_h2y", text="H2 Y")

# 缩放操作符
class GRAPH_OT_emo_bezier_zoom(bpy.types.Operator):
    bl_idname = "graph.emo_bezier_zoom"
    bl_label = "Bezier Zoom"
    bl_description = "Zoom the bezier editor"
    
    mode: bpy.props.EnumProperty(
        items=[
            ('IN', 'In', ''),
            ('OUT', 'Out', ''),
            ('CENTER', 'Center', ''),
        ]
    )
    
    def execute(self, context):
        if self.mode == 'IN':
            bezier_editor.zoom = min(6.0, bezier_editor.zoom * 1.2)
        elif self.mode == 'OUT':
            bezier_editor.zoom = max(0.2, bezier_editor.zoom / 1.2)
        else:
            bezier_editor.zoom = 1.0
            bezier_editor.pan_x = 0.0
            bezier_editor.pan_y = 0.0
        return {'FINISHED'}

# 插值设置操作符
class GRAPH_OT_emo_set_interpolation(bpy.types.Operator):
    bl_idname = "graph.emo_set_interpolation"
    bl_label = "Set Interpolation"
    bl_description = "Set interpolation mode for selected keyframes"
    
    mode: bpy.props.StringProperty()
    
    def execute(self, context):
        try:
            # 尝试使用Blender内置的插值类型操作符
            bpy.ops.graph.interpolation_type(type=self.mode)
        except RuntimeError:
            # 如果操作符失败（例如在编辑模式下），直接设置关键帧属性
            for fc, sel_keys, _ in _selected_fcurves_with_selected_keys(context):
                for kp in sel_keys:
                    kp.interpolation = self.mode
        return {'FINISHED'}

class GRAPH_OT_emo_toggle_edit_mode(bpy.types.Operator):
    bl_idname = "graph.emo_toggle_edit_mode"
    bl_label = "Toggle Edit Mode"
    bl_description = "Toggle edit mode for curve modifiers and bezier curves"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        # 切换编辑模式状态
        if not hasattr(context.window_manager, "emo_edit_mode"):
            context.window_manager.emo_edit_mode = False
        context.window_manager.emo_edit_mode = not context.window_manager.emo_edit_mode
        
        # 如果进入编辑模式，启动鼠标侦测
        if context.window_manager.emo_edit_mode:
            # 清除活动状态
            _set_edit_mode_state('emo_active_modifier', None)
            _set_edit_mode_state('emo_active_curve', None)
            # 添加鼠标侦测
            bpy.ops.graph.emo_edit_mode_mouse_detect('INVOKE_DEFAULT')
        
        # 重绘区域
        if context.area:
            context.area.tag_redraw()
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return self.execute(context)

class GRAPH_OT_emo_edit_mode_mouse_detect(bpy.types.Operator):
    bl_idname = "graph.emo_edit_mode_mouse_detect"
    bl_label = "Edit Mode Mouse Detect"
    bl_description = "Detect mouse clicks on modifiers and bezier curves in edit mode"
    bl_options = {'REGISTER', 'UNDO'}
    
    def invoke(self, context, event):
        # 检查是否在编辑模式
        if not getattr(context.window_manager, "emo_edit_mode", False):
            return {'CANCELLED'}
        
        # 添加模态处理
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        # 检查是否在编辑模式
        if not getattr(context.window_manager, "emo_edit_mode", False):
            return {'CANCELLED'}
        
        # 处理鼠标点击
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            # 检查鼠标点击是否发生在UI区域（比如N面板）
            is_ui_click = False
            for r in context.area.regions:
                if r.type == 'UI' and r.x <= event.mouse_x <= r.x + r.width and r.y <= event.mouse_y <= r.y + r.height:
                    is_ui_click = True
                    break
            
            # 如果是UI点击，不执行曲线分析
            if is_ui_click:
                return {'PASS_THROUGH'}
            
            # 获取鼠标位置
            region = context.region
            if not region:
                return {'PASS_THROUGH'}
            
            # 获取view2d从region
            view2d = region.view2d
            if not view2d:
                return {'PASS_THROUGH'}
            
            mouse_x, mouse_y = event.mouse_region_x, event.mouse_region_y
            
            # 转换鼠标位置到帧值
            try:
                frame, value = view2d.region_to_view(mouse_x, mouse_y)
            except Exception:
                return {'PASS_THROUGH'}
            
            # 分析修改器和贝塞尔曲线
            self.analyze_curves(context, frame)
            
            # 重绘区域
            if context.area:
                context.area.tag_redraw()
        
        # 处理ESC键
        if event.type == 'ESC' and event.value == 'PRESS':
            # 退出编辑模式
            context.window_manager.emo_edit_mode = False
            _set_edit_mode_state('emo_active_modifier', None)
            _set_edit_mode_state('emo_active_curve', None)
            if context.area:
                context.area.tag_redraw()
            return {'CANCELLED'}
        
        return {'PASS_THROUGH'}
    
    def analyze_curves(self, context, frame):
        """分析曲线，检测鼠标点击位置是否在修改器或贝塞尔曲线范围内"""
        obj = context.active_object
        if not obj or not obj.animation_data or not obj.animation_data.action:
            return
        
        action = obj.animation_data.action
        
        # 清除之前的活动状态
        _set_edit_mode_state('emo_active_modifier', None)
        _set_edit_mode_state('emo_active_curve', None)
        
        # 分析每个曲线
        for fcu in action.fcurves:
            # 分析修改器
            for mod in fcu.modifiers:
                # 跳过步进和噪声修改器
                if mod.type in {'STEPPED', 'NOISE'}:
                    continue
                
                # 检查修改器是否有帧范围限制
                if hasattr(mod, 'use_restricted_range') and mod.use_restricted_range:
                    if hasattr(mod, 'frame_start') and hasattr(mod, 'frame_end'):
                        if mod.frame_start <= frame <= mod.frame_end:
                            _set_edit_mode_state('emo_active_modifier', mod)
                            return
                elif hasattr(mod, 'use_range') and mod.use_range:
                    if hasattr(mod, 'frame_start') and hasattr(mod, 'frame_end'):
                        if mod.frame_start <= frame <= mod.frame_end:
                            _set_edit_mode_state('emo_active_modifier', mod)
                            return
            
            # 分析贝塞尔曲线（两个关键帧之间）
            keyframes = fcu.keyframe_points
            if len(keyframes) >= 2:
                for i in range(len(keyframes) - 1):
                    kp1 = keyframes[i]
                    kp2 = keyframes[i + 1]
                    
                    # 检查关键帧之间是否是贝塞尔插值
                    if kp1.interpolation == 'BEZIER' or kp2.interpolation == 'BEZIER':
                        if kp1.co[0] <= frame <= kp2.co[0]:
                            # 取消所有曲线的所有关键帧选择（包括控制点和手柄）
                            for fcu_all in action.fcurves:
                                for kp_all in fcu_all.keyframe_points:
                                    kp_all.select_control_point = False
                                    kp_all.select_left_handle = False
                                    kp_all.select_right_handle = False
                            # 只选择当前贝塞尔曲线段的两个关键帧
                            kp1.select_control_point = True
                            kp2.select_control_point = True
                            # 设置活动曲线
                            _set_edit_mode_state('emo_active_curve', fcu)
                            # 添加控制台输出追踪
                            print(f"[E_Motion] 选中贝塞尔曲线段: 帧范围 {kp1.co[0]:.2f}-{kp2.co[0]:.2f}, 关键帧索引 {i} 和 {i+1}")
                            # 尝试设置活动关键帧（在Blender中，活动关键帧通常通过选择来管理）
                            print(f"[E_Motion] 已选择关键帧 {i} 和 {i+1}")
                            return

# 时间线头部绘制
def draw_timeline_header(self, context):
    sp = context.space_data
    if not sp or sp.type != 'DOPESHEET_EDITOR' or sp.mode != 'TIMELINE':
        return
    row = self.layout.row(align=True)
    row.operator("graph.emo_bezier_editor", text="", icon='CURVE_BEZCURVE')

# 曲线编辑器头部绘制
def draw_graph_header(self, context):
    sp = context.space_data
    if not sp or sp.type != 'GRAPH_EDITOR':
        return
    row = self.layout.row(align=True)
    row.operator("graph.emo_toggle_edit_mode", text="", icon='EDITMODE_HLT')

# 绘制回调函数
def draw_bezier_preview_in_panel():
    # 绘制贝塞尔曲线预览
    context = bpy.context
    if not context:
        return
    
    # 检查当前区域是否是N面板
    region = context.region
    if not region or region.type != 'UI':
        return
    
    # 检查是否在曲线编辑器或时间线编辑器中
    area = context.area
    if not area or area.type not in {'GRAPH_EDITOR', 'DOPESHEET_EDITOR'}:
        return
    
    # 获取当前面板
    panels = [p for p in context.area.panels if p.type == 'UI']
    if not panels:
        return
    
    # 绘制贝塞尔曲线
    h1x = context.window_manager.emo_bezier_h1x
    h1y = context.window_manager.emo_bezier_h1y
    h2x = context.window_manager.emo_bezier_h2x
    h2y = context.window_manager.emo_bezier_h2y
    
    # 计算预览区域的位置和大小
    # 注意：这需要根据实际的面板布局进行调整
    # 这里我们使用一个简单的实现，实际使用时可能需要更复杂的逻辑

# 注册函数
def register():
    # 注册窗口管理器属性
    bpy.types.WindowManager.emo_bezier_h1x = bpy.props.FloatProperty(
        name="H1 X",
        default=0.333,
        min=0.0,
        max=1.0
    )
    bpy.types.WindowManager.emo_bezier_h1y = bpy.props.FloatProperty(
        name="H1 Y",
        default=0.0,
        min=-2.0,
        max=2.0
    )
    bpy.types.WindowManager.emo_bezier_h2x = bpy.props.FloatProperty(
        name="H2 X",
        default=0.667,
        min=0.0,
        max=1.0
    )
    bpy.types.WindowManager.emo_bezier_h2y = bpy.props.FloatProperty(
        name="H2 Y",
        default=1.0,
        min=-2.0,
        max=2.0
    )
    # 注册编辑模式相关属性
    bpy.types.WindowManager.emo_edit_mode = bpy.props.BoolProperty(
        name="Edit Mode",
        default=False
    )
    
    # 注册pie菜单
    bpy.utils.register_class(GRAPH_MT_emo_interpolation_pie)
    bpy.utils.register_class(GRAPH_MT_emo_easing_pie)
    bpy.utils.register_class(GRAPH_MT_emo_dynamic_pie)
    
    # 注册操作符
    bpy.utils.register_class(GRAPH_OT_emo_bezier_editor)
    bpy.utils.register_class(GRAPH_OT_emo_apply_bezier_curve)
    bpy.utils.register_class(GRAPH_OT_emo_mirror_bezier_curve)
    bpy.utils.register_class(GRAPH_OT_emo_reset_bezier_curve)
    bpy.utils.register_class(GRAPH_OT_emo_save_bezier_preset)
    bpy.utils.register_class(GRAPH_OT_emo_bezier_mouse_edit)
    bpy.utils.register_class(GRAPH_OT_emo_bezier_preview)
    bpy.utils.register_class(GRAPH_OT_emo_bezier_zoom)
    bpy.utils.register_class(GRAPH_OT_emo_set_interpolation)
    bpy.utils.register_class(GRAPH_OT_emo_open_interpolation_pie)
    bpy.utils.register_class(GRAPH_OT_emo_open_easing_pie)
    bpy.utils.register_class(GRAPH_OT_emo_open_dynamic_pie)
    bpy.utils.register_class(GRAPH_OT_emo_set_easing)
    bpy.utils.register_class(GRAPH_OT_emo_set_dynamic)
    bpy.utils.register_class(GRAPH_OT_emo_toggle_edit_mode)
    bpy.utils.register_class(GRAPH_OT_emo_edit_mode_mouse_detect)
    
    # 添加快捷键映射
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.get('Graph Editor')
    if not km:
        km = wm.keyconfigs.addon.keymaps.new(name='Graph Editor')
    kmi = km.keymap_items.new('graph.emo_toggle_edit_mode', 'TAB', 'PRESS', shift=True)
    
    # 注册面板
    bpy.utils.register_class(GRAPH_PT_emo_bezier_editor)
    bpy.utils.register_class(DOPESHEET_PT_emo_bezier_editor)
    bpy.utils.register_class(GRAPH_PT_emo_edit_mode)
    
    # 注册绘制回调
    bpy.types.DOPESHEET_HT_header.append(draw_timeline_header)
    bpy.types.GRAPH_HT_header.append(draw_graph_header)
    
    print("[E_Motion] Bezier editor registered")

def unregister():
    # 注销面板
    try:
        bpy.utils.unregister_class(GRAPH_PT_emo_bezier_editor)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(DOPESHEET_PT_emo_bezier_editor)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(GRAPH_PT_emo_edit_mode)
    except Exception:
        pass
    
    # 注销pie菜单
    try:
        bpy.utils.unregister_class(GRAPH_MT_emo_interpolation_pie)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(GRAPH_MT_emo_easing_pie)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(GRAPH_MT_emo_dynamic_pie)
    except Exception:
        pass
    
    # 注销操作符
    try:
        bpy.utils.unregister_class(GRAPH_OT_emo_bezier_editor)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(GRAPH_OT_emo_apply_bezier_curve)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(GRAPH_OT_emo_mirror_bezier_curve)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(GRAPH_OT_emo_reset_bezier_curve)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(GRAPH_OT_emo_save_bezier_preset)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(GRAPH_OT_emo_bezier_mouse_edit)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(GRAPH_OT_emo_bezier_preview)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(GRAPH_OT_emo_bezier_zoom)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(GRAPH_OT_emo_set_interpolation)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(GRAPH_OT_emo_open_interpolation_pie)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(GRAPH_OT_emo_open_easing_pie)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(GRAPH_OT_emo_open_dynamic_pie)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(GRAPH_OT_emo_set_easing)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(GRAPH_OT_emo_set_dynamic)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(GRAPH_OT_emo_toggle_edit_mode)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(GRAPH_OT_emo_edit_mode_mouse_detect)
    except Exception:
        pass
    
    # 移除头部绘制
    try:
        bpy.types.DOPESHEET_HT_header.remove(draw_timeline_header)
    except Exception:
        pass
    try:
        bpy.types.GRAPH_HT_header.remove(draw_graph_header)
    except Exception:
        pass
    
    # 移除快捷键映射
    try:
        wm = bpy.context.window_manager
        km = wm.keyconfigs.addon.keymaps.get('Graph Editor')
        if km:
            for kmi in km.keymap_items:
                if kmi.idname == 'graph.emo_toggle_edit_mode':
                    km.keymap_items.remove(kmi)
                    break
    except Exception:
        pass
    
    # 删除窗口管理器属性
    if hasattr(bpy.types.WindowManager, "emo_bezier_h1x"):
        delattr(bpy.types.WindowManager, "emo_bezier_h1x")
    if hasattr(bpy.types.WindowManager, "emo_bezier_h1y"):
        delattr(bpy.types.WindowManager, "emo_bezier_h1y")
    if hasattr(bpy.types.WindowManager, "emo_bezier_h2x"):
        delattr(bpy.types.WindowManager, "emo_bezier_h2x")
    if hasattr(bpy.types.WindowManager, "emo_bezier_h2y"):
        delattr(bpy.types.WindowManager, "emo_bezier_h2y")
    # 删除编辑模式相关属性
    if hasattr(bpy.types.WindowManager, "emo_edit_mode"):
        delattr(bpy.types.WindowManager, "emo_edit_mode")
    
    print("[E_Motion] Bezier editor unregistered")
