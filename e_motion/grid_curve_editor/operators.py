import bpy
from bpy.types import Operator
from .properties import get_grid_cache, clear_grid_selection, frame_to_cell, value_to_cell, cell_to_frame
from .generator import ModifierPresetGenerator


class GRAPH_OT_emo_grid_interact(Operator):
    bl_idname = "graph.emo_grid_interact"
    bl_label = "Grid Interact"
    bl_description = "Interact with grid cells - hover to highlight, click/drag to select and apply preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    _timer = None
    _last_hover = None
    
    def modal(self, context, event):
        props = context.scene.emo_grid_props
        cache = get_grid_cache()
        
        region = None
        for r in context.area.regions:
            if r.type == 'WINDOW':
                region = r
                break
        
        if not region:
            return {'PASS_THROUGH'}
        
        view2d = region.view2d
        mouse_x, mouse_y = event.mouse_region_x, event.mouse_region_y
        
        if mouse_x < 0 or mouse_y < 0 or mouse_x > region.width or mouse_y > region.height:
            return {'PASS_THROUGH'}
        
        try:
            frame, value = view2d.region_to_view(mouse_x, mouse_y)
            
            vis_x_min, vis_y_min = view2d.region_to_view(0, 0)
            vis_x_max, vis_y_max = view2d.region_to_view(region.width, region.height)
            
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
                return {'PASS_THROUGH'}
            
            # 计算视图范围
            frame_range = vis_x_max - vis_x_min
            value_range = vis_y_max - vis_y_min
            
            if frame_range <= 0 or value_range <= 0:
                return {'PASS_THROUGH'}
            
            # 计算网格列数和行数
            num_cols = int(frame_range / x_step) + 1
            num_rows = int(value_range / y_step) + 1
            
            # 确保至少有基本的网格线
            num_cols = max(1, num_cols)
            num_rows = max(1, num_rows)
            
            # 计算单元格坐标
            cell_x = int((frame - vis_x_min) / x_step)
            cell_y = int((value - vis_y_min) / y_step)
            
            cell_x = max(0, min(cell_x, num_cols - 1))
            cell_y = max(0, min(cell_y, num_rows - 1))
            

            
            if event.type == 'MOUSEMOVE':
                # 导入全局变量
                from .ui import is_grid_mode
                
                # 只有在网格模式下才处理悬停和选择
                if is_grid_mode:
                    # 不按鼠标左键时，只显示当前悬停的单元格（最小格子）
                    if not cache.get('is_selecting'):
                        cache['hover_cell'] = (cell_x, cell_y)

                    # 按鼠标左键时，更新选择区域
                    elif cache.get('is_selecting'):
                        cache['selection_end'] = (cell_x, cell_y)

                    
                    context.area.tag_redraw()
                else:
                    # 在非网格模式下，清除悬停状态
                    cache['hover_cell'] = None
                
                return {'PASS_THROUGH'}
            
            elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':

                cache['is_selecting'] = True
                cache['selection_start'] = (cell_x, cell_y)
                cache['selection_end'] = (cell_x, cell_y)
                return {'RUNNING_MODAL'}
            
            elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':

                cache['is_selecting'] = False
                
                if cache['selection_start'] and cache['selection_end']:
                    start = cache['selection_start']
                    end = cache['selection_end']
                    

                    
                    # 检查是否有拖拽（开始和结束位置不同）
                    if start == end:
                        # 没有拖拽，只选择当前悬停的单元格
                        new_cells = [(cell_x, cell_y)]

                        
                        # 检查是否是双击
                        if hasattr(self, '_last_click_time'):
                            import time
                            current_time = time.time()
                            if current_time - self._last_click_time < 0.3:

                                # 双击执行修改器
                                cache['selected_cells'] = new_cells
                                # 获取场景的帧范围
                                scene = context.scene
                                scene_frame_start = scene.frame_start
                                scene_frame_end = scene.frame_end

                                self.apply_preset_to_selection(context, props, cache, scene_frame_start, scene_frame_end, -5, 5)
                                # 退出选择模式
                                try:
                                    from .ui import is_grid_mode, active_preset
                                    is_grid_mode = False
                                    active_preset = None
                                except ImportError:
                                    print("[E_Motion] Error importing UI variables")
                                cache['selected_cells'] = []
                                cache['hover_cell'] = None
                                cache['is_selecting'] = False
                                context.area.tag_redraw()
                                return {'FINISHED'}
                        # 记录单击时间
                        import time
                        self._last_click_time = time.time()
                    else:
                        # 有拖拽，选择多个单元格
                        min_x = min(start[0], end[0])
                        max_x = max(start[0], end[0])
                        min_y = min(start[1], end[1])
                        max_y = max(start[1], end[1])
                        
                        new_cells = [(x, y) for x in range(min_x, max_x + 1)
                                    for y in range(min_y, max_y + 1)]

                        
                        # 左键框选拖拽后自动执行修改器
                        cache['selected_cells'] = new_cells
                        # 获取场景的帧范围
                        scene = context.scene
                        scene_frame_start = scene.frame_start
                        scene_frame_end = scene.frame_end

                        self.apply_preset_to_selection(context, props, cache, scene_frame_start, scene_frame_end, -5, 5)
                        # 退出选择模式
                        try:
                            from .ui import is_grid_mode, active_preset
                            is_grid_mode = False
                            active_preset = None
                        except ImportError:
                            print("[E_Motion] Error importing UI variables")
                        cache['selected_cells'] = []
                        cache['hover_cell'] = None
                        cache['is_selecting'] = False
                        context.area.tag_redraw()
                        return {'FINISHED'}
                    
                    if event.shift:
                        existing = set(cache['selected_cells'])
                        cache['selected_cells'] = list(existing.union(set(new_cells)))

                    elif event.ctrl:
                        existing = set(cache['selected_cells'])
                        cache['selected_cells'] = list(existing - set(new_cells))

                    else:
                        cache['selected_cells'] = new_cells

                
                cache['selection_start'] = None
                cache['selection_end'] = None
                context.area.tag_redraw()
                # 不要立即返回FINISHED，保持网格模式活动
                return {'RUNNING_MODAL'}
            
            elif event.type == 'RIGHTMOUSE' and event.value == 'PRESS':

                cache['selected_cells'] = []
                cache['hover_cell'] = None
                context.area.tag_redraw()
                return {'CANCELLED'}
            
            elif event.type == 'ESC':

                cache['hover_cell'] = None
                cache['is_selecting'] = False
                context.area.tag_redraw()
                return {'CANCELLED'}
            
            elif event.type in {'RET', 'NUMPAD_ENTER'} and event.value == 'PRESS':

                # 导入全局变量来更新状态
                try:
                    from .ui import is_grid_mode, active_preset
                    is_grid_mode = False
                    active_preset = None
                except ImportError:
                    print("[E_Motion] Error importing UI variables")
                
                cache['selected_cells'] = []
                cache['hover_cell'] = None
                cache['is_selecting'] = False
                context.area.tag_redraw()
                return {'FINISHED'}
        except Exception as e:
            # 处理异常
            pass
        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        props = context.scene.emo_grid_props
        cache = get_grid_cache()
        
        print("[E_Motion] Grid interact invoked")
        
        region = None
        for r in context.area.regions:
            if r.type == 'WINDOW':
                region = r
                break
        
        if not region:
            print("[E_Motion] No window region found")
            return {'CANCELLED'}
        
        view2d = region.view2d
        mouse_x, mouse_y = event.mouse_region_x, event.mouse_region_y
        
        try:
            frame, value = view2d.region_to_view(mouse_x, mouse_y)
            
            vis_x_min, vis_y_min = view2d.region_to_view(0, 0)
            vis_x_max, vis_y_max = view2d.region_to_view(region.width, region.height)
            
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
                return {'CANCELLED'}
            
            # 计算视图范围
            frame_range = vis_x_max - vis_x_min
            value_range = vis_y_max - vis_y_min
            
            if frame_range <= 0 or value_range <= 0:
                return {'CANCELLED'}
            
            # 计算网格列数和行数
            num_cols = int(frame_range / x_step) + 1
            num_rows = int(value_range / y_step) + 1
            
            # 确保至少有基本的网格线
            num_cols = max(1, num_cols)
            num_rows = max(1, num_rows)
            
            # 计算单元格坐标
            cell_x = int((frame - vis_x_min) / x_step)
            cell_y = int((value - vis_y_min) / y_step)
            
            cell_x = max(0, min(cell_x, num_cols - 1))
            cell_y = max(0, min(cell_y, num_rows - 1))
            

            
            # 初始化缓存，但不立即开始选择
            cache['is_selecting'] = False
            cache['selection_start'] = None
            cache['selection_end'] = None
            cache['hover_cell'] = (cell_x, cell_y)
            
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        except Exception as e:

            return {'CANCELLED'}
    
    def apply_preset_to_selection(self, context, props, cache, frame_start, frame_end, value_min, value_max):
        region = None
        for r in context.area.regions:
            if r.type == 'WINDOW':
                region = r
                break
        
        if not region:
            return
        
        view2d = region.view2d
        selected_cells = cache.get('selected_cells', [])
        
        if not selected_cells:
            
            return
        
        obj = context.active_object
        if not obj or not obj.animation_data or not obj.animation_data.action:
            
            return
        
        try:
            preset = context.scene.emo_modifier_preset
            preset_type = cache.get('current_preset', 'SINE_FULL')
            preset.preset_type = preset_type
            preset.amplitude = props.amplitude
            preset.phase = props.phase
            preset.frequency = props.frequency
            preset.step_size = props.step_size
            

            
            # 计算选中区域的边界
            min_x = min(cell[0] for cell in selected_cells)
            max_x = max(cell[0] for cell in selected_cells)
            min_y = min(cell[1] for cell in selected_cells)
            max_y = max(cell[1] for cell in selected_cells)
            
            scene = context.scene
            scene_frame_start = scene.frame_start
            scene_frame_end = scene.frame_end
            scene_frame_range = scene_frame_end - scene_frame_start
            
            # 计算当前视口的网格范围
            vis_x_min, vis_y_min = view2d.region_to_view(0, 0)
            vis_x_max, vis_y_max = view2d.region_to_view(region.width, region.height)
            
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
            frame_per_cell = x_step
            value_per_cell = y_step
            
            # 计算帧范围 - 基于选中的单元格，确保与栅格对齐
            # 计算实际的帧范围，确保从整数帧开始和结束

            # 调整计算，确保帧范围正确反映用户选择的区域
            # 使用网格步长的整数倍来计算帧范围，确保与网格对齐
            start_frame = vis_x_min + min_x * frame_per_cell
            end_frame = vis_x_min + (max_x + 1) * frame_per_cell
            
            # 确保坐标对齐到网格线
            start_frame = math.floor(start_frame / frame_per_cell) * frame_per_cell
            end_frame = math.ceil(end_frame / frame_per_cell) * frame_per_cell

            
            # 确保帧范围从1开始
            if start_frame < 1:
                start_frame = 1
            if end_frame < 1:
                end_frame = 1

            
            # 计算值范围 - 基于选中的单元格

            # 根据用户需求，高亮区域的值应该是固定的
            # 我们需要基于网格坐标来计算固定的值范围
            
            # 计算视口的总行数
            view_height = vis_y_max - vis_y_min
            num_rows = int(view_height / value_per_cell) + 1

            
            # 计算选中区域的网格行数
            selected_rows = max_y - min_y + 1

            
            # 计算选中区域对应的值范围
            # 与draw.py中的计算方法完全一致
            # 基于视口的实际最小值和网格步长计算
            v1 = vis_y_min + min_y * value_per_cell
            v2 = vis_y_min + (max_y + 1) * value_per_cell
            
            # 确保坐标对齐到网格线
            import math
            v1 = math.floor(v1 / value_per_cell) * value_per_cell
            v2 = math.ceil(v2 / value_per_cell) * value_per_cell
            
            # 确保值范围正确
            start_value = min(v1, v2)
            end_value = max(v1, v2)

            
            # 移除值范围的限制，允许用户选择任意值范围

            
            cell_range = (start_frame, end_frame)
            value_range = (start_value, end_value)
            

            # 计算幅值和偏移量
            amplitude = (end_value - start_value) / 2
            offset = (start_value + end_value) / 2

            
            # 记录选中区域到属性，以防缩放视口时改变活动区域的位置
            props.selected_frame_start = int(start_frame)
            props.selected_frame_end = int(end_frame)
            props.selected_value_min = start_value
            props.selected_value_max = end_value
            
            fcurves = [fcu for fcu in obj.animation_data.action.fcurves if fcu.select]
            if not fcurves:
                fcurves = obj.animation_data.action.fcurves
            

            
            # 检查是否是叠加类修改器（步进和噪波）
            is_overlay_preset = preset.preset_type in {'STEPPED_LINEAR', 'NOISE'}
            
            for fcu in fcurves:
                # 对于非叠加类修改器，执行覆盖检查
                if not is_overlay_preset:
                    ModifierPresetGenerator.remove_overlapping_modifiers(fcu, start_frame, end_frame)
                mod = ModifierPresetGenerator.apply_preset(fcu, preset, cell_range, value_range, context)
                ModifierPresetGenerator.remove_zero_range_modifiers(fcu)
                if mod:
                    # 处理mod存在的情况
                    pass
            cache['selected_cells'] = []

        except Exception as e:

            import traceback
            traceback.print_exc()


