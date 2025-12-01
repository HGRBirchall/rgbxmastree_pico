# Pico RGBTree Troubleshooting

If you've uploaded `tree_pico.py` to your Raspberry Pi Pico but the LED strip doesn't show lights, follow these steps to diagnose and fix the issue.

Hardware checks
--------------
1. Power supply
   - Ensure your LED strip has a sufficient power supply. APA102s typically expect 5V but many work with 3.3V; verify the LED type.
   - The Pico should not attempt to supply LED power from USB alone unless your LED strip is small; use a dedicated 5V supply if necessary.
2. Ground
   - Ensure the Pico GND and the LED strip GND share a common ground. Without a shared ground, the logic signals won't be interpreted correctly.
3. Data & Clock pins
   - Ensure Data (DI) goes to GP9 and Clock (CI) goes to GP28 (or the pins you configured). Swap if mistakenly reversed.
   - For APA102, the data path is directional. When unsure, reverse both wires and test (DI and CI pins may be swapped).
4. Check pin wiring and orientation
   - Check the solder joints and connectors for continuity.
   - If the strip has arrows printed on the PCB, make sure data flows in the correct direction.
5. Voltage levels
   - If your LED strip is 5V only, and you drive it from GP9/GP28 (3.3V outputs), logic levels may still be accepted by many APA102s, but if not, use a level shifter.

Software diagnostics
--------------------
1. Add debug
   - Make sure you create the tree driver with `debug=True` so the driver prints PIO vs bitbang mode:
     ```python
     tree = RGBXmasTree(pixels=25, data_pin=9, clock_pin=28, debug=True)
     ```
2. Use the diagnostic script `diag_test.py` on the Pico:
   - Upload `tree_pico.py` and `diag_test.py` to Pico and run `diag_test.py` from REPL. The script toggles pins and shows a quick pattern.
3. Force bit-bang
   - If PIO initialization fails silently but without errors, force bitbang to ensure PIO isn't the issue:
     ```python
     tree = RGBXmasTree(..., force_bitbang=True, debug=True)
     ```
4. Try low-level toggling
   - If using Thonny / REPL, toggle pins manually and observe strip behavior:
     ```python
     from machine import Pin
     clk = Pin(28, Pin.OUT); din = Pin(9, Pin.OUT)
     din.value(1); clk.value(1); clk.value(0)
     ```
   - Observe if LED module flickers. If nothing happens, you either have wiring or power issues.
5. Verify brightness
   - Ensure `tree.brightness` is not set to 0.0; the global 5-bit brightness controls whether LEDs are lit even if RGB channels are non-zero.

What to look for
----------------
- If pins toggle (use a scope or LED) and strip doesn't respond: wiring, power, or strip orientation issue.
- If debug indicates `PIO` mode but nothing happens, try `force_bitbang=True` to check whether PIO timing/logic is preventing signals.
- If the strip is half-bright or miscolored: R/G/B order mismatch (we use B,G,R order in bytes for APA102); you can reorder in `tree_pico` if needed.

Next steps
----------
If none of the above solves it, please provide:
- The exact LED strip type (APA102 / SK9822 / DotStar part number / LED variant)
- A clear description of connections (power supply voltage, pin numbers, and wiring)
- The output of running `diag_test.py` with `debug=True` (copy the printed logs from REPL)

I can then adjust the driver to try alternate byte orders, frame formats, or more robust timing settings.
