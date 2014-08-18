"""
The patterns package contains all the pattern modules, plus a decorator and
base class in `patterns.pattern`.

Add any new patterns here with `from . import <name>`.
"""

from . import pong, amaze, sparkle, playlist, static_patterns, on, sample
from .musicpatterns import thegrid

from .pattern import loaded_patterns
