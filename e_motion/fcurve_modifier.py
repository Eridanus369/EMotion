import bpy
import math
import numpy as np

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class ModifierExpressionGenerator:
    
    @staticmethod
    def has_modifiers(fcurve):
        if not fcurve or not fcurve.modifiers:
            return False
        return len(fcurve.modifiers) > 0
    
    @staticmethod
    def get_modifier_range(mod):
        use_from = getattr(mod, 'use_from', True)
        use_to = getattr(mod, 'use_to', True)
        
        if use_from and use_to:
            start = getattr(mod, 'from', 0)
            end = getattr(mod, 'to', 100)
            return start, end
        elif use_from:
            start = getattr(mod, 'from', 0)
            end = float('inf')
            return start, end
        elif use_to:
            start = float('-inf')
            end = getattr(mod, 'to', 100)
            return start, end
        else:
            return float('-inf'), float('inf')
    
    @staticmethod
    def generate_generator_polynomial(mod, var='x'):
        coefficients = getattr(mod, 'coefficients', [0.0, 1.0])
        order = getattr(mod, 'poly_order', 1)
        use_additive = getattr(mod, 'use_additive', False)
        
        terms = []
        for i, coef in enumerate(coefficients):
            if abs(coef) < 1e-10:
                continue
            if i == 0:
                terms.append(f"({coef})")
            else:
                terms.append(f"({coef}*{var}**{i})")
        
        if not terms:
            return "0"
        
        expr = " + ".join(terms)
        
        if use_additive:
            return f"({expr})"
        return expr
    
    @staticmethod
    def generate_factored_polynomial(mod, var='x'):
        a = getattr(mod, 'a', 1.0)
        b = getattr(mod, 'b', 0.0)
        use_additive = getattr(mod, 'use_additive', False)
        
        expr = f"({a}*(({var})-({b})))**2+{var})"
        
        if use_additive:
            return f"({expr})"
        return expr
    
    @staticmethod
    def generate_sine(mod, var='x'):
        amplitude = getattr(mod, 'amplitude', 1.0)
        phase_offset = getattr(mod, 'phase_offset', 0.0)
        use_additive = getattr(mod, 'use_additive', False)
        
        expr = f"({amplitude}*math.sin({var}+{phase_offset}))"
        
        if use_additive:
            return f"({expr})"
        return expr
    
    @staticmethod
    def generate_cosine(mod, var='x'):
        amplitude = getattr(mod, 'amplitude', 1.0)
        phase_offset = getattr(mod, 'phase_offset', 0.0)
        use_additive = getattr(mod, 'use_additive', False)
        
        expr = f"({amplitude}*math.cos({var}+{phase_offset}))"
        
        if use_additive:
            return f"({expr})"
        return expr
    
    @staticmethod
    def generate_tangent(mod, var='x'):
        amplitude = getattr(mod, 'amplitude', 1.0)
        phase_offset = getattr(mod, 'phase_offset', 0.0)
        use_additive = getattr(mod, 'use_additive', False)
        
        expr = f"({amplitude}*math.tan({var}+{phase_offset}))"
        
        if use_additive:
            return f"({expr})"
        return expr
    
    @staticmethod
    def generate_square_root(mod, var='x'):
        amplitude = getattr(mod, 'amplitude', 1.0)
        phase_offset = getattr(mod, 'phase_offset', 0.0)
        use_additive = getattr(mod, 'use_additive', False)
        
        expr = f"({amplitude}*math.sqrt(abs({var}+{phase_offset})))"
        
        if use_additive:
            return f"({expr})"
        return expr
    
    @staticmethod
    def generate_natural_log(mod, var='x'):
        amplitude = getattr(mod, 'amplitude', 1.0)
        phase_offset = getattr(mod, 'phase_offset', 0.0)
        use_additive = getattr(mod, 'use_additive', False)
        
        expr = f"({amplitude}*math.log(abs({var}+{phase_offset})))"
        
        if use_additive:
            return f"({expr})"
        return expr
    
    @staticmethod
    def generate_normalized_sine(mod, var='x'):
        amplitude = getattr(mod, 'amplitude', 1.0)
        phase_offset = getattr(mod, 'phase_offset', 0.0)
        use_additive = getattr(mod, 'use_additive', False)
        
        expr = f"({amplitude}*math.sin(({var}+{phase_offset})*2*math.pi)/(2*math.pi))"
        
        if use_additive:
            return f"({expr})"
        return expr
    
    @staticmethod
    def generate_envelope(mod, var='x'):
        default_min = getattr(mod, 'default_min', 0.0)
        default_max = getattr(mod, 'default_max', 1.0)
        use_additive = getattr(mod, 'use_additive', False)
        
        control_points = getattr(mod, 'control_points', [])
        if control_points and len(control_points) >= 2:
            cp1 = control_points[0]
            cp2 = control_points[-1]
            ref_min = cp1.location[1]
            ref_max = cp2.location[1]
        else:
            ref_min = 0.0
            ref_max = 1.0
        
        expr = f"(({var}-{ref_min})/({ref_max}-{ref_min})*({default_max}-{default_min})+{default_min})"
        
        if use_additive:
            return f"({expr})"
        return expr
    
    @staticmethod
    def generate_cycles(mod, var='x', fcurve_start=0, fcurve_end=250):
        before_mode = getattr(mod, 'before_mode', 'CYCLES')
        after_mode = getattr(mod, 'after_mode', 'CYCLES')
        use_additive = getattr(mod, 'use_additive', False)
        
        cycle_before_expr = ""
        cycle_after_expr = ""
        
        if before_mode == 'CYCLES':
            cycle_before_expr = f"(({var}%({fcurve_end}-{fcurve_start})+{fcurve_end}-{fcurve_start})%({fcurve_end}-{fcurve_start})+{fcurve_start})"
        elif before_mode == 'MIRROR':
            cycle_before_expr = f"(abs(({var}-{fcurve_start})%(({fcurve_end}-{fcurve_start})*2)-({fcurve_end}-{fcurve_start}))+{fcurve_start})"
        elif before_mode == 'EXTRAPOLATED':
            cycle_before_expr = var
        else:
            cycle_before_expr = fcurve_start
        
        if after_mode == 'CYCLES':
            cycle_after_expr = f"(({var}-({fcurve_start}))%({fcurve_end}-{fcurve_start})+{fcurve_start})"
        elif after_mode == 'MIRROR':
            cycle_after_expr = f"(abs(({var}-{fcurve_start})%(({fcurve_end}-{fcurve_start})*2)-({fcurve_end}-{fcurve_start}))+{fcurve_start})"
        elif after_mode == 'EXTRAPOLATED':
            cycle_after_expr = var
        else:
            cycle_after_expr = fcurve_end
        
        expr = f"(({var}<{fcurve_start})*({cycle_before_expr})+({var}>={fcurve_start})*({var}<={fcurve_end})*({var})+({var}>{fcurve_end})*({cycle_after_expr}))"
        
        if use_additive:
            return f"({expr})"
        return expr
    
    @staticmethod
    def generate_noise(mod, var='x'):
        amplitude = getattr(mod, 'amplitude', 1.0)
        scale = getattr(mod, 'scale', 0.5)
        offset = getattr(mod, 'offset', 0.0)
        phase = getattr(mod, 'phase', 0.0)
        seed = getattr(mod, 'seed', 0)
        use_additive = getattr(mod, 'use_additive', False)
        
        noise_expr = f"(({var}+{offset}+{phase})*{scale}+{seed})"
        expr = f"({amplitude}*(math.sin({noise_expr}*1.618033988)*2-1)*math.sin({noise_expr}*3.618033988)*0.5)"
        
        if use_additive:
            return f"({expr})"
        return expr
    
    @staticmethod
    def generate_limits(mod, var='x'):
        use_min = getattr(mod, 'use_min', False)
        use_max = getattr(mod, 'use_max', False)
        min_limit = getattr(mod, 'min_limit', 0.0)
        max_limit = getattr(mod, 'max_limit', 1.0)
        use_additive = getattr(mod, 'use_additive', False)
        
        if use_min and use_max:
            expr = f"(max({min_limit}, min({var}, {max_limit})))"
        elif use_min:
            expr = f"(max({min_limit}, {var}))"
        elif use_max:
            expr = f"(min({var}, {max_limit}))"
        else:
            expr = var
        
        if use_additive:
            return f"({expr})"
        return expr
    
    @staticmethod
    def generate_stepped(mod, var='x'):
        step_size = getattr(mod, 'step_size', 1.0)
        offset = getattr(mod, 'offset', 0.0)
        use_additive = getattr(mod, 'use_additive', False)
        
        expr = f"(({var}+{offset})//{step_size}*{step_size}-{offset})"
        
        if use_additive:
            return f"({expr})"
        return expr
    
    @staticmethod
    def generate_modifier_expression(mod, var='x', fcurve_start=0, fcurve_end=250):
        mod_type = mod.type
        
        print(f"[F-Curve Modifier] Processing modifier type: {mod_type}")
        
        try:
            if mod_type == 'GENERATOR':
                if hasattr(mod, 'mode') and mod.mode == 'POLYNOMIAL':
                    return ModifierExpressionGenerator.generate_generator_polynomial(mod, var)
                else:
                    return ModifierExpressionGenerator.generate_factored_polynomial(mod, var)
            
            elif mod_type == 'FNGENERATOR':
                function = getattr(mod, 'function', 'SINE')
                if function == 'SINE':
                    return ModifierExpressionGenerator.generate_sine(mod, var)
                elif function == 'COSINE':
                    return ModifierExpressionGenerator.generate_cosine(mod, var)
                elif function == 'TANGENT':
                    return ModifierExpressionGenerator.generate_tangent(mod, var)
                elif function == 'SQRT':
                    return ModifierExpressionGenerator.generate_square_root(mod, var)
                elif function == 'LN':
                    return ModifierExpressionGenerator.generate_natural_log(mod, var)
                elif function == 'NORMALISED_SINE':
                    return ModifierExpressionGenerator.generate_normalized_sine(mod, var)
            
            elif mod_type == 'ENVELOPE':
                return ModifierExpressionGenerator.generate_envelope(mod, var)
            
            elif mod_type == 'CYCLES':
                return ModifierExpressionGenerator.generate_cycles(mod, var, fcurve_start, fcurve_end)
            
            elif mod_type == 'NOISE':
                return ModifierExpressionGenerator.generate_noise(mod, var)
            
            elif mod_type == 'LIMITS':
                return ModifierExpressionGenerator.generate_limits(mod, var)
            
            elif mod_type == 'STEPPED':
                return ModifierExpressionGenerator.generate_stepped(mod, var)
            
            else:
                print(f"[F-Curve Modifier] Unknown modifier type: {mod_type}")
                return "0"
                
        except Exception as e:
            print(f"[F-Curve Modifier] Error generating expression for {mod_type}: {e}")
            return "0"
    
    @staticmethod
    def get_fcurve_time_range(fcurve):
        if not fcurve or not fcurve.keyframe_points:
            return 0, 250
        
        times = [kp.co.x for kp in fcurve.keyframe_points]
        return min(times), max(times)
    
    @staticmethod
    def build_modifier_expression(fcurve):
        if not ModifierExpressionGenerator.has_modifiers(fcurve):
            print("[F-Curve Modifier] No modifiers found on fcurve")
            return None
        
        modifiers = list(fcurve.modifiers)
        
        fcurve_start, fcurve_end = ModifierExpressionGenerator.get_fcurve_time_range(fcurve)
        
        expressions = []
        
        for i, mod in enumerate(modifiers):
            mod_start, mod_end = ModifierExpressionGenerator.get_modifier_range(mod)
            influence = getattr(mod, 'influence', 1.0)
            use_additive = getattr(mod, 'use_additive', False)
            
            mod_expr = ModifierExpressionGenerator.generate_modifier_expression(
                mod, 'x', fcurve_start, fcurve_end
            )
            
            if influence != 1.0:
                if use_additive:
                    mod_expr = f"({mod_expr})"
                else:
                    mod_expr = f"({influence}*({mod_expr}))"
            
            print(f"[F-Curve Modifier] Modifier {i}: {mod.type}, range: [{mod_start}, {mod_end}], additive: {use_additive}")
            
            if mod_start == float('-inf') and mod_end == float('inf'):
                range_expr = "1"
            elif mod_start == float('-inf'):
                range_expr = f"({mod_end}-x)/({mod_end}-{fcurve_start})"
            elif mod_end == float('inf'):
                range_expr = f"(x-{mod_start})/({fcurve_end}-{mod_start})"
            else:
                range_expr = f"(({x}>=x_start)*({x}<={x_end})*1.0)"
            
            expressions.append({
                'expression': mod_expr,
                'start': mod_start,
                'end': mod_end,
                'influence': influence,
                'additive': use_additive
            })
        
        return expressions


