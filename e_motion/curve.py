from bisect import bisect_right
from .interpolation import InterpolationLibrary


class KeyframeSegment:

    def __init__(self, start_time, end_time, start_value, end_value,
                 interp_type="LINEAR", handle_left=None, handle_right=None):
        self.start_time = start_time
        self.end_time = end_time
        self.start_value = start_value
        self.end_value = end_value
        self.interp_type = interp_type
        self.duration = end_time - start_time
        self.handle_left = handle_left
        self.handle_right = handle_right
        self.interp_params = self._prepare_params()
        self.interp_func, self.param_count = InterpolationLibrary.get_interp_function(interp_type)

    def _prepare_params(self):
        if self.interp_type == "BEZIER":
            if self.handle_left is not None and self.handle_right is not None:
                return [self.start_value, self.handle_left, self.handle_right, self.end_value]
            else:
                mid = (self.start_value + self.end_value) / 2
                return [self.start_value, mid, mid, self.end_value]
        else:
            return [self.start_value, self.end_value]

    def evaluate(self, t):
        if t <= self.start_time:
            return self.start_value
        if t >= self.end_time:
            return self.end_value
        t_norm = (t - self.start_time) / self.duration if self.duration > 0 else 0
        if self.interp_type == "BEZIER":
            return self.interp_func(t_norm, *self.interp_params)
        else:
            return self.interp_func(t_norm, *self.interp_params[:2])

    def get_derivative(self, t):
        epsilon = 1e-6
        t1 = max(self.start_time, min(t, self.end_time))
        t2 = min(self.end_time, t1 + epsilon)
        v1 = self.evaluate(t1)
        v2 = self.evaluate(t2)
        return (v2 - v1) / (t2 - t1)


class AnimationCurve:

    def __init__(self):
        self.keyframes = []
        self.segments = []
        self.time_array = []

    def add_keyframe(self, time, value, interp_type="LINEAR", handle_left=None, handle_right=None):
        self.keyframes.append((time, value, interp_type, handle_left, handle_right))
        self.keyframes.sort(key=lambda x: x[0])
        self._rebuild_segments()

    def _rebuild_segments(self):
        self.segments = []
        self.time_array = []
        if len(self.keyframes) < 2:
            return
        for i in range(len(self.keyframes) - 1):
            t1, v1, interp_type, handle_left, handle_right = self.keyframes[i]
            t2, v2, _, next_handle_left, next_handle_right = self.keyframes[i + 1]
            
            handle_r = handle_right if handle_right is not None else v1
            handle_l = next_handle_left if next_handle_left is not None else v2
            
            segment = KeyframeSegment(t1, t2, v1, v2, interp_type, handle_r, handle_l)
            self.segments.append(segment)
            self.time_array.append(t1)
        self.time_array.append(self.keyframes[-1][0])

    def evaluate(self, t):
        if not self.segments:
            return self.keyframes[0][1] if self.keyframes else 0.0
        if t <= self.time_array[0]:
            return self.keyframes[0][1]
        if t >= self.time_array[-1]:
            return self.keyframes[-1][1]
        idx = bisect_right(self.time_array, t) - 1
        idx = max(0, min(idx, len(self.segments) - 1))
        segment = self.segments[idx]
        return segment.evaluate(t)

    def get_value(self, t):
        return self.evaluate(t)


def extract_fcurve_to_curve(fcu):
    if not fcu or not fcu.keyframe_points:
        return None
    
    curve = AnimationCurve()
    for kp in fcu.keyframe_points:
        time = kp.co[0]
        value = kp.co[1]
        interp_type = InterpolationLibrary.blender_interp_to_name(kp.interpolation)
        
        handle_left = None
        handle_right = None
        
        if interp_type == "BEZIER":
            handle_left = kp.handle_left[1] if hasattr(kp, 'handle_left') else None
            handle_right = kp.handle_right[1] if hasattr(kp, 'handle_right') else None
        
        curve.add_keyframe(time, value, interp_type, handle_left, handle_right)
    
    return curve


def register():
    pass


def unregister():
    pass
