import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from .properties import get_grid_cache
# 导入编辑模式状态
from .bezier_editor import _get_edit_mode_state


shader_vertex = """
in vec2 pos;
in vec4 color;
out vec4 v_color;
void main()
{
    v_color = color;
    gl_Position = vec4(pos, 0.0, 1.0);
}
"""

shader_fragment = """
in vec4 v_color;
out vec4 fragColor;
void main()
{
    fragColor = v_color;
}
"""

_shader = None
_handler = None


def get_shader():
    global _shader
    if _shader is None:
        try:
            _shader = gpu.types.GPUShader(shader_vertex, shader_fragment)

        except Exception as e:
            # 处理异常
            _shader = None
    return _shader


def view_to_screen(x, y, region):
    try:
        sx, sy = region.view2d.view_to_region(x, y, clip=False)
        nx = sx / region.width * 2 - 1
        ny = sy / region.height * 2 - 1
        return nx, ny
    except Exception as e:
        # 处理异常
        return None, None


def draw_callback():
    try:
        ctx = bpy.context
        space = ctx.space_data
        
        if not space or space.type != 'GRAPH_EDITOR':
            return
        
        region = None
        for r in ctx.area.regions:
            if r.type == 'WINDOW':
                region = r
                break
        
        if not region:
            return
        
        props = ctx.scene.emo_grid_props
        if not props.show_grid:
            return
        
        # 导入全局变量
        from .ui import is_grid_mode
        
        # 检查是否在编辑模式
        edit_mode = getattr(ctx.window_manager, "emo_edit_mode", False)
        
        # 如果在编辑模式，绘制选中区域的高亮
        if edit_mode:
            draw_edit_mode_highlight(region, ctx)
        # 只有在网格模式下才绘制选择和悬停效果
        elif is_grid_mode:
            draw_grid(region, props)
        else:
            # 在非网格模式下，只绘制基本网格，不绘制选择和悬停效果
            draw_basic_grid(region, props)
        
    except Exception as e:
        # 处理异常
        pass

def draw_basic_grid(region, props):
    shader = get_shader()
    if not shader:

        return
    
    view2d = region.view2d
    
    try:
        vis_x_min, vis_y_min = view2d.region_to_view(0, 0)
        vis_x_max, vis_y_max = view2d.region_to_view(region.width, region.height)
    except Exception as e:
        # 处理异常
        return
    
    # 使用 Blender 原生图表编辑器网格规则
    import math
    
    verts = []
    colors = []
    
    # 计算 X 方向（时间轴）网格步长 - 基于视口和时间的相对大小
    # 根据视口宽度自动调整网格步长，确保网格均匀分布
    view_width = vis_x_max - vis_x_min
    if view_width < 10.0:
        x_step = 0.5
    elif view_width < 50.0:
        x_step = 1.0
    elif view_width < 200.0:
        x_step = 2.0
    elif view_width < 1000.0:
        x_step = 5.0
    else:
        x_step = 10.0
    
    # 计算 Y 方向（值轴）网格步长 - 基于值范围
    view_height = vis_y_max - vis_y_min
    if view_height < 5.0:
        y_step = 0.5
    elif view_height < 25.0:
        y_step = 1.0
    elif view_height < 100.0:
        y_step = 2.0
    elif view_height < 500.0:
        y_step = 5.0
    else:
        y_step = 10.0
    
    # X 方向（时间轴）网格线
    if x_step > 0:
        # 计算第一条可见竖线
        # 确保网格线从帧1开始，而不是帧0
        first_x = math.floor(vis_x_min / x_step) * x_step
        # 调整到从1开始
        if first_x < 1:
            first_x = 1
        # 确保first_x是x_step的整数倍
        if first_x % x_step != 0:
            first_x = math.ceil(first_x / x_step) * x_step
        x = first_x
        
        while x <= vis_x_max:
            x1, y1 = view_to_screen(x, vis_y_min, region)
            x2, y2 = view_to_screen(x, vis_y_max, region)
            
            if x1 is not None and x2 is not None:
                # 主网格线（每5步）
                if abs(x % (x_step * 5)) < 0.001:
                    verts.extend([(x1, y1), (x2, y2)])
                    colors.extend([(0.5, 0.5, 0.5, 0.8), (0.5, 0.5, 0.5, 0.8)])
                else:
                    verts.extend([(x1, y1), (x2, y2)])
                    colors.extend([(0.3, 0.3, 0.3, 0.6), (0.3, 0.3, 0.3, 0.6)])
            
            x += x_step
    
    # Y 方向（值轴）网格线
    if y_step > 0:
        # 计算第一条可见横线
        first_y = math.floor(vis_y_min / y_step) * y_step
        y = first_y
        
        while y <= vis_y_max:
            x1, y1 = view_to_screen(vis_x_min, y, region)
            x2, y2 = view_to_screen(vis_x_max, y, region)
            
            if x1 is not None and x2 is not None:
                # 主网格线（每5步）
                if abs(y % (y_step * 5)) < 0.001:
                    verts.extend([(x1, y1), (x2, y2)])
                    colors.extend([(0.5, 0.5, 0.5, 0.8), (0.5, 0.5, 0.5, 0.8)])
                else:
                    verts.extend([(x1, y1), (x2, y2)])
                    colors.extend([(0.3, 0.3, 0.3, 0.6), (0.3, 0.3, 0.3, 0.6)])
            
            y += y_step
    
    if verts and colors:
        batch = batch_for_shader(shader, 'LINES', {"pos": verts, "color": colors})
        shader.bind()
        gpu.state.line_width_set(1.0)
        gpu.state.blend_set('ALPHA')
        batch.draw(shader)
        gpu.state.blend_set('NONE')
    else:
        # 处理其他情况
        pass

