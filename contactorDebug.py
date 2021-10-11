import os
#import logging
import can
import time
import queue
#import pickle
from threading import Thread
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
#from gpiozero import LED #, OutputDevice

#------------------------------------------------------------------------------
GPIO_LBC = 4
GPIO_POS_RELAY = 5
GPIO_NEG_RELAY = 6
GPIO.setup(GPIO_LBC, GPIO.OUT) 
GPIO.setup(GPIO_POS_RELAY, GPIO.OUT) 
GPIO.setup(GPIO_NEG_RELAY, GPIO.OUT) 
global ContactorsOpen

def Sequential():
    #Switch all off
    GPIO.output(GPIO_LBC, GPIO.HIGH)
    GPIO.output(GPIO_POS_RELAY, GPIO.HIGH)
    GPIO.output(GPIO_NEG_RELAY, GPIO.HIGH)
    print('All Relays off')
    time.sleep(5)
    GPIO.output(GPIO_LBC, GPIO.LOW)
    print('LBC Relay on, GPIO 4')
    time.sleep(5)



def OpenContactors():
	global ContactorsOpen
	GPIO.output(GPIO_NEG_RELAY, GPIO.HIGH)
	GPIO.output(GPIO_POS_RELAY, GPIO.HIGH)
	ContactorsOpen = True
	print('CONTACTORS OPEN.')

def CloseContactors():
	global ContactorsOpen
	print('CONTACTORS Closing.')
	GPIO.output(GPIO_NEG_RELAY, GPIO.LOW)
	time.sleep(5)
	GPIO.output(GPIO_POS_RELAY, GPIO.LOW)
	ContactorsOpen = False
	print('CONTACTORS CLOSED.')

    #-------------------------------------

# Trial. I want 

while True:
    CloseContactors()
    time.sleep(5)
    OpenContactors()