import bpy
import re
import math
from .curve import extract_fcurve_to_curve
from . import fcurve_modifier


_cache = {
    "curves": {},
    "curves_with_mods": {},
    "obj_expr": {},
    "driver_data": {},
    "var_cache": {},
}


def get_cache():
    return _cache


class TimeExpressionParser:
    
    @staticmethod
    def parse(expr, frame):
        if not expr or not expr.strip():
            return frame
        
        expr = expr.strip()
        
        if expr.startswith('~'):
            try:
                return int(round(float(expr[1:])))
            except:
                return frame
        
        has_letter = bool(re.search(r'[a-zA-Z]', expr))
        
        if has_letter:
            expr_processed = expr
            expr_processed = re.sub(r'\bf\b', 'frame', expr_processed)
            expr_processed = re.sub(r'\bframe\b', str(frame), expr_processed)
            
            other_letters = re.findall(r'[a-zA-Z]+', expr_processed)
            for letter in other_letters:
                if letter not in ['abs', 'round', 'sin', 'cos', 'tan', 'sqrt', 'pow', 'min', 'max', 'pi', 'e']:
                    expr_processed = re.sub(r'\b' + letter + r'\b', str(frame), expr_processed)
        else:
            expr_processed = f"frame{expr}"
            expr_processed = expr_processed.replace('frame', str(frame))
        
        try:
            result = eval(expr_processed, {"__builtins__": {"abs": abs, "round": round, "min": min, "max": max, "pow": pow}}, {"pi": math.pi, "e": math.e})
            return int(round(result))
        except:
            return frame


def em_time(driver_obj_name, var_name, time_expr=""):
    cache = get_cache()
    
    try:
        frame = bpy.context.scene.frame_current
    except:
        return 0.0
    
    if time_expr:
        expr = time_expr
    else:
        expr = cache["obj_expr"].get(driver_obj_name, "f")
    
    if not expr:
        expr = "f"
    
    new_time = TimeExpressionParser.parse(expr, frame)
    
    driver_data = cache["driver_data"].get(driver_obj_name, {})
    var_data = driver_data.get(var_name, {})
    
    curve_key = var_data.get("curve_key", "")
    if not curve_key:
        curve_key = f"{driver_obj_name}:{var_name}"
    
    if curve_key in cache["curves"]:
        curve = cache["curves"][curve_key]
        
        fcurve_with_mods = cache["curves_with_mods"].get(curve_key)
        
        if fcurve_with_mods:
            print(f"[em_time] Using modifiers for: {curve_key}")
            return fcurve_modifier.evaluate_fcurve_with_modifiers(fcurve_with_mods, float(new_time))
        
        return curve.get_value(float(new_time))
    
    return 0.0


def em_eval(driver_obj_name, var_name, expr=""):
    return em_time(driver_obj_name, var_name, expr)


class DriverVariableInfo:
    
    VARIABLE_TYPES = {
        'SINGLE_PROP': '单个属性',
        'TRANSFORMS': '变换通道',
        'ROTATION_DIFF': '旋转差值',
        'LOC_DIFF': '距离',
        'CONTEXT_PROP': '上下文属性',
    }
    
    def __init__(self, name, var_type, targets=None, curve=None, target_obj=None, data_path=None):
        self.name = name
        self.var_type = var_type
        self.targets = targets or []
        self.curve = curve
        self.target_obj = target_obj
        self.data_path = data_path

    def get_display_name(self):
        type_name = self.VARIABLE_TYPES.get(self.var_type, self.var_type)
        return f"{self.name} ({type_name})"

    def evaluate_at_time(self, t):
        if self.curve:
            return self.curve.get_value(float(t))
        return None


