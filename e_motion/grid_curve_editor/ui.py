import bpy
from bpy.types import Operator, Menu
from bpy.utils import previews
import os
from .properties import get_grid_cache
from .generator import ModifierPresetGenerator
from ..language import _

# 自定义图标字典
custom_icons = {}

# 注册自定义图标
def register_icons():
    global custom_icons
    
    # 清除现有的图标
    if custom_icons:
        unregister_icons()
    
    # 创建图标预览集合
    pcoll = previews.new()
    
    # 获取图标目录
    icons_dir = os.path.join(os.path.dirname(__file__), '..', 'icons')
    
    # 线性类别图标
    linear_icons = {}
    linear_icons['LINEAR'] = pcoll.load('LINEAR', os.path.join(icons_dir, 'linear.png'), 'IMAGE')
    linear_icons['CONSTANT'] = pcoll.load('CONSTANT', os.path.join(icons_dir, 'constant.png'), 'IMAGE')
    linear_icons['LINEAR_POS'] = pcoll.load('LINEAR_POS', os.path.join(icons_dir, 'linear_pos.png'), 'IMAGE')
    linear_icons['LINEAR_NEG'] = pcoll.load('LINEAR_NEG', os.path.join(icons_dir, 'linear_neg.png'), 'IMAGE')
    
    # 正弦类别图标
    sine_icons = {}
    sine_icons['SINE'] = pcoll.load('SINE', os.path.join(icons_dir, 'sine.png'), 'IMAGE')
    sine_icons['SINE_FULL'] = pcoll.load('SINE_FULL', os.path.join(icons_dir, 'sine_full.png'), 'IMAGE')
    sine_icons['SINE_BOTTOM'] = pcoll.load('SINE_BOTTOM', os.path.join(icons_dir, 'sine_bottom.png'), 'IMAGE')
    sine_icons['SINE_TOP'] = pcoll.load('SINE_TOP', os.path.join(icons_dir, 'sine_top.png'), 'IMAGE')
    sine_icons['SINE_HALF_PERIOD'] = pcoll.load('SINE_HALF_PERIOD', os.path.join(icons_dir, 'sine_half.png'), 'IMAGE')
    
    # 非线性类别图标
    nonlinear_icons = {}
    nonlinear_icons['NONLINEAR'] = pcoll.load('NONLINEAR', os.path.join(icons_dir, 'nonlinear.png'), 'IMAGE')
    nonlinear_icons['SQUARE_ROOT'] = pcoll.load('SQUARE_ROOT', os.path.join(icons_dir, 'square_root.png'), 'IMAGE')
    nonlinear_icons['NATURAL_LOG'] = pcoll.load('NATURAL_LOG', os.path.join(icons_dir, 'natural_log.png'), 'IMAGE')
    
    # 贝塞尔类别图标
    bezier_icons = {}
    bezier_icons['BEZIER'] = pcoll.load('BEZIER', os.path.join(icons_dir, 'bezier.png'), 'IMAGE')
    bezier_icons['CUSTOM_BEZIER'] = pcoll.load('CUSTOM_BEZIER', os.path.join(icons_dir, 'custom_bezier.png'), 'IMAGE')
    
    # 叠加类别图标
    overlay_icons = {}
    overlay_icons['OVERLAY'] = pcoll.load('OVERLAY', os.path.join(icons_dir, 'overlay.png'), 'IMAGE')
    overlay_icons['STEPPED_LINEAR'] = pcoll.load('STEPPED_LINEAR', os.path.join(icons_dir, 'stepped_linear.png'), 'IMAGE')
    overlay_icons['SINE_STEPPED'] = pcoll.load('SINE_STEPPED', os.path.join(icons_dir, 'sine_stepped.png'), 'IMAGE')
    overlay_icons['NOISE'] = pcoll.load('NOISE', os.path.join(icons_dir, 'noise.png'), 'IMAGE')
    
    # 存储图标集合
    custom_icons['LINEAR'] = linear_icons
    custom_icons['SINE'] = sine_icons
    custom_icons['NONLINEAR'] = nonlinear_icons
    custom_icons['BEZIER'] = bezier_icons
    custom_icons['OVERLAY'] = overlay_icons
    custom_icons['pcoll'] = pcoll

