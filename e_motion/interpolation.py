import numpy as np


class InterpolationLibrary:
    INTERP_MAP = {
        'CONSTANT': 0,
        'LINEAR': 1,
        'BEZIER': 2,
        'SINE': 3,
        'QUAD': 4,
        'CUBIC': 5,
        'QUART': 6,
        'QUINT': 7,
        'EXPO': 8,
        'CIRC': 9,
        'BACK': 10,
        'BOUNCE': 11,
        'ELASTIC': 12,
    }

    @staticmethod
    def constant_func(t, val):
        return val

    @staticmethod
    def bezier_func(t, p0, p1, p2, p3):
        t2 = t * t
        t3 = t2 * t
        mt = 1 - t
        mt2 = mt * mt
        mt3 = mt2 * mt
        bezier = mt3 * p0 + 3 * mt2 * t * p1 + 3 * mt * t2 * p2 + t3 * p3
        return bezier

    @staticmethod
    def linear_func(t, p0, p1):
        linear = p0 + t * (p1 - p0)
        return linear

    @staticmethod
    def ease_sine_func(t, p0, p1):
        sine = p0 + (p1 - p0) * (1 - np.cos(t * np.pi / 2))
        return sine

    @staticmethod
    def ease_func(t, p0, p1, i):
        ease = p0 + (p1 - p0) * (t ** i)
        return ease

    @staticmethod
    def ease_expo_func(t, p0, p1):
        if t == 0:
            return p0
        expo = p0 + (p1 - p0) * (2 ** (10 * (t - 1)))
        return expo

    @staticmethod
    def ease_circ_func(t, p0, p1):
        circ = p0 + (p1 - p0) * (1 - np.sqrt(1 - t ** 2))
        return circ

    @staticmethod
    def bounce_func(t, p0, p1):
        val = t
        if val < 4 / 11:
            bounce = p0 + (p1 - p0) * (121 * val ** 2 / 16)
            return bounce
        elif val < 8 / 11:
            val = val - 6 / 11
            bounce = p0 + (p1 - p0) * (121 * val ** 2 / 16 + 3 / 4)
            return bounce
        elif val < 10 / 11:
            val = val - 9 / 11
            bounce = p0 + (p1 - p0) * (121 * val ** 2 / 16 + 15 / 16)
            return bounce
        else:
            val = val - 21 / 22
            bounce = p0 + (p1 - p0) * (121 * val ** 2 / 16 + 63 / 64)
            return bounce

    @staticmethod
    def elastic_func(t, p0, p1, amplitude=0.1, period=0.2):
        if t == 0:
            return p0
        if t == 1:
            return p1
        s = period / (2 * np.pi) * np.arcsin(1 / amplitude)
        elastic = p0 + (p1 - p0) * (-amplitude * (2 ** (10 * (t - 1))) * np.sin((t - 1 - s) * (2 * np.pi) / period))
        return elastic

    @staticmethod
    def rebound_func(t, p0, p1):
        rebound = p0 + (p1 - p0) * (t ** 2 * (3 - 2 * t))
        return rebound

    @classmethod
    def get_interp_function(cls, interp_name):
        interp_map = {
            "CONSTANT": (cls.constant_func, 2),
            "LINEAR": (cls.linear_func, 2),
            "BEZIER": (cls.bezier_func, 4),
            "SINE": (cls.ease_sine_func, 2),
            "QUAD": (lambda t, p0, p1: cls.ease_func(t, p0, p1, 2), 2),
            "CUBIC": (lambda t, p0, p1: cls.ease_func(t, p0, p1, 3), 2),
            "QUART": (lambda t, p0, p1: cls.ease_func(t, p0, p1, 4), 2),
            "QUINT": (lambda t, p0, p1: cls.ease_func(t, p0, p1, 5), 2),
            "EXPO": (cls.ease_expo_func, 2),
            "CIRC": (cls.ease_circ_func, 2),
            "BACK": (cls.rebound_func, 2),
            "BOUNCE": (cls.bounce_func, 2),
            "ELASTIC": (cls.elastic_func, 2),
        }

        if interp_name not in interp_map:
            raise ValueError(f"Unknown interpolation type: {interp_name}, "
                             f"Supported types: {list(interp_map.keys())}")
        return interp_map[interp_name]

    @classmethod
    def blender_interp_to_name(cls, blender_interp):
        interp_names = {
            0: "CONSTANT",
            1: "LINEAR",
            2: "BEZIER",
        }
        return interp_names.get(blender_interp, "BEZIER")


def register():
    pass


def unregister():
    pass
