"""
One-by-one example for the Pico driver `tree_pico`.

This version uses simple RGB tuples so it runs under MicroPython without
the colorzero dependency. Set `debug=True` to see diagnostic output
in the REPL and `force_bitbang=True` if you suspect PIO issues.
"""
from tree_pico import RGBXmasTree
import time

# Use Pico pins (GP9 data, GP28 clock) and enable debug for diagnostics
tree = RGBXmasTree(pixels=25, data_pin=9, clock_pin=28, debug=True)

# Simple color tuples in range 0..1
colors = [
    (1.0, 0.0, 0.0),  # red
    (0.0, 1.0, 0.0),  # green
    (0.0, 0.0, 1.0),  # blue
]

try:
    while True:
        for color in colors:
            for pixel in tree:
                pixel.color = color
                # small pacing delay so the visual effect is visible
                time.sleep(0.05)
except KeyboardInterrupt:
    tree.off()
    tree.close()