def draw_grid(region, props):
    shader = get_shader()
    if not shader:

        return
    
    view2d = region.view2d
    
    try:
        vis_x_min, vis_y_min = view2d.region_to_view(0, 0)
        vis_x_max, vis_y_max = view2d.region_to_view(region.width, region.height)
    except Exception as e:
        # 处理异常
        return
    
    # 使用 Blender 原生图表编辑器网格规则
    import math
    
    verts = []
    colors = []
    
    # 计算 X 方向（时间轴）网格步长 - 基于视口和时间的相对大小
    # 根据视口宽度自动调整网格步长，确保网格均匀分布
    view_width = vis_x_max - vis_x_min
    if view_width < 10.0:
        x_step = 0.5
    elif view_width < 50.0:
        x_step = 1.0
    elif view_width < 200.0:
        x_step = 2.0
    elif view_width < 1000.0:
        x_step = 5.0
    else:
        x_step = 10.0
    
    # 计算 Y 方向（值轴）网格步长 - 基于值范围
    view_height = vis_y_max - vis_y_min
    if view_height < 5.0:
        y_step = 0.5
    elif view_height < 25.0:
        y_step = 1.0
    elif view_height < 100.0:
        y_step = 2.0
    elif view_height < 500.0:
        y_step = 5.0
    else:
        y_step = 10.0
    
    # X 方向（时间轴）网格线
    if x_step > 0:
        # 计算第一条可见竖线
        # 确保网格线从帧1开始，而不是帧0
        first_x = math.floor(vis_x_min / x_step) * x_step
        # 调整到从1开始
        if first_x < 1:
            first_x = 1
        # 确保first_x是x_step的整数倍
        if first_x % x_step != 0:
            first_x = math.ceil(first_x / x_step) * x_step
        x = first_x
        
        while x <= vis_x_max:
            x1, y1 = view_to_screen(x, vis_y_min, region)
            x2, y2 = view_to_screen(x, vis_y_max, region)
            
            if x1 is not None and x2 is not None:
                # 主网格线（每5步）
                if abs(x % (x_step * 5)) < 0.001:
                    verts.extend([(x1, y1), (x2, y2)])
                    colors.extend([(0.5, 0.5, 0.5, 0.8), (0.5, 0.5, 0.5, 0.8)])
                else:
                    verts.extend([(x1, y1), (x2, y2)])
                    colors.extend([(0.3, 0.3, 0.3, 0.6), (0.3, 0.3, 0.3, 0.6)])
            
            x += x_step
    
    # Y 方向（值轴）网格线
    if y_step > 0:
        # 计算第一条可见横线
        first_y = math.floor(vis_y_min / y_step) * y_step
        y = first_y
        
        while y <= vis_y_max:
            x1, y1 = view_to_screen(vis_x_min, y, region)
            x2, y2 = view_to_screen(vis_x_max, y, region)
            
            if x1 is not None and x2 is not None:
                # 主网格线（每5步）
                if abs(y % (y_step * 5)) < 0.001:
                    verts.extend([(x1, y1), (x2, y2)])
                    colors.extend([(0.5, 0.5, 0.5, 0.8), (0.5, 0.5, 0.5, 0.8)])
                else:
                    verts.extend([(x1, y1), (x2, y2)])
                    colors.extend([(0.3, 0.3, 0.3, 0.6), (0.3, 0.3, 0.3, 0.6)])
            
            y += y_step
    
    # 计算网格列数和行数
    frame_range = vis_x_max - vis_x_min
    value_range = vis_y_max - vis_y_min
    
    num_cols = int(frame_range / x_step) + 1 if x_step > 0 else 1
    num_rows = int(value_range / y_step) + 1 if y_step > 0 else 1
    
    # 确保至少有基本的网格线
    num_cols = max(1, num_cols)
    num_rows = max(1, num_rows)
    
    # 设置 frame_start, frame_end, value_min, value_max
    frame_start = vis_x_min
    frame_end = vis_x_max
    value_min = vis_y_min
    value_max = vis_y_max
    
    if verts and colors:
        batch = batch_for_shader(shader, 'LINES', {"pos": verts, "color": colors})
        shader.bind()
        gpu.state.line_width_set(1.0)
        gpu.state.blend_set('ALPHA')
        batch.draw(shader)
        gpu.state.blend_set('NONE')
    else:
        # 处理其他情况
        pass

    draw_selection(region, props, num_cols, num_rows, frame_start, frame_end, value_min, value_max)