def evaluate_fcurve_with_modifiers(fcurve, frame):
    if not fcurve:
        return 0.0
    
    base_value = fcurve.evaluate(frame)
    
    if not ModifierExpressionGenerator.has_modifiers(fcurve):
        return base_value
    
    return base_value


def get_fcurve_final_expression(fcurve, var_name='x'):
    if not fcurve:
        print("[F-Curve Final] No fcurve provided")
        return "0"
    
    if not ModifierExpressionGenerator.has_modifiers(fcurve):
        print("[F-Curve Final] No modifiers, returning base expression")
        if fcurve.keyframe_points and len(fcurve.keyframe_points) > 0:
            times = [kp.co.x for kp in fcurve.keyframe_points]
            values = [kp.co.y for kp in fcurve.keyframe_points]
            
            if len(times) == 1:
                return f"({values[0]})"
            
            segments = []
            for i in range(len(times) - 1):
                t0, t1 = times[i], times[i + 1]
                v0, v1 = values[i], values[i + 1]
                
                if t1 != t0:
                    slope = (v1 - v0) / (t1 - t0)
                    intercept = v0 - slope * t0
                    segment = f"(({var_name}>={t0})*({var_name}<{t1})*({intercept}+{slope}*{var_name}))"
                    segments.append(segment)
            
            if segments:
                return "(" + " + ".join(segments) + ")"
        
        return f"{var_name}"
    
    expressions = ModifierExpressionGenerator.build_modifier_expression(fcurve)
    
    if not expressions:
        print("[F-Curve Final] No modifier expressions generated")
        return f"{var_name}"
    
    print(f"[F-Curve Final] Generated {len(expressions)} modifier expressions")
    
    combined_expr = f"({var_name})"
    for expr_data in expressions:
        mod_expr = expr_data['expression']
        start = expr_data['start']
        end = expr_data['end']
        influence = expr_data['influence']
        
        if start == float('-inf') and end == float('inf'):
            range_mult = "1"
        elif start == float('-inf'):
            range_mult = f"max(0, ({end}-{var_name})/({end}-({var_name}))"
        elif end == float('inf'):
            range_mult = f"max(0, ({var_name}-{start})/(({var_name})-({start})))"
        else:
            range_mult = f"(({var_name}>={start})*({var_name}<={end}))"
        
        if influence != 1.0:
            mod_expr = f"({influence}*({mod_expr}))"
        
        combined_expr = f"({combined_expr}+{range_mult}*({mod_expr}))"
    
    return combined_expr


def register():
    print("[F-Curve Modifier] Module loaded")


def unregister():
    print("[F-Curve Modifier] Module unloaded")
