# MicroPython APA102 (.DotStar) driver for Raspberry Pi Pico (RP2040)
# Implements an API compatible with the original tree.py
# - Uses PIO for SPI-like operation on arbitrary pins (clock pin = GP28, data pin = GP9)
# - Provides Pixel proxy objects and a RGBXmasTree class

# NOTE: This is designed to be run in MicroPython on an RP2040 (Raspberry Pi Pico).
# If running on CPython, import errors for 'rp2' will be handled with a fallback
# software bit-bang implementation that still should function on supported platforms.

try:
    import rp2
    PIO_AVAILABLE = True
except Exception:
    PIO_AVAILABLE = False

try:
    from machine import Pin
    from machine import mem32
except Exception:
    # if not running on MicroPython, define minimal mock classes so static analysis works
    Pin = None

import time


# Lightweight Color class to provide similar usage to colorzero.Color for convenience
class Color(tuple):
    def __new__(cls, r=0.0, g=None, b=None):
        if g is None and b is None:
            if isinstance(r, (tuple, list)):
                r, g, b = r
            else:
                raise ValueError("Provide either (r,g,b) or tuple/list")
        return super().__new__(cls, (float(r), float(g), float(b)))


class Pixel:
    def __init__(self, parent, index):
        self.parent = parent
        self.index = index

    @property
    def value(self):
        return self.parent.value[self.index]

    @value.setter
    def value(self, value):
        new_parent_value = list(self.parent.value)
        new_parent_value[self.index] = value
        self.parent.value = tuple(new_parent_value)

    @property
    def color(self):
        return Color(*self.value)

    @color.setter
    def color(self, c):
        r, g, b = c
        self.value = (r, g, b)

    def on(self):
        self.value = (1, 1, 1)

    def off(self):
        self.value = (0, 0, 0)


# PIO program for per-bit SPI with separate clock (sideset) and data (pins)
PIO_PGM_WITH_SIDSET = False
PIO_PGM_WITH_SET = False
if PIO_AVAILABLE:
    # Attempt to use sideset_count (modern MicroPython). If not supported, fall back
    # to an alternate PIO program using `set(pins, x)` for clock toggling.
    try:
        @rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, sideset_count=1, out_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=8)
        def _apa102_pio():
            """
            Contemporary PIO program that uses sideset for clock toggling.
            """
            label('bitloop')
            out(pins, 1)         .side(0)   # set data bit, clock low
            nop()                .side(1)   # clock high
            nop()                .side(0)   # clock low
            jmp('bitloop')                # repeat
        PIO_PGM_WITH_SIDSET = True
    except TypeError:
        # Fallback for older MicroPython versions that don't support sideset_count in decorator.
        PIO_AVAILABLE = True
        @rp2.asm_pio(out_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=8)
        def _apa102_pio_alt():
            """
            Fallback PIO program that writes data via OUT (out_base, data pin) and toggles
            the clock pin via SET (set_base). This requires providing `set_base` when creating
            the StateMachine.
            """
            label('bitloop')
            out(pins, 1)         # set data bit (out_base)
            set(pins, 1)         # set clock high (set_base)
            nop()
            set(pins, 0)         # set clock low (set_base)
            nop()
            jmp('bitloop')
            PIO_PGM_WITH_SET = True
        # end of PIO program selection


