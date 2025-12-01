"""
Diagnostic test for the Pico RGB tree driver - run on the Pico REPL.

This script tries toggling the GPIO pins, showing a quick pattern, and optionally forcing bitbang mode.
"""

from tree_pico import RGBXmasTree
import time


def run(force_bitbang=False):
    tree = RGBXmasTree(pixels=25, data_pin=9, clock_pin=28, brightness=1.0, force_bitbang=force_bitbang, debug=True)
    try:
        print('Mode:', 'bitbang' if not tree._use_pio else 'PIO')
        # Pin check: floating/pull/drive detection
        tree.check_pin_drive()
        # Toggle pins to make sure wiring is good
        tree.test_pins(cycles=6, delay_ms=100)
        # Show test pattern
        tree.show_test_pattern()
        # Turn a single pixel white for 2s
        tree[0].color = (1.0, 1.0, 1.0)
        tree.value = tree.value
        time.sleep(2)
        tree.off()
    finally:
        tree.close()


if __name__ == '__main__':
    # Pass True to force bitbang if PIO fails
    run(force_bitbang=False)
