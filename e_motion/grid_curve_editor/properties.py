import bpy
from bpy.props import IntProperty, BoolProperty, FloatProperty, EnumProperty, StringProperty, CollectionProperty
import math


class EMO_GridCell(bpy.types.PropertyGroup):
    cell_x: IntProperty(default=0)
    cell_y: IntProperty(default=0)


class EMO_GridModifierProperties(bpy.types.PropertyGroup):
    grid_width: IntProperty(
        name="Grid Width",
        description="Number of columns in the grid",
        default=25,
        min=1,
        max=100
    )
    
    grid_height: IntProperty(
        name="Grid Height",
        description="Number of rows in the grid",
        default=10,
        min=1,
        max=50
    )
    
    frame_start: IntProperty(
        name="Frame Start",
        description="Start frame of the grid",
        default=1,
        min=0,
        max=100000
    )
    
    frame_end: IntProperty(
        name="Frame End",
        description="End frame of the grid",
        default=100,
        min=1,
        max=100000
    )
    
    value_min: FloatProperty(
        name="Value Min",
        description="Minimum value of the grid",
        default=-1.0,
        min=-10000.0,
        max=10000.0
    )
    
    value_max: FloatProperty(
        name="Value Max",
        description="Maximum value of the grid",
        default=1.0,
        min=-10000.0,
        max=10000.0
    )
    
    show_grid: BoolProperty(
        name="Show Grid",
        description="Show grid overlay",
        default=True
    )
    
    current_preset: EnumProperty(
        name="Current Preset",
        items=[
            ('CONSTANT', 'Constant', 'Constant value'),
            ('LINEAR_POS', 'Linear +', 'Positive linear function'),
            ('LINEAR_NEG', 'Linear -', 'Negative linear function'),
            ('SINE_FULL', 'Full Sine', 'Complete sine wave'),
            ('SINE_BOTTOM', 'Half Sine ↓', 'Bottom half of sine wave'),
            ('SINE_TOP', 'Half Sine ↑', 'Top half of sine wave'),
            ('SINE_HALF_PERIOD', 'Half Period', 'Half period sine wave'),
            ('SQUARE_ROOT', 'Sqrt', 'Square root function'),
            ('NATURAL_LOG', 'Ln', 'Natural logarithm'),
            ('CUSTOM_BEZIER', 'Bezier', 'User-defined bezier'),
            ('STEPPED_LINEAR', 'Stepped', 'Linear with steps'),
            ('SINE_STEPPED', 'Sine+Step', 'Sine combined with stepped'),
            ('NOISE', 'Noise', 'Random noise'),
        ],
        default='SINE_FULL'
    )
    
    amplitude: FloatProperty(
        name="Amplitude",
        default=1.0,
        min=-100.0,
        max=100.0
    )
    
    phase: FloatProperty(
        name="Phase",
        default=0.0,
        min=-math.pi,
        max=math.pi
    )
    
    frequency: FloatProperty(
        name="Frequency",
        default=1.0,
        min=0.01,
        max=10.0
    )
    
    step_size: FloatProperty(
        name="Step Size",
        default=1.0,
        min=0.1,
        max=100.0
    )
    
    selected_frame_start: IntProperty(
        name="Selected Frame Start",
        description="Start frame of the selected region",
        default=0
    )
    
    selected_frame_end: IntProperty(
        name="Selected Frame End",
        description="End frame of the selected region",
        default=0
    )
    
    selected_value_min: FloatProperty(
        name="Selected Value Min",
        description="Minimum value of the selected region",
        default=0.0
    )
    
    selected_value_max: FloatProperty(
        name="Selected Value Max",
        description="Maximum value of the selected region",
        default=0.0
    )
    
    use_additive: BoolProperty(
        name="Use Additive",
        description="Use additive mode for modifiers",
        default=True
    )


