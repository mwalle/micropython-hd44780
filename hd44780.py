from micropython import const
import utime

_C_CLEAR_DISPLAY = const(0x01)
_C_RETURN_HOME = const(0x02)
_C_ENTRY_MODE_SET = const(0x04)
_F_EM_DISP_SHIFT = const(0x01)
_F_EM_INCREMENT = const(0x02)
_F_EM_DECREMENT = const(0x00)
_C_DISPLAY_CONTROL = const(0x08)
_F_DC_CHARACTER = const(0x01)
_F_DC_CURSOR = const(0x02)
_F_DC_DISPLAY = const(0x04)
_C_SHIFT = const(0x10)
_F_MOVE_CURSOR = const(0x00)
_F_SHIFT_DISPLAY = const(0x80)
_F_LEFT = const(0x00)
_F_RIGHT = const(0x40)
_C_FUNCTION_SET = const(0x20)
_F_5_8_DOTS = const(0x00)
_F_5_10_DOTS = const(0x04)
_F_1_LINE = const(0x00)
_F_2_LINES = const(0x08)
_F_4_BIT = const(0x00)
_F_8_BIT = const(0x10)
_C_SET_CGRAM_ADDR = const(0x40)
_C_SET_DDRAM_ADDR = const(0x80)

_PCF8574_RS = const(0x01)
_PCF8574_RW = const(0x02)
_PCF8574_E = const(0x04)
_PCF8574_BL_EN = const(0x08)

class HD44780(object):
    def __init__(self, i2c, i2c_address=0x27, cols=16, rows=2):
        self.i2c = i2c
        self.i2c_address = i2c_address
        self.cols = cols
        self.rows = rows
        self._backlight = True
        self._display_on = True
        self._cursor_on = False
        self.initialize()

    def _i2c_write(self, data):
        if self._backlight:
            data |= _PCF8574_BL_EN

        self.i2c.writeto(self.i2c_address, bytes([data]))

    def _write_8bit(self, data, is_read=False, is_data=False):
        high_nibble = data & 0xf0
        low_nibble = (data & 0xf) << 4

        ctrl = 0
        if is_read:
            ctrl |= _PCF8574_RW
        if is_data:
            ctrl |= _PCF8574_RS

        # setup control signals
        self._i2c_write(ctrl)
        # pulse enable (high nibble)
        self._i2c_write(ctrl | high_nibble | _PCF8574_E)
        self._i2c_write(ctrl | high_nibble)
        # pulse enable (low nibble)
        self._i2c_write(ctrl | low_nibble | _PCF8574_E)
        self._i2c_write(ctrl | low_nibble)

    def _write_cmd(self, data):
        return self._write_8bit(data)

    def _write_data(self, data):
        return self._write_8bit(data, is_data=True)

    def _write_nibble(self, data):
        nibble = data & 0xf0

        # setup control signals
        self._i2c_write(0)
        # pulse enable
        self._i2c_write(nibble | _PCF8574_E)
        self._i2c_write(nibble)

    @property
    def backlight(self):
        return self._backlight

    @backlight.setter
    def backlight(self, value):
        self._backlight = bool(value)
        self._i2c_write(0)

    def initialize(self):
        self._write_nibble(_C_FUNCTION_SET | _F_8_BIT)
        utime.sleep_ms(5)
        self._write_nibble(_C_FUNCTION_SET | _F_8_BIT)
        utime.sleep_ms(1)
        self._write_nibble(_C_FUNCTION_SET | _F_8_BIT)
        self._write_nibble(_C_FUNCTION_SET | _F_4_BIT)

        # we are now in 4 bit mode
        if (self.rows > 1):
            self._write_cmd(_C_FUNCTION_SET | _F_4_BIT | _F_2_LINES | _F_5_8_DOTS)
        else:
            self._write_cmd(_C_FUNCTION_SET | _F_4_BIT | _F_5_8_DOTS)

        self.clear()
        self._update_display_control()
        self._write_cmd(_C_ENTRY_MODE_SET | _F_EM_INCREMENT)

    def _update_display_control(self):
        cmd = _C_DISPLAY_CONTROL
        if self._display_on:
            cmd |= _F_DC_DISPLAY
        if self._cursor_on:
            cmd |= _F_DC_CURSOR            
        self._write_cmd(cmd)

    def write(self, text):
        for b in text:
            self._write_data(ord(b))

    def home(self):
        self._write_cmd(_C_RETURN_HOME)
        # according to the datasheet this takes 1.52ms
        utime.sleep_ms(2)

    def clear(self):
        self._write_cmd(_C_CLEAR_DISPLAY)

    def set_cursor(self, col, row):
        col = min(col, self.cols - 1)
        row = min(row, self.rows - 1)

        # this should be true for most 2x16 and 4x20 displays
        if row == 1 or row == 3:
            col += 0x40
        if row >= 2:
            col += 0x14

        self._write_cmd(_C_SET_DDRAM_ADDR | col & 0x7f)

    def cursor_on(self):
        self._cursor_on = True
        self._update_display_control()

    def cursor_off(self):
        self._cursor_on = False
        self._update_display_control()

from machine import Pin, I2C
import random
i = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
h = HD44780(i, cols=20, rows=4)
h.backlight = True
h.clear()
h.home()
while True:
    h.write(random.choice("ABCDEFGHIJKLMNOPQRSTUVXYZ"))