# 注销自定义图标
def unregister_icons():
    global custom_icons
    if custom_icons and 'pcoll' in custom_icons:
        previews.remove(custom_icons['pcoll'])
    custom_icons.clear()

# 全局变量跟踪当前激活的预置按钮
active_preset = None
is_grid_mode = False


PRESET_ICONS = {
    'CONSTANT': {'icon': 'DOT', 'label': _('Constant')},
    'LINEAR_POS': {'icon': 'TRIA_UP', 'label': _('Linear') + '+'},
    'LINEAR_NEG': {'icon': 'TRIA_DOWN', 'label': _('Linear') + '-'},
    'SINE_FULL': {'icon': 'MODIFIER', 'label': _('Sine')},
    'SINE_BOTTOM': {'icon': 'TRIA_DOWN', 'label': _('Sine') + ' ' + _('Bottom')},
    'SINE_TOP': {'icon': 'TRIA_UP', 'label': _('Sine') + ' ' + _('Top')},
    'SINE_HALF_PERIOD': {'icon': 'MODIFIER', 'label': _('Sine') + ' ' + _('Half Period')},
    'SQUARE_ROOT': {'icon': 'MODIFIER', 'label': _('Square Root')},
    'NATURAL_LOG': {'icon': 'MODIFIER', 'label': _('Natural Log')},
    'CUSTOM_BEZIER': {'icon': 'MODIFIER', 'label': _('Bezier')},
    'STEPPED_LINEAR': {'icon': 'MODIFIER', 'label': _('Stepped')},
    'SINE_STEPPED': {'icon': 'MODIFIER', 'label': _('Sine') + ' ' + _('Stepped')},
    'NOISE': {'icon': 'MODIFIER', 'label': _('Noise')},
}


# Pie菜单类
class GRAPH_MT_emo_pie_linear(Menu):
    bl_idname = "GRAPH_MT_emo_pie_linear"
    bl_label = _("Linear Presets")

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        
        # 常值
        if 'LINEAR' in custom_icons and 'CONSTANT' in custom_icons['LINEAR']:
            op = pie.operator("graph.emo_toggle_preset", text=_('Constant'), icon_value=custom_icons['LINEAR']['CONSTANT'].icon_id)
        else:
            op = pie.operator("graph.emo_toggle_preset", text=_('Constant'), icon='DOT')
        op.preset_type = 'CONSTANT'
        
        # 线性+
        if 'LINEAR' in custom_icons and 'LINEAR_POS' in custom_icons['LINEAR']:
            op = pie.operator("graph.emo_toggle_preset", text=_('Linear') + '+', icon_value=custom_icons['LINEAR']['LINEAR_POS'].icon_id)
        else:
            op = pie.operator("graph.emo_toggle_preset", text=_('Linear') + '+', icon='TRIA_UP')
        op.preset_type = 'LINEAR_POS'
        
        # 线性-
        if 'LINEAR' in custom_icons and 'LINEAR_NEG' in custom_icons['LINEAR']:
            op = pie.operator("graph.emo_toggle_preset", text=_('Linear') + '-', icon_value=custom_icons['LINEAR']['LINEAR_NEG'].icon_id)
        else:
            op = pie.operator("graph.emo_toggle_preset", text=_('Linear') + '-', icon='TRIA_DOWN')
        op.preset_type = 'LINEAR_NEG'


