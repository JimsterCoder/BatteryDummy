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

# samples commands for testing
# 
# ./cansend can1 010#cafeface
# sudo /sbin/ip link set can1 up type can bitrate 500000
# ./candump can0



import os
import logging
import can
import time
import queue
#import pickle
from threading import Thread
#from gpiozero import LED #, OutputDevice



PID_UPDATE_BLOCK_REQUEST  = 0x720 #from inverter
PID_UPDATE_BLOCK_RESPONSE = 0x758 #from battery

msg_data = [[0x02, 0x21, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
			[0x02, 0x21, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]]



#F#0#0x4D8#8#F#F#0x00 0x42 0x00 0x00 0x00 0x8B 0x02 0x00#5000ms##
#F#0#0x358#8#F#F#0x13 0x56 0x10 0xFE 0x00 0x00 0x00 0x00#1000ms##
#F#0#0x3D8#8#F#F#0x1A 0xB1 0x27 0x10 0xFF 0xFF 0xFF 0xFF#5000ms##
#F#0#0x158#8#F#F#0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00#5000ms##
#F#0#0x198#8#F#F#0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFF#5000ms##
#F#0#0x218#8#F#F#0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFF#5000ms##
#F#0#0x758#8#F#F#0x07 0x62 0x00 0x00 0x01 0x08 0x00 0x00#id0x720 10ms 1x bus0##
#F#0#0x558#8#F#F#0x16 0x18 0x06 0x04 0x00 0x62 0x01 0x02#id0x720 30ms 1x bus0##
#F#0#0x598#8#F#F#0x60 0x17 0x90 0x61 0xFF 0xFF 0xFF 0xFF#id0x720 30ms 1x bus0##
#F#0#0x5D8#8#F#F#0x00 0x4C 0x47 0x20 0x43 0x48 0x45 0x4D#id0x720 30ms 1x bus0##
#F#0#0x5D8#8#F#F#0x01 0x00 0x00 0x01 0x08 0x00 0x00 0x00#id0x720 35ms 1x bus0##
#F#0#0x618#8#F#F#0x00 0x52 0x45 0x53 0x55 0x31 0x30 0x48#id0x720 40ms 1x bus0##
#F#0#0x618#8#F#F#0x01 0x00 0x00 0x01 0x08 0x00 0x00 0x00#id0x720 45ms 1x bus0##
#F####F#F####
#




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
def read_can():

# initiallise byte array for all the group data
	group_data = bytearray()

	try:
		message = q.get(False)
	# if the q is empty an expection is raised
	except queue.Empty:
		#print("Empty")
		return group_data
	
	
#	c = '{0:f} {1:x} {2:x} '.format(message.timestamp, message.arbitration_id, message.dlc)
#	s=''
#	for i in range(message.dlc ):
#		s +=  '{0:x} '.format(message.data[i])
#	print(' {}'.format(c+s))

	
	for x in range(message.dlc):
		group_data.append(message.data[x])
		
	byte_str = format(message.arbitration_id,'03x') + ': '
	
	for x in range(len(group_data)):
		value = format(group_data[x],'02x')
		byte_str = byte_str + value + ' '
	logging.info(byte_str)
	print(byte_str)

	return group_data

#------------------------------------------------------------------------------
# MAIN
#------------------------------------------------------------------------------
#logging.basicConfig(filename='can.log',format='%(levelname)s:%(message)s', level=logging.WARN) # INFO-WARN
logging.basicConfig(filename='can.log',format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO)
logging.debug('Debug Message')
logging.info('Info Message')
logging.warning('Warning Message')

# Bring up can interface at 500kbps
print('Bring up can0 interface....')
logging.info('Bring up can0 interface....')
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

q = queue.Queue()
rx = Thread(target=can_rx_task) 
rx.start()

mstime0 = int(round(time.time() * 1000))

# Main loop
try:
	while True:

		# non blocking read
		data = read_can()

		mstime1 = int(round(time.time() * 1000))
		
		msdiff= mstime1 - mstime0
		if (msdiff > 2000):
			mstime0 = int(round(time.time() * 1000))
			print ("Send Message")

		time.sleep(0.010)

except KeyboardInterrupt:
	#Catch keyboard interrupt
	os.system("sudo /sbin/ip link set can0 down")
	print('\n\rKeyboard interrupt')
