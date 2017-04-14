# -*- coding: utf-8 -*-

import math

from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QColor


def hsl(hue, saturation, lightness, alpha=100):
    return QColor.fromHsvF((hue % 360) / 360, saturation / 100, lightness / 100, alpha / 100)

def deg2rad(deg):
    return deg / 180 * math.pi

def rad2deg(rad):
    return rad * 180 / math.pi

def lerp(x, old_min, old_max, new_min, new_max, clip_=False):
    x = (x - old_min) / (old_max - old_min) * (new_max - new_min) + new_min
    if clip_: return clip(x, new_min, new_max)
    return x

def clip(x, min, max):
    if x < min: return min
    if x > max: return max
    return x

def lengthsq(p):
    return QPointF.dotProduct(p, p)

def length(p):
    return math.sqrt(lengthsq(p))

def normalized(p):
    if p.isNull():
        return QPointF(1, 0)
    return p / length(p)

def normalized_or_null(p):
    if p.isNull():
        return p
    return p / length(p)
