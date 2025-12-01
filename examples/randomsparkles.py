"""
Random sparkles example updated to use `tree_pico` for Raspberry Pi Pico.

This version generates random colors using the standard library random module
and updates a random pixel with a short delay; it runs under MicroPython and
uses debug=True to help with diagnostics.
"""
from tree_pico import RGBXmasTree
import time
try:
    import random
except Exception:
    # Some MicroPython builds provide urandom; emulate a simple random
    import urandom as random

tree = RGBXmasTree(pixels=25, data_pin=9, clock_pin=28, debug=True)

def random_color():
    r = random.random()
    g = random.random()
    b = random.random()
    return (r, g, b)

try:
    while True:
        pixel = random.choice(tree)
        pixel.color = random_color()
        # commit the new values to the LEDs
        tree.value = tree.value
        # short delay so the effect is visible
        time.sleep(0.1)
except KeyboardInterrupt:
    tree.off()
    tree.close()
