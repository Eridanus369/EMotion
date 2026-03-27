import bpy
import math


class ModifierPresetGenerator:
    
    @staticmethod
    def calculate_range_coefficients(cell_range, value_range=(0.0, 1.0)):
        start_cell, end_cell = cell_range
        start_val, end_val = value_range
        
        cell_span = end_cell - start_cell if end_cell != start_cell else 1
        val_span = end_val - start_val
        
        slope = val_span / cell_span if cell_span != 0 else 0
        intercept = start_val - slope * start_cell
        
        return slope, intercept
    
    @staticmethod
    def _set_modifier_range(mod, start_frame, end_frame):
        # 检查修改器类型并设置相应的属性
        
        # 优先检查 use_range 属性，因为 FNGENERATOR 也可能有这个属性
        if hasattr(mod, 'use_range'):
            mod.use_range = True
            mod.frame_start = start_frame
            mod.frame_end = end_frame
        elif hasattr(mod, 'use_from') and hasattr(mod, 'use_to'):
            mod.use_from = True
            mod.use_to = True
            setattr(mod, 'from', start_frame)
            setattr(mod, 'to', end_frame)
        elif hasattr(mod, 'frame_start') and hasattr(mod, 'frame_end'):
            # 对于 FNGENERATOR 等类型的修改器，直接设置 frame_start 和 frame_end
            mod.frame_start = start_frame
            mod.frame_end = end_frame
        
        # 打开限定帧范围按钮
        if hasattr(mod, 'use_restricted_range'):
            mod.use_restricted_range = True
        
        # 检查其他可能的范围限制属性
        if hasattr(mod, 'use_restrict_range'):
            mod.use_restrict_range = True
    
    @staticmethod
    def generate_constant(fcurve, cell_range, preset, value_range=None, context=None):
        # 如果提供了值范围，使用值范围的上限作为常量值
        if value_range:
            start_val, end_val = value_range
            constant_value = end_val
        else:
            slope, intercept = ModifierPresetGenerator.calculate_range_coefficients(cell_range)
            constant_value = intercept
        
        mod = fcurve.modifiers.new(type='GENERATOR')
        # 使用use_additive开关
        use_additive = True
        if context and hasattr(context.scene, 'emo_grid_props'):
            use_additive = context.scene.emo_grid_props.use_additive
        if hasattr(mod, 'use_additive'):
            mod.use_additive = use_additive
        mod.mode = 'POLYNOMIAL'
        mod.poly_order = 1
        
        mod.coefficients = [constant_value, 0.0]
        
        start_frame, end_frame = cell_range
        ModifierPresetGenerator._set_modifier_range(mod, start_frame, end_frame)
        
        mod.name = f"{start_frame:.0f}-{end_frame:.0f}"
        
        return mod
    
    @staticmethod
    def generate_linear_positive(fcurve, cell_range, preset, value_range=None, context=None):
        # 单增函数：选中区域左下，右上两个地方在函数上
        if value_range:
            start_frame, end_frame = cell_range
            start_val, end_val = value_range
            
            # 计算斜率和截距
            slope = (end_val - start_val) / (end_frame - start_frame) if (end_frame - start_frame) != 0 else 0
            intercept = start_val - slope * start_frame
        else:
            slope, intercept = ModifierPresetGenerator.calculate_range_coefficients(
                cell_range, (0.0, 1.0)
            )
        
        mod = fcurve.modifiers.new(type='GENERATOR')
        # 使用use_additive开关
        use_additive = True
        if context and hasattr(context.scene, 'emo_grid_props'):
            use_additive = context.scene.emo_grid_props.use_additive
        if hasattr(mod, 'use_additive'):
            mod.use_additive = use_additive
        mod.mode = 'POLYNOMIAL'
        mod.poly_order = 1
        
        mod.coefficients = [intercept, slope]
        
        start_frame, end_frame = cell_range
        ModifierPresetGenerator._set_modifier_range(mod, start_frame, end_frame)
        
        mod.name = f"{start_frame:.0f}-{end_frame:.0f}"
        
        return mod
    
    @staticmethod
    def generate_linear_negative(fcurve, cell_range, preset, value_range=None, context=None):
        # 单减函数：选中区域左上，右下两个地方在函数上
        if value_range:
            start_frame, end_frame = cell_range
            start_val, end_val = value_range
            
            # 对于单减函数，我们需要从左上角开始（较大的值），到右下角结束（较小的值）
            # 确保起点值大于终点值，实现单减效果
            if start_val < end_val:
                start_val, end_val = end_val, start_val
            
            # 计算斜率和截距
            slope = (end_val - start_val) / (end_frame - start_frame) if (end_frame - start_frame) != 0 else 0
            # 确保斜率为负
            if slope > 0:
                slope = -abs(slope)
            
            # 计算截距
            intercept = start_val - slope * start_frame
        else:
            slope, intercept = ModifierPresetGenerator.calculate_range_coefficients(
                cell_range, (1.0, 0.0)
            )
        
        mod = fcurve.modifiers.new(type='GENERATOR')
        # 使用use_additive开关
        use_additive = True
        if context and hasattr(context.scene, 'emo_grid_props'):
            use_additive = context.scene.emo_grid_props.use_additive
        if hasattr(mod, 'use_additive'):
            mod.use_additive = use_additive
        mod.mode = 'POLYNOMIAL'
        mod.poly_order = 1
        
        mod.coefficients = [intercept, slope]
        
        start_frame, end_frame = cell_range
        ModifierPresetGenerator._set_modifier_range(mod, start_frame, end_frame)
        
        mod.name = f"{start_frame:.0f}-{end_frame:.0f}"
        
        return mod
    
    @staticmethod
    def generate_full_sine(fcurve, cell_range, preset, value_range=None, context=None):
        if value_range:
            start_frame, end_frame = cell_range
            start_val, end_val = value_range
            
            # 计算幅值：(y-x)/2
            amplitude = (end_val - start_val) / 2
            # 计算偏移量：(x+y)/2
            offset = (start_val + end_val) / 2
            # 计算周期：确保一个周期
            period = end_frame - start_frame
            if period <= 0:
                period = 1
        else:
            amplitude = preset.amplitude
            phase = preset.phase
            offset = 0.0
            period = 10.0  # 默认周期
        
        start_frame, end_frame = cell_range
        
        # 使用 FNGENERATOR 类型的修改器来创建正弦波
        mod = fcurve.modifiers.new(type='FNGENERATOR')
        # 使用use_additive开关
        use_additive = True
        if context and hasattr(context.scene, 'emo_grid_props'):
            use_additive = context.scene.emo_grid_props.use_additive
        # 检查并设置正确的属性名
        if hasattr(mod, 'function_type'):
            mod.function_type = 'SIN'
        elif hasattr(mod, 'function'):
            mod.function = 'SINE'
        mod.amplitude = amplitude
        # 计算相位偏移，确保正弦波在正确的位置开始
        # 相位偏移是从帧0开始计算的，所以我们需要调整相位偏移值
        # 正弦波公式：y = A * sin(2π * (x - a) / (b - a)) + offset
        # 其中，A 是幅值，a 是起始帧，b 是结束帧
        # 相位偏移应该是：-2π * a / (b - a)，这样当 x = a 时，相位为 0，当 x = b 时，相位为 2π
        phase_offset = 0.0
        if period > 0:
            phase_offset = -2 * math.pi * start_frame / period
        mod.phase_offset = phase_offset
        # 设置相位倍移，确保一个周期
        if hasattr(mod, 'phase_multiplier'):
            # 对于某些 Blender 版本，使用 phase_multiplier 来控制频率
            # 计算 phase_multiplier 确保一个周期
            if period > 0:
                mod.phase_multiplier = 2 * math.pi / period
        # 对于不支持 phase_multiplier 的版本，使用其他方法
        elif hasattr(mod, 'frequency'):
            # 计算频率，确保一个周期
            if period > 0:
                mod.frequency = 1.0 / period
        # 设置值偏移，确保正弦波在正确的值范围内
        if hasattr(mod, 'value_offset'):
            mod.value_offset = offset
        # 无论是否有 value_offset 属性，都设置 use_additive
        if hasattr(mod, 'use_additive'):
            mod.use_additive = use_additive
        # 如果没有 value_offset 属性，创建一个偏移修改器
        if not hasattr(mod, 'value_offset'):
            offset_mod = fcurve.modifiers.new(type='GENERATOR')
            offset_mod.mode = 'POLYNOMIAL'
            offset_mod.poly_order = 1
            # 偏移修改器直接设置基础值，不使用 additive
            if hasattr(offset_mod, 'use_additive'):
                offset_mod.use_additive = False
            offset_mod.coefficients = [offset, 0.0]
            ModifierPresetGenerator._set_modifier_range(offset_mod, start_frame, end_frame)
            offset_mod.name = f"{start_frame:.0f}-{end_frame:.0f}_OFFSET"
        
        ModifierPresetGenerator._set_modifier_range(mod, start_frame, end_frame)
        mod.name = f"{start_frame:.0f}-{end_frame:.0f}_SINE"
        
        return mod
    
    @staticmethod
    def generate_half_sine_bottom(fcurve, cell_range, preset, value_range=None, context=None):
        if value_range:
            start_frame, end_frame = cell_range
            x, y = value_range
            
            # 计算幅值：(y-x)
            amplitude = y - x
            # 计算偏移量：y
            offset = y
            # 计算周期
            period = end_frame - start_frame
            if period <= 0:
                period = 1
        else:
            amplitude = preset.amplitude
            offset = 0.0
            period = 10.0
        
        start_frame, end_frame = cell_range
        
        # 使用 FNGENERATOR 类型的修改器来创建正弦波
        mod = fcurve.modifiers.new(type='FNGENERATOR')
        # 使用use_additive开关
        use_additive = True
        if context and hasattr(context.scene, 'emo_grid_props'):
            use_additive = context.scene.emo_grid_props.use_additive
        # 检查并设置正确的属性名
        if hasattr(mod, 'function_type'):
            mod.function_type = 'SIN'
        elif hasattr(mod, 'function'):
            mod.function = 'SINE'
        # 计算相位偏移，使正弦波从底部开始
        # 帧为a,b时值为y，帧为（a+b）/2时值为x
        # 正弦波公式：y = A * sin(ω(t - a)) + y
        # 其中ω = π / period（半个周期）
        # 当t = a时，sin(0) = 0 → y = y
        # 当t = (a + b)/2时，sin(π/2) = 1 → y = A + y = x
        # 当t = b时，sin(π) = 0 → y = y
        # 所以A = x - y
        amplitude = x - y  # 负值，使正弦波向下
        mod.amplitude = amplitude
        
        # 计算相位偏移
        phase_offset = 0.0
        if period > 0:
            phase_offset = -math.pi * start_frame / period
        mod.phase_offset = phase_offset
        
        # 设置相位倍移，确保半个周期
        if hasattr(mod, 'phase_multiplier'):
            if period > 0:
                mod.phase_multiplier = math.pi / period
        elif hasattr(mod, 'frequency'):
            if period > 0:
                mod.frequency = 0.5 / period
        
        # 设置值偏移
        if hasattr(mod, 'value_offset'):
            mod.value_offset = y  # 从y开始
            # 使用use_additive开关
            if hasattr(mod, 'use_additive'):
                mod.use_additive = use_additive
            else:
                mod.use_additive = use_additive
        
        ModifierPresetGenerator._set_modifier_range(mod, start_frame, end_frame)
        mod.name = f"{start_frame:.0f}-{end_frame:.0f}_SINE_BOTTOM"
        
        return mod
    
    @staticmethod
    def generate_half_sine_top(fcurve, cell_range, preset, value_range=None, context=None):
        if value_range:
            start_frame, end_frame = cell_range
            x, y = value_range
            
            # 计算幅值：(y-x)
            amplitude = y - x
            # 计算偏移量：x
            offset = x
            # 计算周期
            period = end_frame - start_frame
            if period <= 0:
                period = 1
        else:
            amplitude = preset.amplitude
            offset = 0.0
            period = 10.0
        
        start_frame, end_frame = cell_range
        
        # 使用 FNGENERATOR 类型的修改器来创建正弦波
        mod = fcurve.modifiers.new(type='FNGENERATOR')
        # 使用use_additive开关
        use_additive = True
        if context and hasattr(context.scene, 'emo_grid_props'):
            use_additive = context.scene.emo_grid_props.use_additive
        # 检查并设置正确的属性名
        if hasattr(mod, 'function_type'):
            mod.function_type = 'SIN'
        elif hasattr(mod, 'function'):
            mod.function = 'SINE'
        mod.amplitude = amplitude
        
        # 计算相位偏移，使正弦波从顶部开始
        # 帧为a,b时值为x，帧为（b-a）/2时值为y
        # 正弦波公式：y = A * sin(ω(t - a)) + x
        # 其中ω = π / period（半个周期）
        # 当t = a时，sin(0) = 0 → y = x
        # 当t = (a + b)/2时，sin(π/2) = 1 → y = x + A = y
        # 当t = b时，sin(π) = 0 → y = x
        phase_offset = 0.0
        if period > 0:
            phase_offset = -math.pi * start_frame / period
        mod.phase_offset = phase_offset
        
        # 设置相位倍移，确保半个周期
        if hasattr(mod, 'phase_multiplier'):
            if period > 0:
                mod.phase_multiplier = math.pi / period
        elif hasattr(mod, 'frequency'):
            if period > 0:
                mod.frequency = 0.5 / period
        
        # 设置值偏移
        if hasattr(mod, 'value_offset'):
            mod.value_offset = offset
            # 使用use_additive开关
            if hasattr(mod, 'use_additive'):
                mod.use_additive = use_additive
            else:
                mod.use_additive = use_additive
        
        ModifierPresetGenerator._set_modifier_range(mod, start_frame, end_frame)
        mod.name = f"{start_frame:.0f}-{end_frame:.0f}_SINE_TOP"
        
        return mod
    
    @staticmethod
    def generate_half_sine_increasing(fcurve, cell_range, preset, value_range=None, context=None):
        if value_range:
            start_frame, end_frame = cell_range
            x, y = value_range
            
            # 计算幅值：绝对值(y-x)
            amplitude = abs(y - x)
            # 计算偏移量：x
            offset = x
            # 计算周期
            period = end_frame - start_frame
            if period <= 0:
                period = 1
        else:
            amplitude = preset.amplitude
            offset = 0.0
            period = 10.0
        
        start_frame, end_frame = cell_range
        
        # 使用 FNGENERATOR 类型的修改器来创建正弦波
        mod = fcurve.modifiers.new(type='FNGENERATOR')
        # 使用use_additive开关
        use_additive = True
        if context and hasattr(context.scene, 'emo_grid_props'):
            use_additive = context.scene.emo_grid_props.use_additive
        # 检查并设置正确的属性名
        if hasattr(mod, 'function_type'):
            mod.function_type = 'SIN'
        elif hasattr(mod, 'function'):
            mod.function = 'SINE'
        mod.amplitude = amplitude
        
        # 计算相位偏移，使正弦波从顶部开始
        # 帧为a,b时值为x，帧为（b-a）/2时值为y
        # 正弦波公式：y = A * sin(ω(t - a)) + x
        # 其中ω = π / period（半个周期）
        # 当t = a时，sin(0) = 0 → y = x
        # 当t = (a + b)/2时，sin(π/2) = 1 → y = x + A = y
        # 当t = b时，sin(π) = 0 → y = x
        phase_offset = 0.0
        if period > 0:
            phase_offset = -math.pi * start_frame / period
        mod.phase_offset = phase_offset
        
        # 设置相位倍移，确保半个周期
        if hasattr(mod, 'phase_multiplier'):
            if period > 0:
                mod.phase_multiplier = math.pi / period
        elif hasattr(mod, 'frequency'):
            if period > 0:
                mod.frequency = 0.5 / period
        
        # 设置值偏移
        if hasattr(mod, 'value_offset'):
            mod.value_offset = offset
            # 使用use_additive开关
            if hasattr(mod, 'use_additive'):
                mod.use_additive = use_additive
            else:
                mod.use_additive = use_additive
        
        ModifierPresetGenerator._set_modifier_range(mod, start_frame, end_frame)
        mod.name = f"{start_frame:.0f}-{end_frame:.0f}_SINE_INCREASING"
        
        return mod
    
    @staticmethod
    def generate_half_sine_decreasing(fcurve, cell_range, preset, value_range=None, context=None):
        if value_range:
            start_frame, end_frame = cell_range
            x, y = value_range
            
            # 计算幅值：绝对值(y-x)
            amplitude = abs(y - x)
            # 计算偏移量：y
            offset = y
            # 计算周期
            period = end_frame - start_frame
            if period <= 0:
                period = 1
        else:
            amplitude = preset.amplitude
            offset = 0.0
            period = 10.0
        
        start_frame, end_frame = cell_range
        
        # 使用 FNGENERATOR 类型的修改器来创建正弦波
        mod = fcurve.modifiers.new(type='FNGENERATOR')
        # 使用use_additive开关
        use_additive = True
        if context and hasattr(context.scene, 'emo_grid_props'):
            use_additive = context.scene.emo_grid_props.use_additive
        # 检查并设置正确的属性名
        if hasattr(mod, 'function_type'):
            mod.function_type = 'SIN'
        elif hasattr(mod, 'function'):
            mod.function = 'SINE'
        mod.amplitude = -amplitude  # 使用负值实现递减
        
        # 计算相位偏移，使正弦波从顶部开始
        # 帧为a,b时值为y，帧为（b-a）/2时值为x
        # 正弦波公式：y = y - A * sin(ω(t - a))
        # 其中ω = π / period（半个周期）
        # 当t = a时，sin(0) = 0 → y = y
        # 当t = (a + b)/2时，sin(π/2) = 1 → y = y - A = x
        # 当t = b时，sin(π) = 0 → y = y
        phase_offset = 0.0
        if period > 0:
            phase_offset = -math.pi * start_frame / period
        mod.phase_offset = phase_offset
        
        # 设置相位倍移，确保半个周期
        if hasattr(mod, 'phase_multiplier'):
            if period > 0:
                mod.phase_multiplier = math.pi / period
        elif hasattr(mod, 'frequency'):
            if period > 0:
                mod.frequency = 0.5 / period
        
        # 设置值偏移
        if hasattr(mod, 'value_offset'):
            mod.value_offset = offset
            # 使用use_additive开关
            if hasattr(mod, 'use_additive'):
                mod.use_additive = use_additive
            else:
                mod.use_additive = use_additive
        
        ModifierPresetGenerator._set_modifier_range(mod, start_frame, end_frame)
        mod.name = f"{start_frame:.0f}-{end_frame:.0f}_SINE_DECREASING"
        
        return mod
    
    @staticmethod
    def generate_half_sine_period(fcurve, cell_range, preset, value_range=None, context=None):
        if value_range:
            start_frame, end_frame = cell_range
            x, y = value_range
            
            # 计算幅值：(y-x)/2
            amplitude = (y - x) / 2
            # 计算偏移量：(x+y)/2
            offset = (x + y) / 2
            # 计算周期
            period = end_frame - start_frame
            if period <= 0:
                period = 1
        else:
            amplitude = preset.amplitude
            offset = 0.0
            period = 10.0
        
        start_frame, end_frame = cell_range
        
        # 使用 FNGENERATOR 类型的修改器来创建正弦波
        mod = fcurve.modifiers.new(type='FNGENERATOR')
        # 使用use_additive开关
        use_additive = True
        if context and hasattr(context.scene, 'emo_grid_props'):
            use_additive = context.scene.emo_grid_props.use_additive
        # 检查并设置正确的属性名
        if hasattr(mod, 'function_type'):
            mod.function_type = 'SIN'
        elif hasattr(mod, 'function'):
            mod.function = 'SINE'
        mod.amplitude = amplitude
        
        # 计算相位偏移，确保半个周期
        phase_offset = 0.0
        if period > 0:
            phase_offset = -math.pi * start_frame / period
        mod.phase_offset = phase_offset
        
        # 设置相位倍移，确保半个周期
        if hasattr(mod, 'phase_multiplier'):
            if period > 0:
                mod.phase_multiplier = math.pi / period
        elif hasattr(mod, 'frequency'):
            if period > 0:
                mod.frequency = 0.5 / period
        
        # 设置值偏移
        if hasattr(mod, 'value_offset'):
            mod.value_offset = offset
            # 使用use_additive开关
            if hasattr(mod, 'use_additive'):
                mod.use_additive = use_additive
            else:
                mod.use_additive = use_additive
        
        ModifierPresetGenerator._set_modifier_range(mod, start_frame, end_frame)
        mod.name = f"{start_frame:.0f}-{end_frame:.0f}_SINE_HALF"
        
        return mod
    
    @staticmethod
    def generate_square_root(fcurve, cell_range, preset, value_range=None, context=None):
        start_frame, end_frame = cell_range
        
        # 使用 FNGENERATOR 类型的修改器来创建平方根函数
        mod = fcurve.modifiers.new(type='FNGENERATOR')
        # 使用use_additive开关
        use_additive = True
        if context and hasattr(context.scene, 'emo_grid_props'):
            use_additive = context.scene.emo_grid_props.use_additive
        # 检查并设置正确的属性名
        if hasattr(mod, 'function_type'):
            mod.function_type = 'SQRT'
        elif hasattr(mod, 'function'):
            mod.function = 'SQRT'
        # 检查并设置use_additive属性
        if hasattr(mod, 'use_additive'):
            mod.use_additive = use_additive
        else:
            mod.use_additive = use_additive
        
        if value_range:
            start_val, end_val = value_range
            
            # 计算系数，使平方根函数经过左下角和右上角
            # 平方根函数：y = a * sqrt(x - b) + c
            # 左下角：(start_frame, start_val)
            # 右上角：(end_frame, end_val)
            b = start_frame
            c = start_val
            
            # 计算 a
            amplitude = 1.0
            if end_frame > start_frame:
                amplitude = (end_val - start_val) / math.sqrt(end_frame - start_frame)
            
            mod.amplitude = amplitude
            
            # 设置相位偏移（对应于b）
            phase_offset = -b
            mod.phase_offset = phase_offset
            
            # 设置值偏移（对应于c）
            if hasattr(mod, 'value_offset'):
                mod.value_offset = c
        else:
            amplitude = preset.amplitude
            phase = preset.phase
            mod.amplitude = amplitude
            mod.phase_offset = phase
        
        ModifierPresetGenerator._set_modifier_range(mod, start_frame, end_frame)
        mod.name = f"{start_frame:.0f}-{end_frame:.0f}_SQRT"
        
        return mod
    
    @staticmethod
    def generate_natural_log(fcurve, cell_range, preset, value_range=None, context=None):
        start_frame, end_frame = cell_range
        
        # 使用 FNGENERATOR 类型的修改器来创建自然对数函数
        mod = fcurve.modifiers.new(type='FNGENERATOR')
        # 使用use_additive开关
        use_additive = True
        if context and hasattr(context.scene, 'emo_grid_props'):
            use_additive = context.scene.emo_grid_props.use_additive
        # 检查并设置正确的属性名
        if hasattr(mod, 'function_type'):
            mod.function_type = 'LN'
        elif hasattr(mod, 'function'):
            mod.function = 'LN'
        # 检查并设置use_additive属性
        if hasattr(mod, 'use_additive'):
            mod.use_additive = use_additive
        else:
            mod.use_additive = use_additive
        
        if value_range:
            start_val, end_val = value_range
            
            # 计算系数，使自然对数函数经过左下角和右上角
            # 自然对数函数：y = a * ln(x - b) + c
            # 左下角：(start_frame, start_val)
            # 右上角：(end_frame, end_val)
            b = start_frame - 1  # 确保 x - b > 0
            c = start_val
            
            # 计算 a
            amplitude = 1.0
            if end_frame > start_frame:
                try:
                    amplitude = (end_val - start_val) / math.log(end_frame - b)
                except:
                    amplitude = 1.0
            
            mod.amplitude = amplitude
            
            # 设置相位偏移（对应于b）
            phase_offset = -b
            mod.phase_offset = phase_offset
            
            # 设置值偏移（对应于c）
            if hasattr(mod, 'value_offset'):
                mod.value_offset = c
        else:
            amplitude = preset.amplitude
            phase = preset.phase
            mod.amplitude = amplitude
            mod.phase_offset = phase
        
        start_frame, end_frame = cell_range
        ModifierPresetGenerator._set_modifier_range(mod, start_frame, end_frame)
        mod.name = f"{start_frame:.0f}-{end_frame:.0f}_LOG"
        
        return mod
    
    @staticmethod
    def generate_custom_bezier(fcurve, cell_range, preset, value_range=None, context=None):
        if value_range:
            start_frame, end_frame = cell_range
            start_val, end_val = value_range
            
            # 确保曲线有足够的关键帧
            start_kf = None
            end_kf = None
            
            # 查找或创建起始和结束关键帧
            for kf in fcurve.keyframe_points:
                if abs(kf.co[0] - start_frame) < 0.01:
                    start_kf = kf
                    start_kf.co[1] = start_val
                elif abs(kf.co[0] - end_frame) < 0.01:
                    end_kf = kf
                    end_kf.co[1] = end_val
            
            if not start_kf:
                start_kf = fcurve.keyframe_points.insert(start_frame, start_val)
            if not end_kf:
                end_kf = fcurve.keyframe_points.insert(end_frame, end_val)
            
            # 设置贝塞尔曲线插值
            start_kf.interpolation = 'BEZIER'
            end_kf.interpolation = 'BEZIER'
            
            # 设置自由手柄
            start_kf.handle_right_type = 'FREE'
            end_kf.handle_left_type = 'FREE'
            
            # 计算手柄位置（使用默认值）
            handle_distance = (end_frame - start_frame) * 0.333
            start_kf.handle_right = (start_frame + handle_distance, start_val)
            end_kf.handle_left = (end_frame - handle_distance, end_val)
            
            # 更新曲线
            fcurve.update()
            
            # 返回None，因为我们没有创建修改器
            return None
        else:
            # 如果没有值范围，创建一个默认的贝塞尔曲线修改器
            mod = fcurve.modifiers.new(type='GENERATOR')
            # 使用use_additive开关
            use_additive = True
            if context and hasattr(context.scene, 'emo_grid_props'):
                use_additive = context.scene.emo_grid_props.use_additive
            if hasattr(mod, 'use_additive'):
                mod.use_additive = use_additive
            else:
                mod.use_additive = use_additive
            mod.mode = 'POLYNOMIAL'
            mod.poly_order = 1
            
            start_frame, end_frame = cell_range
            ModifierPresetGenerator._set_modifier_range(mod, start_frame, end_frame)
            mod.name = f"{start_frame:.0f}-{end_frame:.0f}_BEZIER"
            
            return mod
    
    @staticmethod
    def generate_stepped_linear(fcurve, cell_range, preset, value_range=None, context=None):
        start_frame, end_frame = cell_range
        
        step_mod = fcurve.modifiers.new(type='STEPPED')
        # 根据值范围调整步长尺寸，与值范围成反比
        if value_range:
            start_val, end_val = value_range
            value_range_size = abs(end_val - start_val)
            if value_range_size > 0:
                # 计算步长，与值范围成反比
                if hasattr(step_mod, 'frame_step'):
                    step_mod.frame_step = 10.0 / value_range_size
                elif hasattr(step_mod, 'step'):
                    step_mod.step = 10.0 / value_range_size
                elif hasattr(step_mod, 'step_size'):
                    step_mod.step_size = 10.0 / value_range_size
            else:
                if hasattr(step_mod, 'frame_step'):
                    step_mod.frame_step = getattr(preset, 'step_size', 1.0)
                elif hasattr(step_mod, 'step'):
                    step_mod.step = getattr(preset, 'step_size', 1.0)
                elif hasattr(step_mod, 'step_size'):
                    step_mod.step_size = preset.step_size
        else:
            if hasattr(step_mod, 'frame_step'):
                step_mod.frame_step = getattr(preset, 'step_size', 1.0)
            elif hasattr(step_mod, 'step'):
                step_mod.step = getattr(preset, 'step_size', 1.0)
            elif hasattr(step_mod, 'step_size'):
                step_mod.step_size = preset.step_size
        # 设置偏移
        if hasattr(step_mod, 'offset'):
            step_mod.offset = 0.0
        elif hasattr(step_mod, 'step_offset'):
            step_mod.step_offset = 0.0
        # 打开限制帧范围开关
        if hasattr(step_mod, 'use_restricted_range'):
            step_mod.use_restricted_range = True
        elif hasattr(step_mod, 'use_range'):
            step_mod.use_range = True
        # 确保设置正确的帧范围
        if hasattr(step_mod, 'frame_start'):
            step_mod.frame_start = start_frame
        if hasattr(step_mod, 'frame_end'):
            step_mod.frame_end = end_frame
        step_mod.name = f"{start_frame:.0f}-{end_frame:.0f}_STEP"
        
        return step_mod
    

    
    @staticmethod
    def generate_noise(fcurve, cell_range, preset, value_range=None, context=None):
        if value_range:
            start_frame, end_frame = cell_range
            start_val, end_val = value_range
            
            # 计算幅值：(y-x)/2
            amplitude = (end_val - start_val) / 2
            # 计算偏移量：(x+y)/2
            offset = (start_val + end_val) / 2
            # 计算缩放，与值范围成反比
            value_range_size = abs(end_val - start_val)
            if value_range_size > 0:
                scale = 1.0 / value_range_size
            else:
                scale = preset.frequency
        else:
            amplitude = preset.amplitude
            scale = preset.frequency
            offset = preset.phase
        
        start_frame, end_frame = cell_range
        
        mod = fcurve.modifiers.new(type='NOISE')
        # 使用use_additive开关
        use_additive = True
        if context and hasattr(context.scene, 'emo_grid_props'):
            use_additive = context.scene.emo_grid_props.use_additive
        # 检查并设置use_additive属性
        if hasattr(mod, 'use_additive'):
            mod.use_additive = use_additive
        # 设置振幅、缩放和偏移
        if hasattr(mod, 'amplitude'):
            mod.amplitude = amplitude
        if hasattr(mod, 'scale'):
            mod.scale = scale
        if hasattr(mod, 'offset'):
            mod.offset = offset
        # 打开限制帧范围开关
        if hasattr(mod, 'use_restricted_range'):
            mod.use_restricted_range = True
        elif hasattr(mod, 'use_range'):
            mod.use_range = True
        # 确保设置正确的帧范围
        if hasattr(mod, 'frame_start'):
            mod.frame_start = start_frame
        if hasattr(mod, 'frame_end'):
            mod.frame_end = end_frame
        
        mod.name = f"{start_frame:.0f}-{end_frame:.0f}_NOISE"
        
        return mod
    
    @staticmethod
    def apply_preset(fcurve, preset, cell_range, value_range=None, context=None):
        preset_type = preset.preset_type
        
        # 检查是否是叠加类修改器（步进和噪波）
        is_overlay_preset = preset_type in {'STEPPED_LINEAR', 'NOISE'}
        
        # 对于非叠加类修改器，执行覆盖检查
        if not is_overlay_preset:
            start_frame, end_frame = cell_range
            ModifierPresetGenerator.remove_overlapping_modifiers(fcurve, start_frame, end_frame)
        
        generators = {
            'CONSTANT': ModifierPresetGenerator.generate_constant,
            'LINEAR_POS': ModifierPresetGenerator.generate_linear_positive,
            'LINEAR_NEG': ModifierPresetGenerator.generate_linear_negative,
            'SINE_FULL': ModifierPresetGenerator.generate_full_sine,
            'SINE_BOTTOM': ModifierPresetGenerator.generate_half_sine_bottom,
            'SINE_TOP': ModifierPresetGenerator.generate_half_sine_top,
            'SINE_HALF_PERIOD': ModifierPresetGenerator.generate_half_sine_period,
            'SQUARE_ROOT': ModifierPresetGenerator.generate_square_root,
            'NATURAL_LOG': ModifierPresetGenerator.generate_natural_log,
            'CUSTOM_BEZIER': ModifierPresetGenerator.generate_custom_bezier,
            'STEPPED_LINEAR': ModifierPresetGenerator.generate_stepped_linear,
            'NOISE': ModifierPresetGenerator.generate_noise,
        }
        
        generator = generators.get(preset_type)
        if generator:
            return generator(fcurve, cell_range, preset, value_range, context)
        
        return None
    
    @staticmethod
    def remove_overlapping_modifiers(fcurve, start_frame, end_frame):
        to_remove = []
        
        # 检查当前要添加的修改器类型
        # 注意：这里我们无法直接知道要添加的修改器类型，所以我们需要检查所有现有修改器
        # 对于步进和噪波修改器，我们不执行覆盖逻辑
        
        for mod in fcurve.modifiers:
            # 检查是否是叠加类修改器（步进和噪波）
            is_overlay_modifier = mod.type in {'STEPPED', 'NOISE'}
            
            # 对于叠加类修改器，跳过覆盖检查
            if is_overlay_modifier:
                continue
            
            # 检查修改器类型并获取相应的属性
            mod_start = 0
            mod_end = 0
            use_range = False
            
            # 检查所有可能的范围属性
            if hasattr(mod, 'use_from') and hasattr(mod, 'use_to'):
                mod_start = getattr(mod, 'from', 0)
                mod_end = getattr(mod, 'to', 0)
                use_range = mod.use_from and mod.use_to
            elif hasattr(mod, 'use_range'):
                mod_start = getattr(mod, 'frame_start', 0)
                mod_end = getattr(mod, 'frame_end', 0)
                use_range = mod.use_range
            elif hasattr(mod, 'frame_start') and hasattr(mod, 'frame_end'):
                mod_start = mod.frame_start
                mod_end = mod.frame_end
                use_range = True
            
            # 如果没有范围限制，认为它覆盖整个时间轴
            if not use_range:
                mod_start = -float('inf')
                mod_end = float('inf')
            
            # 检查是否有重叠
            if mod_start < end_frame and mod_end > start_frame:
                # 情况1：新修改器完全覆盖现有修改器
                if start_frame <= mod_start and end_frame >= mod_end:
                    # 将现有修改器范围设为0并标记为删除
                    if hasattr(mod, 'use_from') and hasattr(mod, 'use_to'):
                        setattr(mod, 'from', 0)
                        setattr(mod, 'to', 0)
                    elif hasattr(mod, 'use_range'):
                        mod.frame_start = 0
                        mod.frame_end = 0
                    elif hasattr(mod, 'frame_start') and hasattr(mod, 'frame_end'):
                        mod.frame_start = 0
                        mod.frame_end = 0
                    to_remove.append(mod)
                # 情况2：新修改器在现有修改器的右侧
                elif start_frame <= mod_end and start_frame > mod_start:
                    # 将现有修改器的结束帧设为新修改器的开始帧 - 1
                    new_end = start_frame - 1
                    if hasattr(mod, 'use_from') and hasattr(mod, 'use_to'):
                        setattr(mod, 'to', new_end)
                        mod.use_to = True  # 确保启用范围限制
                    elif hasattr(mod, 'use_range'):
                        mod.frame_end = new_end
                        mod.use_range = True  # 确保启用范围限制
                    elif hasattr(mod, 'frame_start') and hasattr(mod, 'frame_end'):
                        mod.frame_end = new_end
                # 情况3：新修改器在现有修改器的左侧
                elif end_frame >= mod_start and end_frame < mod_end:
                    # 将现有修改器的开始帧设为新修改器的结束帧 + 1
                    new_start = end_frame + 1
                    if hasattr(mod, 'use_from') and hasattr(mod, 'use_to'):
                        setattr(mod, 'from', new_start)
                        mod.use_from = True  # 确保启用范围限制
                    elif hasattr(mod, 'use_range'):
                        mod.frame_start = new_start
                        mod.use_range = True  # 确保启用范围限制
                    elif hasattr(mod, 'frame_start') and hasattr(mod, 'frame_end'):
                        mod.frame_start = new_start
        
        # 移除范围为0的修改器
        for mod in to_remove:
            fcurve.modifiers.remove(mod)
    
    @staticmethod
    def remove_zero_range_modifiers(fcurve):
        to_remove = []
        
        for mod in fcurve.modifiers:
            # 检查修改器类型并获取相应的属性
            if hasattr(mod, 'use_from') and hasattr(mod, 'use_to'):
                if mod.use_from and mod.use_to:
                    mod_start = getattr(mod, 'from', 0)
                    mod_end = getattr(mod, 'to', 0)
                    
                    if mod_start == 0 and mod_end == 0:
                        to_remove.append(mod)
            elif hasattr(mod, 'use_range'):
                if mod.use_range:
                    mod_start = getattr(mod, 'frame_start', 0)
                    mod_end = getattr(mod, 'frame_end', 0)
                    
                    if mod_start == 0 and mod_end == 0:
                        to_remove.append(mod)
        
        for mod in to_remove:
            fcurve.modifiers.remove(mod)


def register():
    print("[E_Motion] Modifier preset generator registered")


def unregister():
    print("[E_Motion] Modifier preset generator unregistered")
