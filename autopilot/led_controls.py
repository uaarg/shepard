from rpi_ws281x import PixelStrip, Color
from time import sleep

LED_COUNT = 8
LED_PIN = 18

def set_color(led_strip : PixelStrip, r : int, g : int, b : int, delay_s=0.05):
	"""Sets all leds to a single color"""
	for led in range(led_strip.numPixels()):
		led_strip.setPixelColor(led, Color(r, g, b))
		led_strip.show()
		sleep(delay_s)

def setup_leds() -> PixelStrip:
	led = PixelStrip(LED_COUNT, LED_PIN)
	led.begin()
	set_color(led, 255, 255, 255)
	return led
