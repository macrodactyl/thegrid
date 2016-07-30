# A flame-like fireplace sort of effect.

import numpy as np
from math import sqrt, sin, cos, pi
from .pattern import Pattern, register_pattern
from colorsys import hsv_to_rgb

@register_pattern("Fire")
class PatternColourwave(Pattern):
    def __init__(self, cfg, tracking):
        self.arr = np.zeros((7, 7, 3), dtype=np.uint8)

    def update(self):
        # For every pixel not at the base of a column, set the pixel above it
        # to a darker version of the pixel below
        for x in range(7):
            for y in range(6):
                self.arr[y, x] = self.arr[y+1, x] * 0.8

        # Set a random yellow/orange colour at the base of each column
        for x in range(7):
            self.arr[6, x] = (np.random.rand()*20+235,
                              np.random.rand()*100+55,
                              0)

        return self.arr, 0.01