class GRAPH_OT_emo_set_preset(Operator):
    bl_idname = "graph.emo_set_preset"
    bl_label = "Set Preset"
    bl_description = "Set current modifier preset"
    bl_options = {'REGISTER'}
    
    preset_type: bpy.props.StringProperty(default='SINE_FULL')
    
    def execute(self, context):
        props = context.scene.emo_grid_props
        cache = get_grid_cache()
        cache['current_preset'] = self.preset_type

        return {'FINISHED'}


class GRAPH_OT_emo_clear_grid_selection(Operator):
    bl_idname = "graph.emo_clear_grid_selection"
    bl_label = "Clear Grid Selection"
    bl_description = "Clear all selected cells"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        clear_grid_selection()
        context.area.tag_redraw()
        print("[E_Motion] Grid selection cleared")
        self.report({'INFO'}, "Grid selection cleared")
        return {'FINISHED'}


class GRAPH_OT_emo_auto_detect_range(Operator):
    bl_idname = "graph.emo_auto_detect_range"
    bl_label = "Auto Detect Range"
    bl_description = "Automatically detect frame range from selected fcurves"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        obj = context.active_object
        
        if not obj or not obj.animation_data or not obj.animation_data.action:
            self.report({'WARNING'}, "No active object with animation")
            return {'CANCELLED'}
        
        fcurves = [fcu for fcu in obj.animation_data.action.fcurves if fcu.select]
        
        if not fcurves:
            fcurves = obj.animation_data.action.fcurves
        
        if not fcurves:
            self.report({'WARNING'}, "No fcurves found")
            return {'CANCELLED'}
        
        min_frame = float('inf')
        max_frame = float('-inf')
        min_value = float('inf')
        max_value = float('-inf')
        
        for fcu in fcurves:
            for kp in fcu.keyframe_points:
                min_frame = min(min_frame, kp.co.x)
                max_frame = max(max_frame, kp.co.x)
                min_value = min(min_value, kp.co.y)
                max_value = max(max_value, kp.co.y)
        
        if min_frame == float('inf') or max_frame == float('-inf'):
            self.report({'WARNING'}, "No keyframes found")
            return {'CANCELLED'}
        
        props = context.scene.emo_grid_props
        
        value_padding = (max_value - min_value) * 0.1 if max_value != min_value else 1.0
        
        props.frame_start = int(min_frame)
        props.frame_end = int(max_frame) + 1
        props.value_min = min_value - value_padding
        props.value_max = max_value + value_padding
        

        
        context.area.tag_redraw()
        self.report({'INFO'}, f"Range set: frames {props.frame_start}-{props.frame_end}")
        return {'FINISHED'}


class GRAPH_OT_emo_start_grid_interaction(Operator):
    bl_idname = "graph.emo_start_grid_interaction"
    bl_label = "Start Grid Interaction"
    bl_description = "Start interacting with grid cells"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        print("[E_Motion] Starting grid interaction")
        bpy.ops.graph.emo_grid_interact('INVOKE_DEFAULT')
        return {'FINISHED'}


classes = (
    GRAPH_OT_emo_grid_interact,
    GRAPH_OT_emo_set_preset,
    GRAPH_OT_emo_clear_grid_selection,
    GRAPH_OT_emo_auto_detect_range,
    GRAPH_OT_emo_start_grid_interaction,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    print("[E_Motion] Grid operators registered")


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("[E_Motion] Grid operators unregistered")
