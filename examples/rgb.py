"""
Simple RGB example for the Pico using `tree_pico`.

This example cycles the whole tree through red, green, and blue colors. It uses
simple RGB tuples instead of the colorzero library so it runs under MicroPython.
"""
from tree_pico import RGBXmasTree
import time

tree = RGBXmasTree(pixels=25, data_pin=9, clock_pin=28, debug=True)

colors = [
    (1.0, 0.0, 0.0),  # red
    (0.0, 1.0, 0.0),  # green
    (0.0, 0.0, 1.0),  # blue
]

try:
    while True:
        for color in colors:
            tree.color = color
            time.sleep(1)
except KeyboardInterrupt:
    tree.off()
    tree.close()
