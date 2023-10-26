import gc
import os
import rtc
import ssl
import json
import math
import time
import wifi
import board
import neopixel
import socketpool
import microcontroller
import adafruit_ntp
import adafruit_requests
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_pixel_framebuf import PixelFramebuffer
from adafruit_datetime import datetime

### CONSTANTS

# NIGHTSCOUT CONFIG
NIGHTSCOUT_URL = "https://" + os.getenv("NIGHTSCOUT_DOMAIN") + "/api/v1/entries.json?count=1&token=" + os.getenv("NIGHTSCOUT_TOKEN")

# GLUCOSE VALUE THRESHOLDS
URGENT_LOW = 3
LOW = 4
HIGH = 9
URGENT_HIGH = 12

# OFF HOURS AND TIME CONFIG
OFF_HOURS_BEGIN = 0
OFF_HOURS_END = 8
TZ_OFFSET = 1

# COLOR / HEX VALUES IN GGRRBB
OFF_COLOR = 0x000000
BACKGROUND_COLOR = 0x000000
FOREGROUND_COLOR = 0x111111
URGENT_OUT_OF_RANGE_COLOR = 0x00FF00
OUT_OF_RANGE_COLOR = 0x49E909
IN_RANGE_COLOR = 0xFF0000

# REFRESH TIMERS / CYCLES
CYCLES_FOR_CLOCK_REFRESH = 1800
UPDATE_CYCLES = 16
TIME_BETWEEN_CYCLES_IN_SEC = 2

# RGB MATRIX DEFINITION
PIXEL_PIN = board.GP6
PIXEL_WIDTH = 16
PIXEL_HEIGHT = 10
PIXEL_ROTATION = 2
PIXEL_ALTERNATING = False
PIXEL_BRIGHTNESS = 0.1

### GLOBAL VARIABLES

# INTERFACE WITH THE LED MATRIX
pixels = neopixel.NeoPixel(
    PIXEL_PIN,
    PIXEL_WIDTH * PIXEL_HEIGHT,
    brightness = PIXEL_BRIGHTNESS,
    auto_write = False,
)

# IN MEMORY BUFFER TO STORE PIXELS
pixel_framebuf = PixelFramebuffer(
    pixels,
    PIXEL_WIDTH,
    PIXEL_HEIGHT,
    rotation = PIXEL_ROTATION,
    alternating = PIXEL_ALTERNATING,
)

# ON / OFF VARIABLE TO DISABLE THE SCREEN
disable_screen = False

### FUNCTIONS

# UPDATES SCREEN TAKING INITO ACCOUNT THE OFF HOURS / SWITCH VARIABLE
def update_screen(buffer):
    if disable_screen:
        buffer.fill(OFF_COLOR)
        buffer.display()
    else:
        buffer.display()

# MAP LED COLORS TO CONFIGURED GLUCOSE LIMITS
def calc_color(number):
    if number < URGENT_LOW:
        return URGENT_OUT_OF_RANGE_COLOR
    if number < LOW:
        return OUT_OF_RANGE_COLOR
    if number < HIGH:
        return IN_RANGE_COLOR
    if number < URGENT_HIGH:
        return OUT_OF_RANGE_COLOR
    return URGENT_OUT_OF_RANGE_COLOR

# PRINT A NUMBER IN THE BUFFER BETWEEN 0 AND 29
# IT USES DECIMALS FROM 0.0 to 19.9, AND ROUND NUMBERS FROM 20 TO 29
# PRINT NUMBERS USING STRINGS BUT CUSTOMIZE THE No 1 TO FILL ONE 
# EXTRA DIGIT ON A 16x10 LED MATRIX
def print_num(buffer, number):
    buffer.fill(BACKGROUND_COLOR)
    number_values = number.split(".");
    integer_number = number_values[0]
    number_as_int = int(integer_number);
    color = calc_color(number_as_int)
    decimal_number = 0
    if len(number_values) > 1:
        decimal_number = number_values[1]
    if number_as_int >= 20:
        buffer.text(str(integer_number), 3, 2, color)
        if number_as_int == 21:
            buffer.pixel(10, 8, BACKGROUND_COLOR)
            buffer.pixel(12, 8, BACKGROUND_COLOR)
        update_screen(buffer)
        return
    if number_as_int >= 10:
        buffer.pixel(0, 3, color)
        buffer.line(1, 2, 1, 8, color)
        integer_number = str(number_as_int - 10).split(".")[0];
    buffer.text(str(integer_number), 3, 2, color)
    if integer_number == "1":
        buffer.pixel(4, 8, BACKGROUND_COLOR)
        buffer.pixel(6, 8, BACKGROUND_COLOR)
    buffer.pixel(9, 8, color)
    buffer.text(str(decimal_number), 11, 2, color)
    buffer.text(str(decimal_number), 11, 2, color)
    if decimal_number == "1":
        buffer.pixel(12, 8, BACKGROUND_COLOR)
        buffer.pixel(14, 8, BACKGROUND_COLOR)
    update_screen(buffer)

# UPDATE THE INTERNAL CLOCK USING NTP (FROM THE INTERNET)
def update_date(pool):
    rtc.RTC().datetime = adafruit_ntp.NTP(pool, tz_offset=TZ_OFFSET).datetime

### MAIN METHOD / LOOP

try:
    pool = socketpool.SocketPool(wifi.radio)
    requests = adafruit_requests.Session(pool, ssl.create_default_context())

    refresh_time_counter = CYCLES_FOR_CLOCK_REFRESH
    counter = UPDATE_CYCLES
    while True:
        counter += 1
        refresh_time_counter += 1
        if refresh_time_counter == CYCLES_FOR_CLOCK_REFRESH + 1:
            old_datetime = datetime.now()
            update_date(pool)
            current_datetime = datetime.now()
            print(f"time updated from {old_datetime.hour}:{old_datetime.minute:02}:{old_datetime.second:02} to {current_datetime.hour}:{current_datetime.minute:02}:{current_datetime.second:02}")
            counter = 0
        if counter == UPDATE_CYCLES + 1:
            gc.collect()
            current_datetime = datetime.now()
            if current_datetime.hour >= OFF_HOURS_BEGIN and current_datetime.hour <= OFF_HOURS_END:
                disable_screen = True
                print(f"night time {current_datetime.hour}:{current_datetime.minute:02}:{current_datetime.second:02}, no updates")
            else:
                disable_screen = False
                print(f"getting sgv data on {current_datetime.hour}:{current_datetime.minute:02}:{current_datetime.second:02}...")
                response = requests.get(NIGHTSCOUT_URL)
                data = json.loads(response.text)
                response.close()
                sgv = round(data[0]["sgv"] / 18.0, 1)
                print(f"got {sgv}")
                print_num(buffer=pixel_framebuf, number=str(sgv))
                pixel_framebuf.line(0, 0, 15, 0, BACKGROUND_COLOR)
            counter = 0
        else:
            print(f"{counter}: waiting 2s")
            pixel_framebuf.line(0, 0, counter - 1, 0, FOREGROUND_COLOR)
        time.sleep(TIME_BETWEEN_CYCLES_IN_SEC)
        update_screen(pixel_framebuf)

    pixel_framebuf.fill(BACKGROUND_COLOR)
    update_screen(pixel_framebuf)
except Exception:
    microcontroller.reset()
