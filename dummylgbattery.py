#!/usr/bin/python3
#
# For use with PiCAN boards on the Raspberry Pi
# http://skpang.co.uk/catalog/pican2-canbus-board-for-raspberry-pi-2-p-1475.html
#
# Make sure Python-CAN is installed first http://skpang.co.uk/blog/archives/1220
#
# August/Sept 2020 James Stulen
#

# samples commands for testing
# 
# ./cansend can1 010#cafeface
# sudo /sbin/ip link set can1 up type can bitrate 500000
# ./candump can0

# message logging to file batterydummy.log in local directory

import os
#import logging
import can
import time
import queue
#import pickle
from threading import Thread
#from gpiozero import LED #, OutputDevice

PID_UPDATE_BLOCK_REQUEST  = 0x720 #from inverter
PID_UPDATE_BLOCK_RESPONSE = 0x758 #from battery

class cSendMsg:
	def __init__(self, id, msgdata, interval, time):
		self.id = id
		self.msgdata = msgdata
		self.interval = interval
		self.time = time
	
# get time in milliseconds
tnow = int(round(time.time() * 1000)) 

# LIST OF MESSAGES TO BE SENT AT SET INTERVALS
sendmsg = []

msg = cSendMsg( 0x358, [0x13, 0x56, 0x10, 0xFE, 0x00, 0xA2, 0x00, 0xA2], 1000, tnow)
sendmsg.append(msg)

msg = cSendMsg( 0x4D8, [0x00, 0x16, 0x00, 0x00, 0x00, 0xA1, 0x02, 0x00], 5000, tnow)
sendmsg.append(msg)

msg = cSendMsg( 0x3D8, [0x1A, 0xB1, 0x27, 0x10, 0xFF, 0xFF, 0xFF, 0xFF], 5000, tnow)
sendmsg.append(msg)

msg = cSendMsg( 0x158, [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], 5000, tnow)
sendmsg.append(msg)

msg = cSendMsg( 0x198, [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF], 5000, tnow)
sendmsg.append(msg)

msg = cSendMsg( 0x218, [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF], 5000, tnow)
sendmsg.append(msg)

# LIST OF MESSAGES TO SEND IN RESPONSE TO 0x720
rspmsg = []

msg = cSendMsg( 0x758, [0x07, 0x62, 0x00, 0x00, 0x01, 0x08, 0x00, 0x00], 10, 0)
rspmsg.append(msg)

msg = cSendMsg( 0x558, [0x16, 0x18, 0x06, 0x04, 0x00, 0x62, 0x01, 0x02], 10, 0)
rspmsg.append(msg)

msg = cSendMsg( 0x598, [0x60, 0x17, 0x90, 0x61, 0xFF, 0xFF, 0xFF, 0xFF], 10, 0)
rspmsg.append(msg)

msg = cSendMsg( 0x5D8, [0x00, 0x4C, 0x47, 0x20, 0x43, 0x48, 0x45, 0x4D], 10, 0)
#msg = cSendMsg( 0x5D8, [ord("M"), ord("O"), ord("N"), ord("K"), ord("E"), ord("Y"), 0, 0], 10, 0)
rspmsg.append(msg)
msg = cSendMsg( 0x5D8, [0x01, 0, 0, 0, 0, 0, 0, 0], 10, 0)
rspmsg.append(msg)

msg = cSendMsg( 0x618, [0x00, 0x52, 0x45, 0x53, 0x55, 0x31, 0x30, 0x48], 10, 0)
#msg = cSendMsg( 0x618, [ord("A"), ord("B"), ord("C"), ord("D"), ord("E"), ord("F"), ord("G"), ord("H")], 10, 0)
rspmsg.append(msg)
msg = cSendMsg( 0x618, [0x01, 0, 0, 0, 0, 0, 0, 0], 10, 0)
rspmsg.append(msg)

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
		return 0
	
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
	#logginginfo(byte_str)
	##print(byte_str)

	return message.arbitration_id

#------------------------------------------------------------------------------
# MAIN
#------------------------------------------------------------------------------
##loggingbasicConfig(filename='can.log',format='%(levelname)s:%(message)s', level=#loggingWARN) # INFO-WARN
#loggingbasicConfig(filename='batterydummy.log',format='%(asctime)s %(levelname)s:%(message)s', level=#loggingINFO)
#loggingdebug('Debug Message')
#logginginfo('Info Message')
#loggingwarning('Warning Message')

# Bring up can interface at 500kbps
print('Bring up can0 interface....')
#logginginfo('Bring up can0 interface....')
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


# Main loop
try:
	while True:
		timenow = int(round(time.time() * 1000))

		# non-blocking read, returns 0 if nothing read
		rx_id = read_can()
		
		if (rx_id != 0):
			#print ('Message Received ' + format(rx_id,' 02x'))
			if (rx_id == PID_UPDATE_BLOCK_REQUEST):
				print('Received 720')
				for x in range(len(rspmsg)):
					msg = can.Message(arbitration_id=rspmsg[x].id, data=rspmsg[x].msgdata, extended_id=False)
					bus.send(msg)
					##print ('Response Sent ' + format(x,' 02x') + format(rspmsg[x].id,' 02x'))
					# send for loop delay
					time.sleep(rspmsg[x].interval/1000) # interval is in milliseconds
				

		for x in range(len(sendmsg)):
			if (timenow - sendmsg[x].time > sendmsg[x].interval):
				sendmsg[x].time = int(round(time.time() * 1000))
				msg = can.Message(arbitration_id=sendmsg[x].id, data=sendmsg[x].msgdata, extended_id=False)
				bus.send(msg)
				##print ('Message Sent ' + format(x,' 02x') + format(sendmsg[x].id,' 02x'))
				# send for loop delay
				time.sleep(0.010)

		# main loop delay
		time.sleep(0.010)

except KeyboardInterrupt:
	#Catch keyboard interrupt
	os.system("sudo /sbin/ip link set can0 down")
	print('\n\rKeyboard interrupt')
	