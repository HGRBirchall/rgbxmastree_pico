# RGBTree Pico driver — MicroPython (RP2040)

This folder contains a MicroPython-compatible driver `tree_pico.py` for APA102/DotStar LED strips attached to a Raspberry Pi Pico (RP2040), plus several Pico-compatible example programs.

This README supplements the original README to explain the Pico-specific steps and features: PIO/bitbang operation modes, default pins, and device safety.

Quick summary
- Default pins: Data = GP9, Clock = GP28. These are the defaults used by the examples.
- Supported protocol: APA102 / DotStar (separate data and clock lines). Not suitable for WS2812/NeoPixel strips (use a different driver).
- `tree_pico.py` uses PIO for fast SPI-like output where available and falls back to a software bit-bang if the PIO variant is not available or fails to initialize.
- Use `debug=True` when constructing the driver to print diagnostic messages. Use `force_bitbang=True` to force the software fallback for troubleshooting.

Getting started on the Pico
--------------------------
1. Copy files to your Pico (easiest with Thonny): upload `tree_pico.py` and any example (`examples/` folder) to the Pico filesystem.
	- Alternatively, use `mpremote`, `rshell`, or `ampy` to copy files:

```powershell
# Example with mpremote (Windows PowerShell)
mpremote cp pico_to_pHat\RGBTree\tree_pico.py :
mpremote cp pico_to_pHat\RGBTree\examples\combo.py :
```

2. Run examples using Thonny or your preferred MicroPython tool, or import the module from the REPL:

```python
from tree_pico import RGBXmasTree
tree = RGBXmasTree(pixels=25, data_pin=9, clock_pin=28)
tree.color = (1, 0, 0)  # whole-strip red
tree.value = tree.value  # force write to strip
```

MicroPython usage notes & diagnostics
------------------------------------
- Use `debug=True` to print whether the driver uses PIO or the bitbang fallback:

```python
tree = RGBXmasTree(pixels=25, data_pin=9, clock_pin=28, debug=True)
```

- If PIO fails at runtime, set `force_bitbang=True` to force the software fallback to verify wiring and strip compatibility:

```python
tree = RGBXmasTree(pixels=25, data_pin=9, clock_pin=28, force_bitbang=True, debug=True)
```

- To run the Pico diag tool and get pin-level checks, use the `diag_test.py` script (copy it to the Pico and run):

```python
import diag_test
diag_test.run(force_bitbang=False)  # try PIO first
diag_test.run(force_bitbang=True)   # force software bit-bang and re-run
```

The `diag_test` output includes:
- `Mode: PIO` or `Mode: bitbang` to show which path is used.
- `check_pin_drive` results: values for floating/pull/pulse tests for the clock and data pins.
- `bitbang write N bytes` when bitbang writes frames.

Hardware checklist
------------------
- Shared ground: Ensure the Pico ground and the LED strip ground are connected.
- Power: Use a suitable 5V supply for most APA102 strips; many APA102 accept 3.3V logic on the data pins but the power line for the LEDs needs 5V.
- Check wiring: Data -> GP9, Clock -> GP28 (or change pins with constructor args). Verify the strip orientation (arrows on strip show data direction).
- Level Shifter: If your APA102 requires 5V logic and the Pico's 3.3V is not accepted, use a 3.3V-to-5V TTL buffer that doesn't clamp lines when MCU pins are inputs.

Brightness & colours
--------------------
- The driver uses APA102 global brightness (5 bits). You can set `brightness` from `0.0` to `1.0` when creating the tree:

```python
tree = RGBXmasTree(pixels=25, brightness=0.6)
```

- You can set the full-strip color with a tuple in the form `(r, g, b)` where values are floats in `[0.0, 1.0]`:

```python
tree.color = (1.0, 0.0, 0.0)  # red
```

- Per-pixel control is available (index from `0` to `pixels-1`):

```python
tree[0].color = (0.0, 1.0, 0.0)
```

Examples
--------
These examples are Pico-compatible and are located under `pico_to_pHat/RGBTree/Originals/examples` and `pico_to_pHat/RGBTree/examples`:

- `rgb.py` — whole-tree RGB cycle. Use `tree.color = ...` and `time.sleep()` to cycle.
- `onebyone.py` — set each pixel one by one.
- `huecycle.py` — hue rotation across entire tree (no `colorzero` dependency: uses `hsv_to_rgb`).
- `randomsparkles.py` — random pixel sparkles across the strip.
- `combo.py` — cycles through the above patterns in sequence; you can tune durations at the top of the script.

Troubleshooting (brief)
----------------------
If the LEDs do not light or you see strange behavior:
- Check `diag_test.run()` output and review the `check_pin_drive` dictionary. This helps pinpoint whether pins are being driven or clamped by external hardware.
- Confirm a shared ground and sufficient power supply (5V) for the strip.
- If the clock line is stuck low when the strip is connected, disconnect the strip and run `diag_test.run()` again. If it is now free, the strip or level-shifter is pulling the line down.
- If PIO fails and bitbang works, use `force_bitbang=True` for reliable tests while debugging the PIO program.
- If you think the color order is wrong or the strip has a different RGB byte order, the driver supports editing the `tree_pico` implementation to change the per-pixel byte order (BGR vs RGB).

Further reading & files
----------------------
- Driver: `tree_pico.py` in this folder
- Diagnostics: `diag_test.py` (copy to Pico to run)
- Troubleshooting guide: `TROUBLESHOOTING.md` in this folder
- Examples: `Originals/examples` and `examples/`

If you're using the Raspberry Pi (Linux) host (not the Pico)
-----------------------------------------------------------
For Raspberry Pi host users, see the original `tree.py` (which is Linux/gpiozero based). Use the original host README or the `Originals` folder for the full Raspbian-based usage instructions.

Contact
-------
If you're still stuck, paste your `diag_test.run()` output along with your strip model (APA102 or part number), whether you're using a level shifter, and a short description of how the Pico is powered and wired. I can then help you further.

