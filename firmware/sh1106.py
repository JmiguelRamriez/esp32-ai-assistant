# Controlador estándar SH1106 para MicroPython
import time
import framebuf

# Constantes de registros
SET_CONTRAST        = const(0x81)
SET_NORM_INV        = const(0xa6)
SET_DISP            = const(0xae)
SET_SCAN_DIR        = const(0xc0)
SET_SEG_REMAP       = const(0xa0)
LOW_COLUMN_ADDRESS  = const(0x00)
HIGH_COLUMN_ADDRESS = const(0x10)
SET_PAGE_ADDRESS    = const(0xB0)

class SH1106:
    def __init__(self, width, height, external_vcc):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        # Inicializa el framebuffer
        self.framebuf = framebuf.FrameBuffer(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.poweron()
        self.init_display()

    def init_display(self):
        for cmd in (
            SET_DISP | 0x00, # off
            # timing and driving scheme
            0xd5, 0x80,
            0xa8, self.height - 1,
            0xd3, 0x00,
            0x40,
            0xad, 0x8b if self.external_vcc else 0x8b,
            0xa1,
            0xc8,
            0xda, 0x12,
            0x81, 0xff,
            0xd9, 0x1f if self.external_vcc else 0x22,
            0xdb, 0x40,
            0x20, 0x00,
            SET_NORM_INV,
            SET_DISP | 0x01): # on
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def poweroff(self):
        self.write_cmd(SET_DISP | 0x00)

    def poweron(self):
        self.write_cmd(SET_DISP | 0x01)

    def contrast(self, contrast):
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert):
        self.write_cmd(SET_NORM_INV | (invert & 1))

    def show(self):
        for page in range(self.height // 8):
            self.write_cmd(SET_PAGE_ADDRESS | page)
            self.write_cmd(LOW_COLUMN_ADDRESS | 2)
            self.write_cmd(HIGH_COLUMN_ADDRESS | 0)
            self.write_data(self.buffer[
                self.width * page:self.width * page + self.width
            ])

    def fill(self, col):
        self.framebuf.fill(col)

    def pixel(self, x, y, col):
        self.framebuf.pixel(x, y, col)

    def scroll(self, dx, dy):
        self.framebuf.scroll(dx, dy)

    def text(self, string, x, y, col=1):
        self.framebuf.text(string, x, y, col)
        
    def hline(self, x, y, w, col):
        self.framebuf.hline(x, y, w, col)

    def vline(self, x, y, h, col):
        self.framebuf.vline(x, y, h, col)

    def line(self, x1, y1, x2, y2, col):
        self.framebuf.line(x1, y1, x2, y2, col)

    def rect(self, x, y, w, h, col):
        self.framebuf.rect(x, y, w, h, col)

    def fill_rect(self, x, y, w, h, col):
        self.framebuf.fill_rect(x, y, w, h, col)

    def blit(self, fbuf, x, y):
        self.framebuf.blit(fbuf, x, y)


class SH1106_I2C(SH1106):
    def __init__(self, width, height, i2c, res=None, addr=0x3c, external_vcc=False):
        self.i2c = i2c
        self.addr = addr
        self.res = res
        if res is not None:
            res.init(res.OUT, value=1)
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd):
        self.i2c.writeto(self.addr, bytearray([0x80, cmd]))

    def write_data(self, buf):
        self.i2c.writevto(self.addr, (b'\x40', buf))