def _get_transform_data_path_and_index(transform_type, bone_target="", rotation_mode="AUTO"):
    bone_prefix = f'pose.bones["{bone_target}"].' if bone_target else ""
    
    transform_map = {
        'LOC_X': (f'{bone_prefix}location', 0),
        'LOC_Y': (f'{bone_prefix}location', 1),
        'LOC_Z': (f'{bone_prefix}location', 2),
        'SCALE_X': (f'{bone_prefix}scale', 0),
        'SCALE_Y': (f'{bone_prefix}scale', 1),
        'SCALE_Z': (f'{bone_prefix}scale', 2),
        'SCALE_AVG': (f'{bone_prefix}scale', 0),
    }
    
    if transform_type.startswith('ROT_'):
        if rotation_mode == 'QUATERNION' or transform_type == 'ROT_W':
            rot_map = {
                'ROT_W': (f'{bone_prefix}rotation_quaternion', 0),
                'ROT_X': (f'{bone_prefix}rotation_quaternion', 1),
                'ROT_Y': (f'{bone_prefix}rotation_quaternion', 2),
                'ROT_Z': (f'{bone_prefix}rotation_quaternion', 3),
            }
            transform_map.update(rot_map)
        elif rotation_mode == 'SWING_TWIST':
            rot_map = {
                'ROT_X': (f'{bone_prefix}rotation_quaternion', 1),
                'ROT_Y': (f'{bone_prefix}rotation_quaternion', 2),
                'ROT_Z': (f'{bone_prefix}rotation_quaternion', 3),
            }
            transform_map.update(rot_map)
        else:
            rot_map = {
                'ROT_X': (f'{bone_prefix}rotation_euler', 0),
                'ROT_Y': (f'{bone_prefix}rotation_euler', 1),
                'ROT_Z': (f'{bone_prefix}rotation_euler', 2),
            }
            transform_map.update(rot_map)
    
    result = transform_map.get(transform_type, ("", -1))
    return result[0], result[1]


def _extract_variable_info(var):
    var_info = DriverVariableInfo(
        name=var.name,
        var_type=var.type,
        targets=[],
        curve=None,
        target_obj=None,
        data_path=None
    )
    
    if var.type == 'SINGLE_PROP':
        for target in var.targets:
            if target.id:
                var_info.target_obj = target.id
                var_info.data_path = target.data_path
                var_info.targets.append({
                    'object': target.id.name if hasattr(target.id, 'name') else str(target.id),
                    'data_path': target.data_path,
                })
                
                target_id = target.id
                if target_id and hasattr(target_id, 'animation_data') and target_id.animation_data:
                    action = target_id.animation_data.action
                    if action:
                        for fcu in action.fcurves:
                            if fcu.data_path == target.data_path:
                                var_info.curve = extract_fcurve_to_curve(fcu)
                                
                                if fcurve_modifier.ModifierExpressionGenerator.has_modifiers(fcu):
                                    var_info.targets[0]['fcurve_with_mods'] = fcu
                                    print(f"[Driver] Found modifiers on fcurve: {target.data_path}")
                                break
    
    elif var.type == 'TRANSFORMS':
        for target in var.targets:
            if target.id:
                var_info.target_obj = target.id
                bone_target = target.bone_target if hasattr(target, 'bone_target') else ""
                transform_type = target.transform_type if hasattr(target, 'transform_type') else ""
                rotation_mode = target.rotation_mode if hasattr(target, 'rotation_mode') else "AUTO"
                
                data_path, array_index = _get_transform_data_path_and_index(transform_type, bone_target, rotation_mode)
                var_info.data_path = data_path
                var_info.targets.append({
                    'object': target.id.name if hasattr(target.id, 'name') else str(target.id),
                    'transform_type': transform_type,
                    'bone_target': bone_target,
                    'rotation_mode': rotation_mode,
                    'array_index': array_index,
                })
                
                target_id = target.id
                if target_id:
                    if hasattr(target_id, 'animation_data') and target_id.animation_data:
                        action = target_id.animation_data.action
                        if action:
                            for fcu in action.fcurves:
                                if data_path and fcu.data_path == data_path and fcu.array_index == array_index:
                                    var_info.curve = extract_fcurve_to_curve(fcu)
                                    
                                    if fcurve_modifier.ModifierExpressionGenerator.has_modifiers(fcu):
                                        var_info.targets[-1]['fcurve_with_mods'] = fcu
                                        print(f"[Driver] Found modifiers on fcurve: {data_path}[{array_index}]")
                                    break
    
    elif var.type == 'ROTATION_DIFF':
        for target in var.targets:
            if target.id:
                var_info.targets.append({
                    'object': target.id.name if hasattr(target.id, 'name') else str(target.id),
                    'bone_target': target.bone_target if hasattr(target, 'bone_target') else "",
                })
    
    elif var.type == 'LOC_DIFF':
        for target in var.targets:
            if target.id:
                var_info.targets.append({
                    'object': target.id.name if hasattr(target.id, 'name') else str(target.id),
                    'bone_target': target.bone_target if hasattr(target, 'bone_target') else "",
                })
    
    elif var.type == 'CONTEXT_PROP':
        for target in var.targets:
            var_info.targets.append({
                'context': target.context_property if hasattr(target, 'context_property') else "",
                'data_path': target.data_path
            })
    
    return var_info


