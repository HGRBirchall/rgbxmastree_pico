"""
Hue cycle example updated to use `tree_pico` for Raspberry Pi Pico.

This example performs a slow hue rotation across the whole tree. It uses a simple
HSV-to-RGB conversion to run on MicroPython where colorzero may not be available.
"""
from tree_pico import RGBXmasTree
import time
import math


def hsv_to_rgb(h, s, v):
    # h in range [0,1], s and v in [0,1]
    i = int(h * 6.0)  # sector 0..5
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i = i % 6
    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    else:
        r, g, b = v, p, q
    return (r, g, b)


if __name__ == '__main__':
    # Default Pico pins: data=GP9, clock=GP28; set debug=True for diagnostics
    tree = RGBXmasTree(pixels=25, data_pin=9, clock_pin=28, debug=True)
    try:
        hue = 0.0
        while True:
            c = hsv_to_rgb(hue % 1.0, 1.0, 0.5)
            tree.color = c
            hue += 0.0025  # small increment for smooth rotation
            time.sleep(0.05)
    except KeyboardInterrupt:
        tree.off()
        tree.close()