class GRAPH_MT_emo_pie_sine(Menu):
    bl_idname = "GRAPH_MT_emo_pie_sine"
    bl_label = _("Sine Presets")

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        
        # 正弦 - 上
        if 'SINE' in custom_icons and 'SINE_FULL' in custom_icons['SINE']:
            op = pie.operator("graph.emo_toggle_preset", text=_('Sine'), icon_value=custom_icons['SINE']['SINE_FULL'].icon_id)
        else:
            op = pie.operator("graph.emo_toggle_preset", text=_('Sine'), icon='MODIFIER')
        op.preset_type = 'SINE_FULL'
        
        # 下半正弦 - 下
        if 'SINE' in custom_icons and 'SINE_BOTTOM' in custom_icons['SINE']:
            op = pie.operator("graph.emo_toggle_preset", text=_('Sine') + ' ' + _('Bottom'), icon_value=custom_icons['SINE']['SINE_BOTTOM'].icon_id)
        else:
            op = pie.operator("graph.emo_toggle_preset", text=_('Sine') + ' ' + _('Bottom'), icon='TRIA_DOWN')
        op.preset_type = 'SINE_BOTTOM'
        
        # 上半正弦 - 上
        if 'SINE' in custom_icons and 'SINE_TOP' in custom_icons['SINE']:
            op = pie.operator("graph.emo_toggle_preset", text=_('Sine') + ' ' + _('Top'), icon_value=custom_icons['SINE']['SINE_TOP'].icon_id)
        else:
            op = pie.operator("graph.emo_toggle_preset", text=_('Sine') + ' ' + _('Top'), icon='TRIA_UP')
        op.preset_type = 'SINE_TOP'
        
        # 半周期正弦 - 右
        if 'SINE' in custom_icons and 'SINE_HALF_PERIOD' in custom_icons['SINE']:
            op = pie.operator("graph.emo_toggle_preset", text=_('Sine') + ' ' + _('Half Period'), icon_value=custom_icons['SINE']['SINE_HALF_PERIOD'].icon_id)
        else:
            op = pie.operator("graph.emo_toggle_preset", text=_('Sine') + ' ' + _('Half Period'), icon='MODIFIER')
        op.preset_type = 'SINE_HALF_PERIOD'


class GRAPH_MT_emo_pie_nonlinear(Menu):
    bl_idname = "GRAPH_MT_emo_pie_nonlinear"
    bl_label = _("Nonlinear Presets")

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        
        # 平方根
        if 'NONLINEAR' in custom_icons and 'SQUARE_ROOT' in custom_icons['NONLINEAR']:
            op = pie.operator("graph.emo_toggle_preset", text=_('Square Root'), icon_value=custom_icons['NONLINEAR']['SQUARE_ROOT'].icon_id)
        else:
            op = pie.operator("graph.emo_toggle_preset", text=_('Square Root'), icon='MODIFIER')
        op.preset_type = 'SQUARE_ROOT'
        
        # 对数
        if 'NONLINEAR' in custom_icons and 'NATURAL_LOG' in custom_icons['NONLINEAR']:
            op = pie.operator("graph.emo_toggle_preset", text=_('Natural Log'), icon_value=custom_icons['NONLINEAR']['NATURAL_LOG'].icon_id)
        else:
            op = pie.operator("graph.emo_toggle_preset", text=_('Natural Log'), icon='MODIFIER')
        op.preset_type = 'NATURAL_LOG'


class GRAPH_MT_emo_pie_bezier(Menu):
    bl_idname = "GRAPH_MT_emo_pie_bezier"
    bl_label = _("Bezier Presets")

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        
        # 贝塞尔
        if 'BEZIER' in custom_icons and 'CUSTOM_BEZIER' in custom_icons['BEZIER']:
            op = pie.operator("graph.emo_toggle_preset", text=_('Bezier'), icon_value=custom_icons['BEZIER']['CUSTOM_BEZIER'].icon_id)
        else:
            op = pie.operator("graph.emo_toggle_preset", text=_('Bezier'), icon='MODIFIER')
        op.preset_type = 'CUSTOM_BEZIER'


