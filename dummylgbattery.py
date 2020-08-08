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

def byte_formater(data):
	"""This function takes a byte array and returns a dictionary object with 'int and 'str'."""
	i = int.from_bytes(data, byteorder='big', signed=False)
	s = ' '.join(format(b, '02x') for b in data)
	return{'int':i, 'str':s}

#def open_relays():
#	time.sleep(2)
#	#RELAY_POS.on() #TESTING
#	#RELAY_NEG.on() #TESTING
#	print('Relays open...battery isolated')

#def status_check(mode,value,critical,warning,msg):
#	if mode=='max':
#		# Check for warning state
#		if value >= critical:
#			# Critical! --> Shudown
#			Thread(target=open_relays).start #TESTING
#			print("STATUS CHECK: %s max CRITICAL" % msg)
#		elif value >= warning:
#			# Warning!
#			print("STATUS CHECK: %s max CRITICAL" % msg)
#		else:
#			print("\nSTATUS CHECK: %s max OK" % msg)
#	elif mode=='min':
#				# Check for warning state
#		if value <= critical:
#			# Critical! --> Shudown
#			Thread(target=open_relays).start #TESTING
#			print("STATUS CHECK: %s min CRITICAL" % msg)
#		elif value <= warning:
#			# Warning!
#			print("STATUS CHECK: %s min CRITICAL" % msg)
#		else:
#			print("\nSTATUS CHECK: %s min OK" % msg)
#	else:
#		print("ERROR: unknown mode '%s' for %s" % (mode, msg))

def can_rx_task():	# Receive thread
	while True:
		message = bus.recv()
		#if message.arbitration_id == PID_REPLY:
		q.put(message)	# Put message into queue

def request_data(group, frames):

#	# For testing without CAN board
#	#return test_data.test_group_data(group) #TESTING
#	
#	print('\nData group '+ format(group, '02x'))
#	logging.info('Request sent, expecting '+str(frames)+' frames')
#
# initiallise byte array for all the group data
	group_data = bytearray()
#
#	# Send request for data for the group
#	msg_data = [0x02, 0x21, group, 0x00, 0x00, 0x00, 0x00, 0x00]
#	msg = can.Message(arbitration_id=PID_REQUEST, data=msg_data, extended_id=False)
#	bus.send(msg)
#	time.sleep(sleep)

	# Wait for a reply / Wait until there is a message
	# Remove and return an item from the queue.
	# If queue is empty, wait until an item is available.
	message = q.get()

#	if message.arbitration_id == 0x7BB and message.data[0] == 0x10:
#		#print(' '.join(format(x, '02x') for x in message.data))
#		for x in range(1, 8):
#			group_data.append(message.data[x])
#		msg_data = [0x30, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
#		msg = can.Message(arbitration_id=PID_REQUEST, data=msg_data, extended_id=False)
#		bus.send(msg)
#		#print('ACK sent')
#
#	for _ in range(frames-1):
#		message = q.get()
#		#print(' '.join(format(x, '02x') for x in message.data))
#		# The first (index) byte is ignored, should probablly check it's in the right order
	
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
#		if x%7 != 6:
		byte_str = byte_str + value + ' '
#		else:
#			byte_str = byte_str + value + '\n'
	logging.info(byte_str)
    

	return group_data

q = queue.Queue()
rx = Thread(target=can_rx_task) #TESTING
rx.start() #TESTING

bat_stat = None

# Main loop
try:
	while True:

		data = request_data(GROUP_1, 6)
		
		#file_Name = "BatteryStatus.dat"
		#fileObject = open(file_Name, 'wb')
		#pickle.dump(bat_stat,fileObject)
		#fileObject.close()

		#exit() #TESTING
		#time.sleep(10)

except KeyboardInterrupt:
	#Catch keyboard interrupt
	os.system("sudo /sbin/ip link set can0 down")
	print('\n\rKeyboard interrupt')