def get_driver_variables(obj):
    if not obj or not obj.animation_data:
        return []
    
    variables_info = []
    
    for driver in obj.animation_data.drivers:
        if driver.driver:
            for var in driver.driver.variables:
                var_info = _extract_variable_info(var)
                if var_info:
                    variables_info.append(var_info)
    
    return variables_info


def refresh_driver_cache(obj):
    cache = get_cache()
    
    if obj.name not in cache["driver_data"]:
        cache["driver_data"][obj.name] = {}
    
    variables = get_driver_variables(obj)
    cache["var_cache"][obj.name] = variables
    
    for var in variables:
        if var.curve and var.curve.keyframes:
            source_obj_name = ""
            fcurve_with_mods = None
            
            if var.targets and len(var.targets) > 0:
                source_obj_name = var.targets[0].get('object', '')
                if source_obj_name.startswith('OB'):
                    source_obj_name = source_obj_name[2:]
                fcurve_with_mods = var.targets[0].get('fcurve_with_mods')
            
            curve_key = f"{source_obj_name}:{var.data_path}" if source_obj_name else f"{obj.name}:{var.name}"
            cache["curves"][curve_key] = var.curve
            
            if fcurve_with_mods:
                cache["curves_with_mods"][curve_key] = fcurve_with_mods
                print(f"[Driver] Stored fcurve with modifiers: {curve_key}")
            
            cache["driver_data"][obj.name][var.name] = {
                "curve_key": curve_key,
                "source_obj": source_obj_name,
                "data_path": var.data_path,
                "has_modifiers": fcurve_with_mods is not None,
            }
    
    return variables


def apply_driver_expression(obj, time_expr):
    cache = get_cache()
    cache["obj_expr"][obj.name] = time_expr
    
    modified_count = 0
    for driver in obj.animation_data.drivers:
        if driver.driver:
            original_expr = driver.driver.expression
            
            for var in driver.driver.variables:
                if var.name in original_expr:
                    new_expr = original_expr.replace(
                        var.name, 
                        f'em_time("{obj.name}", "{var.name}")'
                    )
                    driver.driver.expression = new_expr
                    modified_count += 1
                    break
    
    return modified_count


def reset_driver_expression(obj):
    reset_count = 0
    for driver in obj.animation_data.drivers:
        if driver.driver:
            original_expr = driver.driver.expression
            
            if 'em_time' in original_expr:
                new_expr = re.sub(r'em_time\("[^"]*",\s*"([^"]*)"\)', r'\1', original_expr)
                driver.driver.expression = new_expr
                reset_count += 1
    
    return reset_count


def register():
    pass


def unregister():
    pass
