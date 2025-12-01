"""
combo.py — combine multiple example patterns into one rotating sequence

Modes included:
- huecycle: smooth hue rotation of entire tree.
- onebyone: step through pixels one by one in primary colors.
- randomsparkles: random pixels light up with random colors.
- rgb: whole-tree static color cycle.

This script uses the `tree_pico` driver for RP2040 (GP9 data, GP28 clock) and
supports `force_bitbang` for PIO troubleshooting and `debug` to print diagnostic
output to the REPL.
"""

from tree_pico import RGBXmasTree
import time
import math
try:
    import random
except Exception:
    # MicroPython may have urandom; if not, provide a fallback
    try:
        import urandom as random
    except Exception:
        random = None


def hsv_to_rgb(h, s, v):
    i = int(h * 6.0)
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


def hue_cycle(tree, duration=10.0, step_delay=0.05):
    start = time.time()
    hue = 0.0
    while time.time() - start < duration:
        c = hsv_to_rgb(hue % 1.0, 1.0, 0.6)
        tree.color = c
        hue += 0.0025
        time.sleep(step_delay)


def one_by_one(tree, duration=10.0, colors=None, delay=0.05):
    if colors is None:
        colors = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)]
    start = time.time()
    while time.time() - start < duration:
        for color in colors:
            for pixel in tree:
                pixel.color = color
                tree.value = tree.value
                time.sleep(delay)
                if time.time() - start >= duration:
                    break
            if time.time() - start >= duration:
                break


def random_sparkles(tree, duration=10.0, delay=0.1):
    # random module: fallback if not present
    rmod = random
    if rmod is None:
        # create a simple linear congruential generator fallback
        class LCG:
            def __init__(self, seed=1):
                self.x = seed
            def rand(self):
                self.x = (1103515245 * self.x + 12345) & 0x7FFFFFFF
                return self.x
            def randint(self, a, b):
                r = self.rand()
                return a + (r % (b - a + 1))
            def random(self):
                return (self.rand() & 0x7FFFFFFF) / 0x7FFFFFFF
        rmod = LCG(seed=12345)

    start = time.time()
    while time.time() - start < duration:
        idx = rmod.randint(0, len(tree) - 1)
        color = (rmod.random(), rmod.random(), rmod.random())
        tree[idx].color = color
        tree.value = tree.value
        time.sleep(delay)


def rgb_static(tree, duration=10.0):
    colors = [(1.0,0.0,0.0),(0.0,1.0,0.0),(0.0,0.0,1.0)]
    start = time.time()
    i = 0
    while time.time() - start < duration:
        tree.color = colors[i % len(colors)]
        i += 1
        time.sleep(1.0)


def run_all(tree, cycle_durations=None):
    if cycle_durations is None:
        # (hue, onebyone, random, rgb)
        cycle_durations = (20.0, 15.0, 15.0, 12.0)
    while True:
        hue_cycle(tree, duration=cycle_durations[0])
        one_by_one(tree, duration=cycle_durations[1])
        random_sparkles(tree, duration=cycle_durations[2])
        rgb_static(tree, duration=cycle_durations[3])


if __name__ == '__main__':
    # On Pico default to pins: data=GP9, clock=GP28
    # Quick configuration variables - change as needed
    FORCE_BITBANG = False
    DEBUG = True
    PIXELS = 25
    DATA_PIN = 9
    CLOCK_PIN = 28
    BRIGHTNESS = 0.6

    tree = RGBXmasTree(pixels=PIXELS, data_pin=DATA_PIN, clock_pin=CLOCK_PIN, brightness=BRIGHTNESS, force_bitbang=FORCE_BITBANG, debug=DEBUG)
    try:
        run_all(tree)
    except KeyboardInterrupt:
        tree.off()
        tree.close()
