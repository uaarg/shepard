from time import sleep

try:
    from rpi_ws281x import PixelStrip, Color
    HAS_RPI_WS281X = True
except ImportError:
    print("WARN: Failed to import rpi_ws281x, disabling related features")
    HAS_RPI_WS281X = False

    # stubs for typechecking
    class Color:
        def __init__(self, r: int, g: int, b: int):
            raise NotImplementedError()

    class PixelStrip:
        def __init__(self, led_count: int, led_pin: int):
            raise NotImplementedError()

        def numPixels(self) -> int:
            raise NotImplementedError()

        def setPixelColor(self, led: int, color: Color):
            raise NotImplementedError()

        def show(self):
            raise NotImplementedError()

        def begin(self):
            raise NotImplementedError()


LED_COUNT = 24
LED_PIN = 18


def set_color(led_strip: PixelStrip, r: int, g: int, b: int, delay_s=0.05):
    """Sets all leds to a single color"""
    if not led_strip:
        return

    for led in range(led_strip.numPixels()):
        led_strip.setPixelColor(led, Color(r, g, b))
        led_strip.show()
        sleep(delay_s)


def setup_leds() -> PixelStrip:
    if not HAS_RPI_WS281X:
        return None

    try:
        led = PixelStrip(LED_COUNT, LED_PIN)
        led.begin()
        set_color(led, 255, 255, 255)
        return led
    except RuntimeError as err:
        print("WARN: Found error %r while initializing the LED strip" % err)
        return None