class EMO_ModifierPreset(bpy.types.PropertyGroup):
    name: StringProperty(name="Preset Name")
    preset_type: EnumProperty(
        name="Preset Type",
        items=[
            ('CONSTANT', 'Constant', 'Constant value'),
            ('LINEAR_POS', 'Linear Positive', 'Positive linear function'),
            ('LINEAR_NEG', 'Linear Negative', 'Negative linear function'),
            ('SINE_FULL', 'Full Sine', 'Complete sine wave'),
            ('SINE_BOTTOM', 'Half Sine Bottom', 'Bottom half of sine wave'),
            ('SINE_TOP', 'Half Sine Top', 'Top half of sine wave'),
            ('SINE_HALF_PERIOD', 'Half Period Sine', 'Half period sine wave'),
            ('SQUARE_ROOT', 'Square Root', 'Square root function'),
            ('NATURAL_LOG', 'Natural Log', 'Natural logarithm'),
            ('CUSTOM_BEZIER', 'Custom Bezier', 'User-defined bezier'),
            ('STEPPED_LINEAR', 'Stepped Linear', 'Linear with steps'),
            ('SINE_STEPPED', 'Sine + Stepped', 'Sine combined with stepped'),
            ('NOISE', 'Noise', 'Random noise'),
        ],
        default='SINE_FULL'
    )
    
    amplitude: FloatProperty(
        name="Amplitude",
        default=1.0,
        min=-100.0,
        max=100.0
    )
    
    phase: FloatProperty(
        name="Phase",
        default=0.0,
        min=-math.pi,
        max=math.pi
    )
    
    frequency: FloatProperty(
        name="Frequency",
        default=1.0,
        min=0.01,
        max=10.0
    )
    
    step_size: FloatProperty(
        name="Step Size",
        default=1.0,
        min=0.1,
        max=100.0
    )
    
    offset: FloatProperty(
        name="Offset",
        default=0.0,
        min=-1000.0,
        max=1000.0
    )


_grid_cache = {
    'selected_cells': [],
    'hover_cell': None,
    'is_selecting': False,
    'selection_start': None,
    'selection_end': None,
    'current_preset': 'SINE_FULL',
}


def get_grid_cache():
    return _grid_cache


def clear_grid_selection():
    _grid_cache['selected_cells'] = []
    _grid_cache['selection_start'] = None
    _grid_cache['selection_end'] = None


def cell_to_frame(cell_x, props):
    frame_range = props.frame_end - props.frame_start
    if frame_range <= 0:
        frame_range = 1
    frame_per_cell = frame_range / props.grid_width
    return props.frame_start + cell_x * frame_per_cell


def cell_to_value(cell_y, props):
    value_range = props.value_max - props.value_min
    if value_range <= 0:
        value_range = 1
    value_per_cell = value_range / props.grid_height
    return props.value_max - cell_y * value_per_cell


def frame_to_cell(frame, props):
    frame_range = props.frame_end - props.frame_start
    if frame_range <= 0:
        return 0
    cell_x = int((frame - props.frame_start) * props.grid_width / frame_range)
    return max(0, min(cell_x, props.grid_width - 1))


def value_to_cell(value, props):
    value_range = props.value_max - props.value_min
    if value_range <= 0:
        return 0
    cell_y = int((props.value_max - value) * props.grid_height / value_range)
    return max(0, min(cell_y, props.grid_height - 1))


classes = (
    EMO_GridCell,
    EMO_GridModifierProperties,
    EMO_ModifierPreset,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.emo_grid_props = bpy.props.PointerProperty(type=EMO_GridModifierProperties)
    bpy.types.Scene.emo_modifier_preset = bpy.props.PointerProperty(type=EMO_ModifierPreset)
    print("[E_Motion] Grid modifier properties registered")


def unregister():
    if hasattr(bpy.types.Scene, 'emo_grid_props'):
        del bpy.types.Scene.emo_grid_props
    if hasattr(bpy.types.Scene, 'emo_modifier_preset'):
        del bpy.types.Scene.emo_modifier_preset
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("[E_Motion] Grid modifier properties unregistered")