class GRAPH_MT_emo_pie_overlay(Menu):
    bl_idname = "GRAPH_MT_emo_pie_overlay"
    bl_label = _("Overlay Presets")

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        
        # 步进
        if 'OVERLAY' in custom_icons and 'STEPPED_LINEAR' in custom_icons['OVERLAY']:
            op = pie.operator("graph.emo_toggle_preset", text=_('Stepped'), icon_value=custom_icons['OVERLAY']['STEPPED_LINEAR'].icon_id)
        else:
            op = pie.operator("graph.emo_toggle_preset", text=_('Stepped'), icon='MODIFIER')
        op.preset_type = 'STEPPED_LINEAR'
        
        # 正弦步进
        if 'OVERLAY' in custom_icons and 'SINE_STEPPED' in custom_icons['OVERLAY']:
            op = pie.operator("graph.emo_toggle_preset", text=_('Sine') + ' ' + _('Stepped'), icon_value=custom_icons['OVERLAY']['SINE_STEPPED'].icon_id)
        else:
            op = pie.operator("graph.emo_toggle_preset", text=_('Sine') + ' ' + _('Stepped'), icon='MODIFIER')
        op.preset_type = 'SINE_STEPPED'
        
        # 噪声
        if 'OVERLAY' in custom_icons and 'NOISE' in custom_icons['OVERLAY']:
            op = pie.operator("graph.emo_toggle_preset", text=_('Noise'), icon_value=custom_icons['OVERLAY']['NOISE'].icon_id)
        else:
            op = pie.operator("graph.emo_toggle_preset", text=_('Noise'), icon='MODIFIER')
        op.preset_type = 'NOISE'


# 长按显示pie菜单的操作符
class GRAPH_OT_emo_open_pie(Operator):
    bl_idname = "graph.emo_open_pie"
    bl_label = "Open Pie Menu"
    bl_description = "Open pie menu for preset categories"
    bl_options = {'REGISTER'}
    
    menu_id: bpy.props.StringProperty()
    
    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name=self.menu_id)
        return {'FINISHED'}


class GRAPH_OT_emo_toggle_preset(Operator):
    bl_idname = "graph.emo_toggle_preset"
    bl_label = "Toggle Preset"
    bl_description = "Toggle grid selection mode with preset"
    bl_options = {'REGISTER'}
    
    preset_type: bpy.props.StringProperty(default='SINE_FULL')
    
    def execute(self, context):
        global active_preset, is_grid_mode
        cache = get_grid_cache()
        
        if active_preset == self.preset_type and is_grid_mode:
            # 退出网格模式
            is_grid_mode = False
            active_preset = None
            cache['selected_cells'] = []
            cache['hover_cell'] = None
            context.area.tag_redraw()

        else:
            # 进入网格模式
            is_grid_mode = True
            active_preset = self.preset_type
            cache['current_preset'] = self.preset_type
            # 启动网格交互
            bpy.ops.graph.emo_grid_interact('INVOKE_DEFAULT')

        
        return {'FINISHED'}


