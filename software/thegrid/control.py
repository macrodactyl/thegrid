import sys
import argparse
import struct
import asyncio
import logging
import json
import numpy as np
from imp import reload

from . import patterns, web, serial

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('--serial-port')
parser.add_argument('--web-host', default='localhost',
                    help="Host/IP for HTTP server")
parser.add_argument('--web-port', default=8080, help="Port for HTTP server")
parser.add_argument('--password', default="hunter2",
                    help="Password for web admin access")
args = parser.parse_args()


class Control:
    def __init__(self):
        self.loop = asyncio.get_event_loop()

        # Set up UI interface
        self.ui = dict()

        # Grab loaded patterns
        self.pattern = None
        self.pattern_name = None
        self.patterns = patterns.loaded_patterns

        # Store password for admin access
        self.password = args.password

    @asyncio.coroutine
    def setup(self):
        logger.info("Starting up")

        # Start HTTP server
        web.start_server(args.web_host, args.web_port, self)

        # Set up serial port
        if args.serial_port:
            logger.info("Opening serial port %s", args.serial_port)
            yield from serial.open(args.serial_port)

        # Enqueue first pattern thing
        self.loop.call_soon(self.run_pattern)

    def shutdown(self):
        logger.info("Shutting down")

        # Stop HTTP server
        web.stop_server()

        # Delete pattern
        del self.pattern

    def load_pattern(self, name):
        # First kill old pattern
        if self.pattern is not None:
            # Call a shutdown method if one exists:
            if hasattr(self.pattern, "shutdown"):
                logger.info("Calling shutdown method on old pattern")
                self.pattern.shutdown()
            del self.pattern
            self.pattern = None
            self.pattern_name = None

        logger.info("Loading pattern %s", name)
        cls, cfg = self.patterns[name]
        self.pattern = cls(cfg, self.ui)
        self.pattern_name = name

    def reload_patterns(self):
        logger.info("Reloading patterns")
        reload(sys.modules["thegrid.pattern"])
        for mod in sys.modules:
            if mod.startswith("thegrid.patterns."):
                reload(sys.modules[mod])
        self.patterns = sys.modules["thegrid.patterns"].loaded_patterns

    def run_pattern(self):
        # Skip if no pattern loaded
        if getattr(self, 'pattern') is None:
            self.loop.call_later(1, self.run_pattern)
            return

        try:
            poles, delay = self.pattern.update()
        except StopIteration:
            logger.info("Pattern %s stopped, restarting in 1 second",
                        self.pattern_name)
            self.clear_grid()
            self.load_pattern(self.pattern_name)
            self.loop.call_later(1, self.run_pattern)
        except Exception:
            logger.exception("Error in pattern %s, restarting in 1 second",
                             self.pattern_name)
            self.clear_grid()
            self.load_pattern(self.pattern_name)
            self.loop.call_later(1, self.run_pattern)
        else:
            # Enqueue next frame
            self.loop.call_later(delay, self.run_pattern)

            def off(row, col, grid):
                return (grid[row, col, 0] == 0 and
                    grid[row, col, 1] == 0 and
                    grid[row, col, 2] == 0 and (
                    grid[row, col, 3] == 0 or
                    grid[row, col, 5] == 0))

            sync = b"\xFF" * 6
            cmd = b"\xFC"
            for row in range(7):
                rowbyte = 0
                for col in range(7):
                    if not off(6-row, 6-col, poles):
                        rowbyte |= 1 << col
                cmd += struct.pack("B", rowbyte)
            cmd += b"\x00" * (398-14)
            serial.write_raw(sync + cmd)

            # Enqueue writing new frame to serial port and web sockets
            self.send_frame(poles)

    def send_frame(self, poles):
        serial.write(poles)
        ws_str = json.dumps(poles.tolist())
        for ws in web.app['sockets']:
            ws.send_str(ws_str)

    def clear_grid(self):
        poles = np.zeros((7, 7, 6), dtype=np.uint8)
        self.send_frame(poles)