def draw_selection(region, props, num_cols, num_rows, frame_start, frame_end, value_min, value_max):
    # 使用与 draw_grid 相同的网格范围和步长计算逻辑
    view2d = region.view2d
    
    try:
        vis_x_min, vis_y_min = view2d.region_to_view(0, 0)
        vis_x_max, vis_y_max = view2d.region_to_view(region.width, region.height)
    except Exception as e:
        # 处理异常
        return
    
    # 使用 Blender 原生图表编辑器网格规则
    import math
    
    # 计算 X 方向（时间轴）网格步长 - 基于视口和时间的相对大小
    # 根据视口宽度自动调整网格步长，确保网格均匀分布
    view_width = vis_x_max - vis_x_min
    if view_width < 10.0:
        x_step = 0.5
    elif view_width < 50.0:
        x_step = 1.0
    elif view_width < 200.0:
        x_step = 2.0
    elif view_width < 1000.0:
        x_step = 5.0
    else:
        x_step = 10.0
    
    # 计算 Y 方向（值轴）网格步长 - 基于值范围
    view_height = vis_y_max - vis_y_min
    if view_height < 5.0:
        y_step = 0.5
    elif view_height < 25.0:
        y_step = 1.0
    elif view_height < 100.0:
        y_step = 2.0
    elif view_height < 500.0:
        y_step = 5.0
    else:
        y_step = 10.0
    
    if x_step <= 0 or y_step <= 0:
        return
    
    # 计算网格步长
    frame_step = x_step
    value_step = y_step
    cache = get_grid_cache()
    shader = get_shader()
    
    if not shader:
        return
    
    tiffany_fill = (0.039, 0.729, 0.71, 0.35)  # 蒂芙尼蓝色
    tiffany_line = (0.039, 0.729, 0.71, 0.95)
    hover_fill = (0.039, 0.729, 0.71, 0.2)
    hover_line = (0.039, 0.729, 0.71, 0.6)
    drag_fill = (0.039, 0.729, 0.71, 0.25)
    drag_line = (0.039, 0.729, 0.71, 0.8)
    
    verts = []
    colors = []
    
    # 绘制拖拽选择区域（一体高亮）
    if cache.get('is_selecting') and cache.get('selection_start') and cache.get('selection_end'):
        start = cache['selection_start']
        end = cache['selection_end']
        

        
        min_x = min(start[0], end[0])
        max_x = max(start[0], end[0])
        min_y = min(start[1], end[1])
        max_y = max(start[1], end[1])
        

        
        # 计算拖拽区域的实际坐标
        # 使用固定的网格步长，确保选中区域与栅格对齐
        # 基于视口位置和网格单元格计算绝对坐标
        f1 = vis_x_min + min_x * frame_step
        f2 = vis_x_min + (max_x + 1) * frame_step
        v1 = vis_y_min + min_y * value_step
        v2 = vis_y_min + (max_y + 1) * value_step
        # 确保坐标对齐到网格线
        f1 = math.floor(f1 / frame_step) * frame_step
        f2 = math.ceil(f2 / frame_step) * frame_step
        v1 = math.floor(v1 / value_step) * value_step
        v2 = math.ceil(v2 / value_step) * value_step
        # 确保帧范围从1开始
        if f1 < 1:
            f1 = 1
        # 确保结束帧也大于等于1
        if f2 < 1:
            f2 = 1
        

        
        # 确保坐标正确
        if f1 > f2:
            f1, f2 = f2, f1
        if v1 > v2:
            v1, v2 = v2, v1
        
        # 计算四个角的屏幕坐标
        x1, y1 = view_to_screen(f1, v1, region)
        x2, y2 = view_to_screen(f2, v1, region)
        x3, y3 = view_to_screen(f2, v2, region)
        x4, y4 = view_to_screen(f1, v2, region)
        

        
        if all(coord is not None for coord in [x1, y1, x2, y2, x3, y3, x4, y4]):
            # 绘制拖拽区域填充（两个三角形）
            verts.extend([(x1, y1), (x2, y2), (x3, y3), (x1, y1), (x3, y3), (x4, y4)])
            colors.extend([drag_fill] * 6)
            
            # 绘制拖拽区域边框（矩形）
            verts.extend([(x1, y1), (x2, y2), (x2, y2), (x3, y3), (x3, y3), (x4, y4), (x4, y4), (x1, y1)])
            colors.extend([drag_line] * 8)
            

    
    selected = cache.get('selected_cells', [])

    
    # 绘制选中的单元格（每个单元格单独绘制）
    for cx, cy in selected:
        if 0 <= cx < num_cols and 0 <= cy < num_rows:
            # 计算单元格的实际坐标
            f1 = vis_x_min + cx * frame_step
            f2 = vis_x_min + (cx + 1) * frame_step
            v1 = vis_y_min + cy * value_step
            v2 = vis_y_min + (cy + 1) * value_step
            
            # 确保坐标对齐到网格线
            f1 = math.floor(f1 / frame_step) * frame_step
            f2 = math.ceil(f2 / frame_step) * frame_step
            v1 = math.floor(v1 / value_step) * value_step
            v2 = math.ceil(v2 / value_step) * value_step
            # 确保帧范围从1开始
            if f1 < 1:
                f1 = 1
            
            # 确保坐标正确
            if f1 > f2:
                f1, f2 = f2, f1
            if v1 > v2:
                v1, v2 = v2, v1
            
            # 计算四个角的屏幕坐标
            x1, y1 = view_to_screen(f1, v1, region)
            x2, y2 = view_to_screen(f2, v1, region)
            x3, y3 = view_to_screen(f2, v2, region)
            x4, y4 = view_to_screen(f1, v2, region)
            
            if all(coord is not None for coord in [x1, y1, x2, y2, x3, y3, x4, y4]):
                # 绘制单元格填充（两个三角形）
                verts.extend([(x1, y1), (x2, y2), (x3, y3), (x1, y1), (x3, y3), (x4, y4)])
                colors.extend([tiffany_fill] * 6)
                
                # 绘制单元格边框（矩形）
                verts.extend([(x1, y1), (x2, y2), (x2, y2), (x3, y3), (x3, y3), (x4, y4), (x4, y4), (x1, y1)])
                colors.extend([tiffany_line] * 8)
    
    # 只有在非选择状态下才绘制悬停效果
    if not cache.get('is_selecting'):
        hover = cache.get('hover_cell')
        if hover and hover not in selected:

            cx, cy = hover
            if 0 <= cx < num_cols and 0 <= cy < num_rows:
                # 计算单元格的实际坐标
                # 使用固定的网格步长，确保选中区域与栅格对齐
                # 基于视口位置和网格单元格计算绝对坐标
                f1 = vis_x_min + cx * frame_step
                f2 = vis_x_min + (cx + 1) * frame_step
                v1 = vis_y_min + cy * value_step
                v2 = vis_y_min + (cy + 1) * value_step
                
                # 确保坐标对齐到网格线
                f1 = math.floor(f1 / frame_step) * frame_step
                f2 = math.ceil(f2 / frame_step) * frame_step
                v1 = math.floor(v1 / value_step) * value_step
                v2 = math.ceil(v2 / value_step) * value_step
                # 确保帧范围从1开始
                if f1 < 1:
                    f1 = 1
                
                # 确保坐标正确
                if f1 > f2:
                    f1, f2 = f2, f1
                if v1 > v2:
                    v1, v2 = v2, v1
                

                
                # 计算四个角的屏幕坐标
                x1, y1 = view_to_screen(f1, v1, region)
                x2, y2 = view_to_screen(f2, v1, region)
                x3, y3 = view_to_screen(f2, v2, region)
                x4, y4 = view_to_screen(f1, v2, region)
                

                
                if all(coord is not None for coord in [x1, y1, x2, y2, x3, y3, x4, y4]):
                    # 绘制悬停单元格填充（两个三角形）
                    verts.extend([(x1, y1), (x2, y2), (x3, y3), (x1, y1), (x3, y3), (x4, y4)])
                    colors.extend([hover_fill] * 6)
                    
                    # 绘制悬停单元格边框（矩形）
                    verts.extend([(x1, y1), (x2, y2), (x2, y2), (x3, y3), (x3, y3), (x4, y4), (x4, y4), (x1, y1)])
                    colors.extend([hover_line] * 8)
    
    if verts and colors:

        tris_n = len(verts) // 3 * 3
        if tris_n > 0:
            batch = batch_for_shader(shader, 'TRIS', {"pos": verts[:tris_n], "color": colors[:tris_n]})
            shader.bind()
            gpu.state.blend_set('ALPHA')
            batch.draw(shader)
        
        if len(verts) > tris_n:
            batch = batch_for_shader(shader, 'LINES', {"pos": verts[tris_n:], "color": colors[tris_n:]})
            gpu.state.line_width_set(1.5)
            batch.draw(shader)
        
        gpu.state.blend_set('NONE')
    else:
        # 处理其他情况
        pass