class GRAPH_OT_emo_apply_modifier(Operator):
    bl_idname = "graph.emo_apply_modifier"
    bl_label = "Apply Modifier"
    bl_description = "Apply selected modifier preset to selected cells"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        global active_preset, is_grid_mode
        cache = get_grid_cache()
        props = context.scene.emo_grid_props
        
        # 应用修改器到选中的单元格
        selected_cells = cache.get('selected_cells', [])
        if not selected_cells:
            self.report({'WARNING'}, "No cells selected")
            return {'CANCELLED'}
        
        obj = context.active_object
        if not obj or not obj.animation_data or not obj.animation_data.action:
            self.report({'WARNING'}, "No active object with animation")
            return {'CANCELLED'}
        
        try:
            # 获取当前预置
            preset_type = cache.get('current_preset', 'SINE_FULL')
            preset = context.scene.emo_modifier_preset
            preset.preset_type = preset_type
            preset.amplitude = props.amplitude
            preset.phase = props.phase
            preset.frequency = props.frequency
            preset.step_size = props.step_size
            
            # 计算帧范围
            region = None
            for r in context.area.regions:
                if r.type == 'WINDOW':
                    region = r
                    break
            
            if not region:
                self.report({'WARNING'}, "No window region found")
                return {'CANCELLED'}
            
            view2d = region.view2d
            vis_x_min, vis_y_min = view2d.region_to_view(0, 0)
            vis_x_max, vis_y_max = view2d.region_to_view(region.width, region.height)
            
            # 计算网格步长
            view_width = vis_x_max - vis_x_min
            if view_width < 5.0:
                x_step = 0.5
            elif view_width < 25.0:
                x_step = 1.0
            elif view_width < 100.0:
                x_step = 2.0
            elif view_width < 500.0:
                x_step = 5.0
            else:
                x_step = 10.0
            
            # 计算选中的帧范围
            min_x = min(cell[0] for cell in selected_cells)
            max_x = max(cell[0] for cell in selected_cells)
            min_y = min(cell[1] for cell in selected_cells)
            max_y = max(cell[1] for cell in selected_cells)
            
            start_frame = vis_x_min + min_x * x_step
            end_frame = vis_x_min + (max_x + 1) * x_step
            cell_range = (start_frame, end_frame)
            
            # 计算值范围
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
            
            start_value = vis_y_min + min_y * y_step
            end_value = vis_y_min + (max_y + 1) * y_step
            value_range = (start_value, end_value)
            

            
            # 应用到所有选中的 fcurve
            fcurves = [fcu for fcu in obj.animation_data.action.fcurves if fcu.select]
            if not fcurves:
                fcurves = obj.animation_data.action.fcurves
            
            for fcu in fcurves:
                ModifierPresetGenerator.remove_overlapping_modifiers(fcu, start_frame, end_frame)
                mod = ModifierPresetGenerator.apply_preset(fcu, preset, cell_range, value_range, context)
                ModifierPresetGenerator.remove_zero_range_modifiers(fcu)
            
            # 清除选择
            cache['selected_cells'] = []
            cache['hover_cell'] = None
            is_grid_mode = False
            active_preset = None
            context.area.tag_redraw()
            
            self.report({'INFO'}, f"Applied {preset_type} modifier to frames {start_frame:.0f}-{end_frame:.0f}")
            return {'FINISHED'}
        except Exception as e:

            self.report({'ERROR'}, f"Error applying modifier: {e}")
            return {'CANCELLED'}


class GRAPH_OT_emo_jump_to_frame(Operator):
    bl_idname = "graph.emo_jump_to_frame"
    bl_label = "Jump to Frame"
    bl_description = "Jump to specified frame"
    bl_options = {'REGISTER'}
    
    frame: bpy.props.FloatProperty(
        name="Frame",
        default=1.0,
        description="Frame to jump to"
    )
    
    def execute(self, context):
        context.scene.frame_current = self.frame
        return {'FINISHED'}


class GRAPH_OT_emo_jump_to_endpoint(Operator):
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


