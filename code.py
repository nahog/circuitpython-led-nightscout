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
from adafruit_pixel_framebuf import PixelFramebuffer
from adafruit_datetime import datetime

NIGHTSCOUT_URL="https://<<NIGHTSCOUT_URL>>/api/v1/entries.json?count=1&token=<<NIGHTSCOUT_API_TOKEN>>"

URGENT_LOW=3
LOW=4
HIGH=9
URGENT_HIGH=12

OFF_HOURS_BEGIN=0
OFF_HOURS_END=8
TZ_OFFSET=1

OFF_COLOR=0x000000
BACKGROUND_COLOR=0x000000
FOREGROUND_COLOR=0x222222
URGENT_OUT_OF_RANGE_COLOR=0x00FF00
OUT_OF_RANGE_COLOR=0xFFFF00
IN_RANGE_COLOR=0xFF0000

UPDATE_CYCLES=16
TIME_BETWEEN_CYCLES_IN_SEC=2

disable_screen = False

pixel_pin = board.GP6
pixel_width = 16
pixel_height = 10

pixels = neopixel.NeoPixel(
    pixel_pin,
    pixel_width * pixel_height,
    brightness=0.1,
    auto_write=False,
)

pixel_framebuf = PixelFramebuffer(
    pixels,
    16,
    10,
    rotation=2,
    alternating=False,
)

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

def update_screen(buffer):
    if disable_screen:
        buffer.fill(OFF_COLOR)
        buffer.display()
    else:
        buffer.display()

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

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())
ntp = adafruit_ntp.NTP(pool, tz_offset=TZ_OFFSET)
rtc.RTC().datetime = ntp.datetime

counter = UPDATE_CYCLES
while True:
    counter += 1
    if counter == UPDATE_CYCLES + 1:
        gc.collect()
        current_datetime = datetime.now()
        if current_datetime.hour >= OFF_HOURS_BEGIN and current_datetime.hour <= OFF_HOURS_END:
            disable_screen = True
            print(f"night time {current_datetime.hour}:{current_datetime.minute}:{current_datetime.second}, no updates")
        else:
            disable_screen = False
            print(f"getting sgv data on {current_datetime.hour}:{current_datetime.minute}:{current_datetime.second}...")
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
