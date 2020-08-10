#!/usr/bin/python3
#
# This python3 program sends out requests to a Nisan Leaf BMS then outputs the reply to the stdout.
# For use with PiCAN boards on the Raspberry Pi
# http://skpang.co.uk/catalog/pican2-canbus-board-for-raspberry-pi-2-p-1475.html
#
# Make sure Python-CAN is installed first http://skpang.co.uk/blog/archives/1220
#
# http://www.mynissanleaf.com/viewtopic.php?f=44&t=11676&sid=9d8ebf1c2ac610a7e99deb79149f985c
#
# July 2018 Mark Hornby
#

# samples for testing
# 
# ./cansend can1 010#cafeface


import os
import logging
import can
import time
import queue
#import pickle
from threading import Thread
from gpiozero import LED #, OutputDevice
#import test_data
#from BatteryStatus import BatteryStatus

#logging.basicConfig(filename='can.log',format='%(levelname)s:%(message)s', level=logging.WARN) # INFO-WARN
logging.basicConfig(filename='can.log',format='%(asctime)s %(levelname)s:%(message)s', level=logging.DEBUG)
sleep = 0.1
logging.debug('Debug Message')
logging.info('Info Message')
logging.warning('Warning Message')

PID_UPDATE_BLOCK_REQUEST  = 0x720 #from inverter
PID_UPDATE_BLOCK_RESPONSE = 0x758 #from battery

GROUP_1 = 0x01 # 6 lines, precision SOC, Ah Capacity and perhaps battery State of Health %
GROUP_2 = 0x02 # 29 lines, 96 cell voltages.
GROUP_3 = 0x03 # 5 lines, Vmin and Vmax
GROUP_4 = 0x04 # 3 lines, 4 pack temperatures.
GROUP_5 = 0x05 # 11 lines, not sure what
GROUP_6 = 0x06 # 4 lines, status of the resistive cell balancing shunts.

CRIT_VOLT_MAX = 4.15
CRIT_VOLT_MIN = 3.00
CRIT_VOLT_DELTA = 1.00
CRIT_TEMP_MAX = 50
CRIT_TEMP_MIN = 2

WARN_VOLT_MAX = 4.1
WARN_VOLT_MIN = 3.3
WARN_VOLT_DELTA = 0.1
WARN_TEMP_MAX = 40
WARN_TEMP_MIN = 3

RELAY_POS = LED(4) # Turn on first 
RELAY_NEG = LED(26) # OFF is precharge ON is high voltage

# Bring up can interface at 500kbps
print('Bring up can0 interface....')
os.system("sudo /sbin/ip link set can0 up type can bitrate 500000")
time.sleep(0.1)
print('Ready')

try:
	#bus = can.interface.Bus('can0', bustype='virtual') #TESTING
	bus = can.interface.Bus(channel='can0', bustype='socketcan') #TESTING
	#bus.set_filters([{"can_id": PID_REPLY, "can_mask": 0x00}])
except OSError:
	print('Cannot find PiCAN board.')
	exit()

#------------------------------------------------------------------------------
def byte_formater(data):
	"""This function takes a byte array and returns a dictionary object with 'int and 'str'."""
	i = int.from_bytes(data, byteorder='big', signed=False)
	s = ' '.join(format(b, '02x') for b in data)
	return{'int':i, 'str':s}

#------------------------------------------------------------------------------
def can_rx_task():	# Receive thread
	while True:
		message = bus.recv()
		#if message.arbitration_id == PID_REPLY:
		q.put(message)	# Put message into queue

#------------------------------------------------------------------------------
def request_data(group, frames):

# initiallise byte array for all the group data
	group_data = bytearray()

	try:
		message = q.get(False)
	# if the q is empty an expection is raised
	except queue.Empty:
		#print("Empty")
		return group_data
	
	
	c = '{0:f} {1:x} {2:x} '.format(message.timestamp, message.arbitration_id, message.dlc)
	s=''
	for i in range(message.dlc ):
		s +=  '{0:x} '.format(message.data[i])
			
	print(' {}'.format(c+s))

	
	for x in range(1, message.dlc):
		group_data.append(message.data[x])

	byte_str = ""
	for x in range(len(group_data)):
		value = format(group_data[x],'02x')
		byte_str = byte_str + value + ' '
	logging.info(byte_str)
    

	return group_data

q = queue.Queue()
rx = Thread(target=can_rx_task) 
rx.start()

mstime0 = int(round(time.time() * 1000))

# Main loop
try:
	while True:

		data = request_data(GROUP_1, 6)

		mstime1 = int(round(time.time() * 1000))
		
		msdiff= mstime1 - mstime0
		if (msdiff > 2000):
			mstime0 = int(round(time.time() * 1000))
			print ("Send Message")

		time.sleep(0.100)

except KeyboardInterrupt:
	#Catch keyboard interrupt
	os.system("sudo /sbin/ip link set can0 down")
	print('\n\rKeyboard interrupt')