class GRAPH_PT_emo_grid_editor(bpy.types.Panel):
    bl_label = _("E_Motion Grid Editor")
    bl_idname = "GRAPH_PT_emo_grid_editor"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = "E_Motion"
    
    @classmethod
    def poll(cls, context):
        # 在编辑模式下不显示
        edit_mode = getattr(context.window_manager, "emo_edit_mode", False)
        if edit_mode:
            return False
        
        space = context.space_data
        if space and space.type == 'GRAPH_EDITOR':
            if hasattr(space, 'mode') and space.mode == 'FCURVES':
                # 只在选中一条曲线时显示面板
                obj = context.active_object
                if obj and obj.animation_data and obj.animation_data.action:
                    selected_fcurves = [fcu for fcu in obj.animation_data.action.fcurves if fcu.select]
                    return len(selected_fcurves) == 1
        return False
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        cache = get_grid_cache()
        selected_count = len(cache.get('selected_cells', []))
        current_preset = cache.get('current_preset', 'SINE_FULL')
        
        row = layout.row(align=True)
        row.prop(scene.emo_grid_props, "show_grid", text="")
        
        layout.separator()
        
        layout.label(text=_('Current Preset'), icon='CURVE_DATA')
        preset_info = PRESET_ICONS.get(current_preset, {'icon': 'MODIFIER', 'label': 'Unknown'})
        
        # 尝试使用自定义图标
        if current_preset == 'CONSTANT' and 'LINEAR' in custom_icons and 'CONSTANT' in custom_icons['LINEAR']:
            layout.label(text=preset_info['label'], icon_value=custom_icons['LINEAR']['CONSTANT'].icon_id)
        elif current_preset == 'LINEAR_POS' and 'LINEAR' in custom_icons and 'LINEAR_POS' in custom_icons['LINEAR']:
            layout.label(text=preset_info['label'], icon_value=custom_icons['LINEAR']['LINEAR_POS'].icon_id)
        elif current_preset == 'LINEAR_NEG' and 'LINEAR' in custom_icons and 'LINEAR_NEG' in custom_icons['LINEAR']:
            layout.label(text=preset_info['label'], icon_value=custom_icons['LINEAR']['LINEAR_NEG'].icon_id)
        elif current_preset == 'SINE_FULL' and 'SINE' in custom_icons and 'SINE_FULL' in custom_icons['SINE']:
            layout.label(text=preset_info['label'], icon_value=custom_icons['SINE']['SINE_FULL'].icon_id)
        elif current_preset == 'SINE_BOTTOM' and 'SINE' in custom_icons and 'SINE_BOTTOM' in custom_icons['SINE']:
            layout.label(text=preset_info['label'], icon_value=custom_icons['SINE']['SINE_BOTTOM'].icon_id)
        elif current_preset == 'SINE_TOP' and 'SINE' in custom_icons and 'SINE_TOP' in custom_icons['SINE']:
            layout.label(text=preset_info['label'], icon_value=custom_icons['SINE']['SINE_TOP'].icon_id)
        elif current_preset == 'SINE_HALF_PERIOD' and 'SINE' in custom_icons and 'SINE_HALF_PERIOD' in custom_icons['SINE']:
            layout.label(text=preset_info['label'], icon_value=custom_icons['SINE']['SINE_HALF_PERIOD'].icon_id)
        elif current_preset == 'SQUARE_ROOT' and 'NONLINEAR' in custom_icons and 'SQUARE_ROOT' in custom_icons['NONLINEAR']:
            layout.label(text=preset_info['label'], icon_value=custom_icons['NONLINEAR']['SQUARE_ROOT'].icon_id)
        elif current_preset == 'NATURAL_LOG' and 'NONLINEAR' in custom_icons and 'NATURAL_LOG' in custom_icons['NONLINEAR']:
            layout.label(text=preset_info['label'], icon_value=custom_icons['NONLINEAR']['NATURAL_LOG'].icon_id)
        elif current_preset == 'CUSTOM_BEZIER' and 'BEZIER' in custom_icons and 'CUSTOM_BEZIER' in custom_icons['BEZIER']:
            layout.label(text=preset_info['label'], icon_value=custom_icons['BEZIER']['CUSTOM_BEZIER'].icon_id)
        elif current_preset == 'STEPPED_LINEAR' and 'OVERLAY' in custom_icons and 'STEPPED_LINEAR' in custom_icons['OVERLAY']:
            layout.label(text=preset_info['label'], icon_value=custom_icons['OVERLAY']['STEPPED_LINEAR'].icon_id)
        elif current_preset == 'SINE_STEPPED' and 'OVERLAY' in custom_icons and 'SINE_STEPPED' in custom_icons['OVERLAY']:
            layout.label(text=preset_info['label'], icon_value=custom_icons['OVERLAY']['SINE_STEPPED'].icon_id)
        elif current_preset == 'NOISE' and 'OVERLAY' in custom_icons and 'NOISE' in custom_icons['OVERLAY']:
            layout.label(text=preset_info['label'], icon_value=custom_icons['OVERLAY']['NOISE'].icon_id)
        else:
            layout.label(text=preset_info['label'], icon=preset_info['icon'])
        
        layout.separator()
        
        # 添加复选框
        if is_grid_mode:
            row = layout.row(align=True)
            row.prop(context.scene.emo_grid_props, "use_additive", text=_('Additive Mode'), toggle=True)
            layout.separator()
        
        # 主要类别按钮（长按显示pie菜单）
        # 使用网格布局，使按钮更大、更分散
        grid = layout.grid_flow(row_major=True, columns=5, even_columns=True, even_rows=True, align=True)
        
        # 线型
        if 'LINEAR' in custom_icons and 'LINEAR' in custom_icons['LINEAR']:
            op = grid.operator("graph.emo_open_pie", text="", icon_value=custom_icons['LINEAR']['LINEAR'].icon_id)
        else:
            op = grid.operator("graph.emo_open_pie", text="", icon='TRIA_UP')
        op.menu_id = "GRAPH_MT_emo_pie_linear"
        
        # 正弦
        if 'SINE' in custom_icons and 'SINE' in custom_icons['SINE']:
            op = grid.operator("graph.emo_open_pie", text="", icon_value=custom_icons['SINE']['SINE'].icon_id)
        else:
            op = grid.operator("graph.emo_open_pie", text="", icon='CURVE_DATA')
        op.menu_id = "GRAPH_MT_emo_pie_sine"
        
        # 非线性
        if 'NONLINEAR' in custom_icons and 'NONLINEAR' in custom_icons['NONLINEAR']:
            op = grid.operator("graph.emo_open_pie", text="", icon_value=custom_icons['NONLINEAR']['NONLINEAR'].icon_id)
        else:
            op = grid.operator("graph.emo_open_pie", text="", icon='CURVE_PATH')
        op.menu_id = "GRAPH_MT_emo_pie_nonlinear"
        
        # 贝塞尔
        if 'BEZIER' in custom_icons and 'BEZIER' in custom_icons['BEZIER']:
            op = grid.operator("graph.emo_open_pie", text="", icon_value=custom_icons['BEZIER']['BEZIER'].icon_id)
        else:
            op = grid.operator("graph.emo_open_pie", text="", icon='CURVE_BEZCURVE')
        op.menu_id = "GRAPH_MT_emo_pie_bezier"
        
        # 叠加
        if 'OVERLAY' in custom_icons and 'OVERLAY' in custom_icons['OVERLAY']:
            op = grid.operator("graph.emo_open_pie", text="", icon_value=custom_icons['OVERLAY']['OVERLAY'].icon_id)
        else:
            op = grid.operator("graph.emo_open_pie", text="", icon='MODIFIER')
        op.menu_id = "GRAPH_MT_emo_pie_overlay"
        



classes = (
    GRAPH_OT_emo_toggle_preset,
    GRAPH_OT_emo_apply_modifier,
    GRAPH_OT_emo_open_pie,
    GRAPH_MT_emo_pie_linear,
    GRAPH_MT_emo_pie_sine,
    GRAPH_MT_emo_pie_nonlinear,
    GRAPH_MT_emo_pie_bezier,
    GRAPH_MT_emo_pie_overlay,
    GRAPH_PT_emo_grid_editor,
)


def register():
    register_icons()
    for cls in classes:
        bpy.utils.register_class(cls)
    print("[E_Motion] Grid editor panels registered")


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    unregister_icons()
    print("[E_Motion] Grid editor panels unregistered")
