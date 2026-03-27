import bpy
import gpu
from gpu_extras.batch import batch_for_shader
import time


vertex_shader = """
in vec2 pos;
in float t;

out float v_t;

void main()
{
    v_t = t;
    gl_Position = vec4(pos, 0.0, 1.0);
}
"""

fragment_shader = """
uniform float u_time;
uniform float u_alpha;

in float v_t;
out vec4 fragColor;

void main()
{
    float flow = u_time * 0.8 + v_t * 6.283;
    vec3 rgb = 0.5 + 0.5 * cos(flow + vec3(0.0, 2.094, 4.189));
    fragColor = vec4(rgb, u_alpha);
}
"""


_glow_handler = None
_shader = None


def draw_callback():
    global _shader
    
    if _shader is None:
        return
    
    try:
        ctx = bpy.context
        space = ctx.space_data
        
        if not space or space.type != 'GRAPH_EDITOR':
            return
        
        obj = ctx.active_object
        if not obj or not obj.animation_data:
            return
        
        action = obj.animation_data.action
        if not action:
            return
        
        fcurves = [fcu for fcu in action.fcurves if fcu.select]
        if not fcurves:
            return
        
        region = None
        for r in ctx.area.regions:
            if r.type == 'WINDOW':
                region = r
                break
        
        if not region:
            return
        
        t_now = time.time()
        
        for fcu in fcurves:
            draw_fcurve_glow(fcu, t_now, _shader, region)
            
    except Exception as e:
        print(f"E_Motion draw error: {e}")


def draw_fcurve_glow(fcu, t_now, shader, region):
    try:
        pts = fcu.keyframe_points
        if not pts:
            return
        
        view2d = region.view2d
        
        x_min, y_min = view2d.region_to_view(0, 0)
        x_max, y_max = view2d.region_to_view(region.width, region.height)
        
        verts = []
        ts = []
        
        n = 150
        for i in range(n + 1):
            t = i / n
            
            frame = x_min + t * (x_max - x_min)
            value = fcu.evaluate(frame)
            
            screen_x, screen_y = view2d.view_to_region(frame, value, clip=False)
            
            nx = screen_x / region.width * 2 - 1
            ny = screen_y / region.height * 2 - 1
            
            verts.append((nx, ny))
            ts.append(t)
        
        if len(verts) < 2:
            return
        
        for width, alpha in [(10.0, 0.12), (6.0, 0.25), (3.0, 0.5), (1.5, 0.9)]:
            batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": verts, "t": ts})
            
            shader.bind()
            shader.uniform_float("u_time", t_now % 100)
            shader.uniform_float("u_alpha", alpha)
            
            gpu.state.line_width_set(width)
            gpu.state.blend_set('ALPHA')
            batch.draw(shader)
        
        gpu.state.line_width_set(1)
        gpu.state.blend_set('NONE')
        
    except Exception as e:
        print(f"E_Motion fcurve draw error: {e}")


def register_glow():
    global _glow_handler, _shader
    
    if _glow_handler is not None:
        return
    
    try:
        _shader = gpu.types.GPUShader(vertex_shader, fragment_shader)
        _glow_handler = bpy.types.SpaceGraphEditor.draw_handler_add(
            draw_callback, (), 'WINDOW', 'POST_PIXEL'
        )
        print("E_Motion: Glow registered successfully")
    except Exception as e:
        print(f"E_Motion Glow Error: {e}")


def unregister_glow():
    global _glow_handler, _shader
    
    if _glow_handler is not None:
        try:
            bpy.types.SpaceGraphEditor.draw_handler_remove(_glow_handler, 'WINDOW')
        except Exception:
            pass
        _glow_handler = None
    
    _shader = None


def toggle_glow(enabled):
    if enabled:
        register_glow()
    else:
        unregister_glow()


def register():
    pass


def unregister():
    unregister_glow()
