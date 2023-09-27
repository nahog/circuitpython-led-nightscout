# CircuitPython RBG LED Matrix 16x10 connected to Nightscout CGM

A project that uses CircuitPython and reads glucose values from Nigthscout and display them in an RGB LED matrix

## Current functionality

- Display the last SGV value from nighscout on the RGB LED Matrix
- Progress bar to show next update
- Show one digit precision for values between 0.0 and 19.9
- Customized "1" so it looks nice when 3 digits are shown
- Colorized value depending on configurable urgent, warning or in range values
- NTP sync to get time and turn off the screen during night hours

## Assumptions and TODOs

- The code always convert the glucose value to mmol/L (and assumes the value comes as mg/dL)
- The code does not handle errors for now
- Off hours cannot break over the day, they must start at a minimum at 0
- There are console messages than can be removed to optimize memory usage

## Includes

Configuration and dependencies from `adafruit-circuitpython-bundle-8.x-mpy-20230211` see https://github.com/adafruit/circuitpython

1. font5x8.bin
2. lib/adafruit_led_animation/*
3. lib/adafruit_datetime
4. lib/adafruit_framebuf
5. lib/adafruit_ntp
6. lib/adafruit_pixel_framebuf
7. lib/adafruit_requests
8. lib/neopixel

## Tested with

- Raspberry Pi Pico W see https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html 
- Waveshare 16x10 RGB LED HAT for Raspberry Pi Pico see https://www.waveshare.com/pico-rgb-led.htm

## What you need to change

- Set your wifi name/pass on the `settings.toml` file
- Set you nightscout url on `code.py` replacing the `<<NIGHTSCOUT_URL>>` section
- (Optional) If your nightscout requires a token for the api, on the `code.py` set the `<<NIGHTSCOUT_API_TOKEN>>` see https://nightscout.github.io/nightscout/security/ 