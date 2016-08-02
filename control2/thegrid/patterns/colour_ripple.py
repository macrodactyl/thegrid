"""
Colour ripple pattern

Colours will rippple from the centre of The Grid, with the colour changing
gradually through the spectrum.  Pretty!  Hopefully.
"""

import collections
import copy
import itertools
import numpy as np
import logging
from ..pattern import Pattern, register_pattern
logger = logging.getLogger(__name__)


@register_pattern("ColourRipple")
class ColourRipple(Pattern):
    """
    Colour ripple pattern

    Colours will emanate from the centre of the grid, with colour moving
    gradually through the spectrum.
    """

    def __init__(self, config, ui):
        super().__init__(config, ui)
        self.grid_gen = self.generate_grid()

    @staticmethod
    def colour_gradient(n=10):
        """Yields deque containing four RGB tuples."""
        colours = collections.deque(maxlen=4)
        for _ in range(4):
            colours.appendleft(tuple([255, 255, 255]))

        red = [255, 0, 0]
        green = [0, 255, 0]
        blue = [0, 0, 255]
        start_rgb_cycle = itertools.cycle([red, green, blue])
        end_rgb_cycle = itertools.cycle([green, blue, red])

        while True:
            start_rgb = next(start_rgb_cycle)
            end_rgb = next(end_rgb_cycle)
            for i in range(n):
                rgb = [int(start_rgb[channel] +
                       i/n * (end_rgb[channel] - start_rgb[channel]))
                       for channel in range(3)]
                colours.appendleft(tuple(rgb))
                yield colours

    def update(self):
        """Return a tuple of (new_grid, update_time)"""
        return next(self.grid_gen), 1/10

    def generate_grid(self):
        colour_gradient = self.colour_gradient()
        grid = np.zeros((7, 7, 6), dtype=np.uint8)

        while True:
            colours = copy.deepcopy(next(colour_gradient))
            grid[3][3] = colours.popleft() + (0, 0, 0)

            for i, j in zip([2, 1, 0], [4, 5, 6]):
                c = colours.popleft()
                grid[:, i] = c + (0, 0, 0)
                grid[:, j] = c + (0, 0, 0)
                grid[i, :] = c + (0, 0, 0)
                grid[j, :] = c + (0, 0, 0)

            yield grid