def register():
    global _handler
    if _handler is None:
        _handler = bpy.types.SpaceGraphEditor.draw_handler_add(draw_callback, (), 'WINDOW', 'POST_PIXEL')
        print("[E_Motion] Grid draw registered")


def draw_edit_mode_highlight(region, context):
    """绘制编辑模式下选中区域的高亮"""
    shader = get_shader()
    if not shader:
        return
    
    # 获取活动的修改器或贝塞尔曲线
    active_mod = _get_edit_mode_state('emo_active_modifier')
    active_curve = _get_edit_mode_state('emo_active_curve')
    
    # 绘制高亮区域
    verts = []
    colors = []
    highlight_color = (0.039, 0.729, 0.71, 0.35)  # 蒂芙尼蓝色，半透明
    border_color = (0.039, 0.729, 0.71, 0.95)  # 蒂芙尼蓝色，不透明
    
    view2d = region.view2d
    try:
        vis_x_min, vis_y_min = view2d.region_to_view(0, 0)
        vis_x_max, vis_y_max = view2d.region_to_view(region.width, region.height)
    except Exception:
        return
    
    # 绘制活动修改器的高亮
    if active_mod:
        if hasattr(active_mod, 'frame_start') and hasattr(active_mod, 'frame_end'):
            frame_start = active_mod.frame_start
            frame_end = active_mod.frame_end
            
            # 计算高亮区域的坐标
            x1, y1 = view_to_screen(frame_start, vis_y_min, region)
            x2, y2 = view_to_screen(frame_end, vis_y_min, region)
            x3, y3 = view_to_screen(frame_end, vis_y_max, region)
            x4, y4 = view_to_screen(frame_start, vis_y_max, region)
            
            if all(coord is not None for coord in [x1, y1, x2, y2, x3, y3, x4, y4]):
                # 绘制高亮区域填充
                verts.extend([(x1, y1), (x2, y2), (x3, y3), (x1, y1), (x3, y3), (x4, y4)])
                colors.extend([highlight_color] * 6)
                
                # 绘制高亮区域边框
                verts.extend([(x1, y1), (x2, y2), (x2, y2), (x3, y3), (x3, y3), (x4, y4), (x4, y4), (x1, y1)])
                colors.extend([border_color] * 8)
    
    # 绘制活动贝塞尔曲线的高亮
    elif active_curve:
        keyframes = active_curve.keyframe_points
        if len(keyframes) >= 2:
            # 找到当前选中的关键帧对
            selected_kps = [kp for kp in keyframes if kp.select_control_point]
            if len(selected_kps) == 2:
                kp1, kp2 = selected_kps
                frame1, value1 = kp1.co[0], kp1.co[1]
                frame2, value2 = kp2.co[0], kp2.co[1]
                
                # 计算高亮区域的坐标
                x1, y1 = view_to_screen(frame1, vis_y_min, region)
                x2, y2 = view_to_screen(frame2, vis_y_min, region)
                x3, y3 = view_to_screen(frame2, vis_y_max, region)
                x4, y4 = view_to_screen(frame1, vis_y_max, region)
                
                if all(coord is not None for coord in [x1, y1, x2, y2, x3, y3, x4, y4]):
                    # 绘制高亮区域填充
                    verts.extend([(x1, y1), (x2, y2), (x3, y3), (x1, y1), (x3, y3), (x4, y4)])
                    colors.extend([highlight_color] * 6)
                    
                    # 绘制高亮区域边框
                    verts.extend([(x1, y1), (x2, y2), (x2, y2), (x3, y3), (x3, y3), (x4, y4), (x4, y4), (x1, y1)])
                    colors.extend([border_color] * 8)
    
    if verts and colors:
        # 绘制三角形填充
        tris_n = len(verts) // 3 * 3
        if tris_n > 0:
            batch = batch_for_shader(shader, 'TRIS', {"pos": verts[:tris_n], "color": colors[:tris_n]})
            shader.bind()
            gpu.state.blend_set('ALPHA')
            batch.draw(shader)
        
        # 绘制线条边框
        if len(verts) > tris_n:
            batch = batch_for_shader(shader, 'LINES', {"pos": verts[tris_n:], "color": colors[tris_n:]})
            gpu.state.line_width_set(1.5)
            batch.draw(shader)
        
        gpu.state.blend_set('NONE')


def unregister():
    global _handler
    if _handler is not None:
        try:
            bpy.types.SpaceGraphEditor.draw_handler_remove(_handler, 'WINDOW')
        except Exception as e:
            # 处理异常
            pass
        _handler = None