class RGBXmasTree:
    def __init__(self, pixels=25, brightness=0.5, data_pin=9, clock_pin=28, sm_id=0, pio_freq=2_000_000, force_bitbang=False, debug=False):
        self._pixels = int(pixels)
        self._value = [(0.0, 0.0, 0.0)] * self._pixels
        self._brightness = float(brightness)
        self._brightness_bits = int(self._brightness * 31) & 0x1F

        self.data_pin = int(data_pin)
        self.clock_pin = int(clock_pin)

        # Allow forcing bit-bang in case issues with PIO; show debug info if requested
        self._use_pio = PIO_AVAILABLE and not force_bitbang
        self._debug = bool(debug)
        self._sm = None
        self._sm_id = sm_id
        self._pio_freq = int(pio_freq)

        # Create Pixel proxies
        self._all = [Pixel(self, i) for i in range(self._pixels)]

        # Setup state machine or bitbang pins
        if self._use_pio:
            # Initialize SM with PIO program. Use the available PIO program variant
            try:
                if PIO_PGM_WITH_SIDSET:
                    self._sm = rp2.StateMachine(self._sm_id, _apa102_pio, freq=self._pio_freq, sideset_base=Pin(self.clock_pin), out_base=Pin(self.data_pin))
                elif PIO_PGM_WITH_SET:
                    self._sm = rp2.StateMachine(self._sm_id, _apa102_pio_alt, freq=self._pio_freq, set_base=Pin(self.clock_pin), out_base=Pin(self.data_pin))
                else:
                    # No PIO variant available
                    raise RuntimeError("No PIO program variant available")
                self._sm.active(1)
            except Exception as e:
                if self._debug:
                    print('PIO init failed, falling back to bitbang:', e)
                self._use_pio = False
                self._sm = None
        if self._debug:
            print('RGBXmasTree: pixels=%d, data_pin=%d, clock_pin=%d, pio=%s, sm_id=%s' % (self._pixels, self.data_pin, self.clock_pin, self._use_pio, self._sm_id))

        if not self._use_pio:
            # Use bitbang pins as fallback
            self._clk = Pin(self.clock_pin, Pin.OUT)
            self._din = Pin(self.data_pin, Pin.OUT)

        self.off()

    def __len__(self):
        return len(self._all)

    def __getitem__(self, index):
        return self._all[index]

    def __iter__(self):
        return iter(self._all)

    @property
    def color(self):
        average_r = sum(pixel.color[0] for pixel in self) / len(self)
        average_g = sum(pixel.color[1] for pixel in self) / len(self)
        average_b = sum(pixel.color[2] for pixel in self) / len(self)
        return Color(average_r, average_g, average_b)

    @color.setter
    def color(self, c):
        r, g, b = c
        self.value = ((r, g, b),) * len(self)

    @property
    def brightness(self):
        return self._brightness

    @brightness.setter
    def brightness(self, brightness):
        max_brightness = 31
        self._brightness_bits = int(brightness * max_brightness) & 0x1F
        self._brightness = brightness
        # force a refresh of current values to apply the brightness
        self.value = self.value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        # Expect iterable of (r,g,b) tuples with floats 0.0-1.0
        pixels = [tuple(map(float, p)) for p in value]
        if len(pixels) != self._pixels:
            raise ValueError("value must contain exactly {} pixels".format(self._pixels))

        # Build frame
        start_frame = bytearray([0x00, 0x00, 0x00, 0x00])
        brightness_byte = 0b11100000 | self._brightness_bits
        body = bytearray()
        for r, g, b in pixels:
            br = [int(255 * v) & 0xFF for v in (b, g, r)]  # Order: B G R
            body.extend(bytes([brightness_byte]))
            body.extend(bytes(br))

        # End frame based on pixel count: send enough clock cycles by sending 0x00 or 0xFF
        # Some APA102 implementations send 0's, some send ones. We'll use zeros (works in many cases),
        # plus a few extra 0x00 frames for safety.
        end_len = (self._pixels + 15) // 16
        end_frame = bytearray([0x00] * (end_len + 4))

        frame = start_frame + body + end_frame

        # Send bytes via PIO or bitbang
        if self._use_pio and self._sm:
            for b in frame:
                self._sm.put(int(b))
        else:
            # Bitbang fallback
            self._bitbang_write(frame)

        self._value = tuple(pixels)

    def _bitbang_write(self, data):
        # Basic software SPI - toggles clock & data pins using Pin and small delay.
        # Timing may be slower than PIO state machine but will work for many APA102 LED strips.
        for byte in data:
            for bit in range(7, -1, -1):  # MSB first
                bit_val = (byte >> bit) & 1
                self._din.value(bit_val)
                # Toggle clock high then low
                self._clk.value(1)
                # Short tiny delay - microsecond sleep
                time.sleep_us(1)
                self._clk.value(0)
                time.sleep_us(1)
        if self._debug:
            print('bitbang write %d bytes' % len(data))

    def test_pins(self, cycles=5, delay_ms=100):
        """Toggle clock and data lines to validate wiring. Use this to confirm pins are connected and toggling."""
        # If there's a PIO state machine active, stop it while testing pins
        sm_was_active = False
        if self._sm:
            try:
                sm_was_active = bool(self._sm.active())
                if sm_was_active:
                    self._sm.active(0)
            except Exception:
                sm_was_active = False

        if not hasattr(self, '_clk') or not hasattr(self, '_din'):
            # If using PIO, create temporary Pin objects for diagnostic toggles
            try:
                clk_pin = Pin(self.clock_pin, Pin.OUT)
                din_pin = Pin(self.data_pin, Pin.OUT)
            except Exception as e:
                print('test_pins: cannot obtain pins for diagnostic', e)
                return
        else:
            clk_pin = self._clk
            din_pin = self._din

        print('Toggling pins: clk=%d, din=%d' % (self.clock_pin, self.data_pin))
        for _ in range(cycles):
            din_pin.value(1)
            clk_pin.value(1)
            time.sleep_ms(delay_ms)
            clk_pin.value(0)
            din_pin.value(0)
            time.sleep_ms(delay_ms)

        # restart PIO state machine if it was active
        if sm_was_active and self._sm:
            try:
                self._sm.active(1)
            except Exception:
                pass

    def show_test_pattern(self):
        """Send a simple pattern (red, green, blue) to the start of the strip to verify mapping.
        This will write to the pixel buffer and flush it to the strip.
        """
        orig = self.value
        # Create a test pattern across first few pixels
        n = min(6, self._pixels)
        vals = list(self.value)
        for i in range(n):
            if i % 3 == 0:
                vals[i] = (1.0, 0.0, 0.0)
            elif i % 3 == 1:
                vals[i] = (0.0, 1.0, 0.0)
            else:
                vals[i] = (0.0, 0.0, 1.0)
        # Leave rest as black
        for i in range(n, self._pixels):
            vals[i] = (0.0, 0.0, 0.0)
        self.value = vals
        # Restore original values after short delay
        time.sleep_ms(1000)
        self.value = orig

    def check_pin_drive(self):
        """Run a check that toggles pin drive/pull state and reports observed values.
        Useful to detect if a pin is externally held low or high by wiring or level shifters.
        """
        try:
            clk_pin = Pin(self.clock_pin)
            din_pin = Pin(self.data_pin)
        except Exception as e:
            print('check_pin_drive: cannot create Pin:', e)
            return

        # Make sure PIO is not driving these pins
        sm_was_active = False
        if self._sm:
            try:
                sm_was_active = bool(self._sm.active())
                if sm_was_active:
                    self._sm.active(0)
            except Exception:
                sm_was_active = False

        results = {}
        # Read floating input: init as input without specifying pull (disables internal pull)
        try:
            clk_pin.init(Pin.IN)
            din_pin.init(Pin.IN)
        except TypeError:
            # Some firmwares require explicit None to disable pull
            try:
                clk_pin.init(Pin.IN, None)
                din_pin.init(Pin.IN, None)
            except Exception:
                pass
        results['clk_floating'] = clk_pin.value()
        results['din_floating'] = din_pin.value()

        # Test pull-up (if supported)
        try:
            clk_pin.init(Pin.IN, Pin.PULL_UP)
            din_pin.init(Pin.IN, Pin.PULL_UP)
        except Exception:
            # Some MicroPython builds might not support pull constants
            pass
        results['clk_pull_up'] = clk_pin.value()
        results['din_pull_up'] = din_pin.value()

        # Test pull-down (if supported)
        try:
            clk_pin.init(Pin.IN, Pin.PULL_DOWN)
            din_pin.init(Pin.IN, Pin.PULL_DOWN)
        except Exception:
            pass
        results['clk_pull_down'] = clk_pin.value()
        results['din_pull_down'] = din_pin.value()

        # Drive low then high and read back
        clk_pin.init(Pin.OUT)
        din_pin.init(Pin.OUT)
        clk_pin.value(0); din_pin.value(0)
        time.sleep_ms(20)
        results['clk_drive_low'] = clk_pin.value(); results['din_drive_low'] = din_pin.value()
        clk_pin.value(1); din_pin.value(1)
        time.sleep_ms(20)
        results['clk_drive_high'] = clk_pin.value(); results['din_drive_high'] = din_pin.value()

        # Restore PIO if it was active
        if sm_was_active and self._sm:
            try:
                self._sm.active(1)
            except Exception:
                pass

        print('check_pin_drive results:', results)

    def on(self):
        self.value = ((1, 1, 1),) * len(self)

    def off(self):
        self.value = ((0, 0, 0),) * len(self)

    def close(self):
        if self._sm:
            try:
                self._sm.active(0)
            except Exception:
                pass


# Example usage block for Pico (not run when imported)
if __name__ == '__main__':
    # The Pico often expects micropython/pico specific runtime; this block demonstrates usage.
    tree = RGBXmasTree(pixels=25, data_pin=9, clock_pin=28, brightness=0.5)
    # Clear then display a test color
    tree.off()
    time.sleep(0.1)
    tree[0].color = (1.0, 0.0, 0.0)  # first pixel red
    tree[1].color = (0.0, 1.0, 0.0)  # next green
    tree[2].color = (0.0, 0.0, 1.0)  # next blue
    # commit
    tree.value = tree.value
    time.sleep(5)
    tree.off()
    tree.close()
