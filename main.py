# Code by Thomas Schreck
# 
# This code is for connecting an Adafruit Trinket M0 to a thermistor
# and vibrating motor to detect sitting in a chair too long and vibrate
# the chair to make you get up. The times in the constants are approximations
# and aren't exact due to processing time between the 1 second control
# loop sleeps. I didn't take the time to test how long the difference
# is to clock time.
#
# Note that the expectation is that you start standing when turned on. The
# time and temperature change are based on testing indoors in a house at 
# 68-72 degrees F. If you use this in other settings, you may need to adjust
# how long and how much the temperature changes from sitting.
#
# Thermistor usage code copyright:
# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import adafruit_dotstar
import adafruit_thermistor
from digitalio import DigitalInOut, Direction

# Constants
MAX_READINGS = 100
READINGS_TRIM_THRESHOLD = MAX_READINGS + 30
SIT_TIME_THRESHOLD = 60 * 30 # About 30 minutes
STAND_TIME_REQUIREMENT = 60 * 3 # About 3 minutes
SAMPLES_TO_DETECT_SIT = 30
SAMPLES_TO_DETECT_STAND = 30

# Board specs
pin_thermistor = board.A1
pin_haptic = board.D1
resistor_thermistor = 10000
resistance = 10000
nominal_temp = 25
b_coefficient = 3950

# Components
led = adafruit_dotstar.DotStar(board.APA102_SCK, board.APA102_MOSI, 1)

thermistor = adafruit_thermistor.Thermistor(
        pin_thermistor, resistor_thermistor, resistance, nominal_temp, b_coefficient
    )
haptic = DigitalInOut(pin_haptic)
haptic.direction = Direction.OUTPUT
haptic.value = False

# Variables
readings = []
seated = False
standing_timer = STAND_TIME_REQUIREMENT + 1
seated_timer = 0
notify_timer = 0

# Set initial baseline by reading the starting temperature
baseline = thermistor.temperature
for x in range(MAX_READINGS):
    readings.append(baseline)

######################
# Functions
######################

def celsius_to_fahrenheit(celcius):
    return (celsius * 9 / 5) + 32
    
def test_stand():
    # If the temperature has gone down at least 2 degrees int eh past 70 seconds.
    return readings[-1] - readings[-SAMPLES_TO_DETECT_STAND] < -2 

def test_sit():
    # If the temperature has gone up at least 2 degrees in the past 30 seconds.
    return readings[-1] - readings[-SAMPLES_TO_DETECT_SIT] > 2

def should_notify():
    # If sitting too long, notify.
    if seated_timer > SIT_TIME_THRESHOLD:
        global notify_timer
        notify_timer += 1
        notify_timer = notify_timer % 10 # Every 10 seconds
        return notify_timer == 1
    # Not sitting too long so don't notify.
    return False


##################################
# Main body of code
##################################
led[0] = (0, 255, 0)

# print the temperature in C and F to the serial console every second
while True:
    celsius = thermistor.temperature
    readings.append(celsius)
    #fahrenheit = celsius_to_fahrenheit(celsius)
    print("{} *C\n{} *Seated\n".format(celsius, seated))
    print((seated_timer, standing_timer, notify_timer, readings[-SAMPLES_TO_DETECT_STAND], readings[-SAMPLES_TO_DETECT_SIT], readings[-1]))

    # Turn off the haptic vibrate if on
    if haptic.value:
        haptic.value = False
        
    if seated:
        seated_timer += 1
        
        if test_stand():
            # Stood up
            seated = False
            led[0] = (0, 255, 0)
            # Start with generally how long it took to detect
            standing_timer = SAMPLES_TO_DETECT_STAND
        else:
            # still seated
            if should_notify():
                led[0] = (255, 0, 0)
                haptic.value = True
    else:
        standing_timer += 1
        
        if test_sit():
            # Sat down
            seated = True
            if standing_timer > STAND_TIME_REQUIREMENT:
                # Start with generally how long it took to detect
                seated_timer = SAMPLES_TO_DETECT_SIT
                led[0] = (0, 0, 255)
            else:
                # Uh oh. Didn't stand long enough! Go back to notifying!
                led[0] = (255, 0, 0)
            standing_timer = 0
    
    # If readings gets too big, resize it down. Only do this when len is greater than the threshold.
    if len(readings) > READINGS_TRIM_THRESHOLD:
        readings = readings[-MAX_READINGS:]
    time.sleep(1)
