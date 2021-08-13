#!/usr/bin/python3
#
# For use with PiCAN boards on the Raspberry Pi
# http://skpang.co.uk/catalog/pican2-canbus-board-for-raspberry-pi-2-p-1475.html
#
# Make sure Python-CAN is installed first http://skpang.co.uk/blog/archives/1220
#
# August 2021 James Stulen
# Holy Sh*t it's been a year since we started this thing!

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
PID_INVERTER_QUERY  = 0x4200 #from inverter

#------------------------------------------------------------------------------
class cSendMsg:
	def __init__(self, id, msgdata, interval, time):
		self.id = id
		self.msgdata = msgdata
		self.interval = interval
		self.time = time

#------------------------------------------------------------------------------
class cCanRead:
  def __init__(self, arbitration_id, byte0):
     self.arbitration_id = arbitration_id
     self.msg_type = msg_type

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
	# if the q is empty an exception is raised
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

	return cCanRead( message.arbitration_id, group_data[0] )

#------------------------------------------------------------------------------
def LoByte(value):
	lobyte = value%256
	return hex(lobyte)

def HiByte(value):
	hibyte = int(value/256)
	return hex(hibyte)

#------------------------------------------------------------------------------
# LIST OF MESSAGES TO SEND IN RESPONSE TO INVERTER QUERY 'ENSEMBILE INFORMATION' byte 0 = 0
# TSUN doc says LSB so we will put lo byte first in the 2 byte values
# this is opposite of the AOS/SMA and done this way because LSB was not checked
# on SavvyCAN Signals from the AOS/SMA

ensemblerspmsg = []

# 0x4210 Battery Info 
BatPileTotVolt = 300
BatPileCur = 50
SecLvlBMSTemp = 20
BatSOC = 51
BatSOH = 70

# 0x4210+0,  2x Bat total voltage * 10, 2x Bat Current * 10, 2x BMS temp *10 -100, 1x SOC, 1x SOH
msg = cSendMsg( 0x42100, [ LoByte( BatPileTotVolt *10 ), HiByte( BatPileTotVolt *10) , LoByte( BatPileCur *10 ), HiByte( BatPileCur *10 ), LoByte(-100 + SecLvlBMSTemp *10 ), HiByte( -100 + SecLvlBMSTemp *10), LoByte( BatSOC), LoByte( BatSOH) ], 10, 0)
ensemblerspmsg.append(msg)

# 0x4220 Charge Limits
ChargeCutoffVolt = 301
DischargeCutoffVolt = 293
MaxChargeCur = 20
MaxDischargeCur = 20

# 0x4220+0, 2x charge cuttff voltage * 10, 2x discharge cuttoff voltage * 10, max charge current *10 -3000, max discharge current *10 - 3000
msg = cSendMsg( 0x42200, [ LoByte( ChargeCutoffVolt*10 ), HiByte( ChargeCutoffVolt*10) , LoByte( DischargeCutoffVolt *10 ), HiByte( DischargeCutoffVolt *10 ), LoByte(-3000 + MaxChargeCur *10 ), HiByte( -3000 + MaxChargeCur *10), LoByte( -3000 + MaxDischargeCur *10), HiByte( -3000 + MaxDischargeCur *10) ], 10, 0)
ensemblerspmsg.append(msg)

# 0x4230 Cell Data
MaxSingleCellVolt = 1
MinSingleCellVolt = 0
MaxSingleCellNumber = 1
MinSingleCellNumber = 0

# 0x4230+0, 2x cell voltage * 1000, 2x cell number
msg = cSendMsg( 0x42300, [ LoByte( MaxSingleCellVolt *1000 ), HiByte( MaxSingleCellVolt *1000 ) , LoByte( MinSingleCellVolt *1000 ), HiByte( MinSingleCellVolt * 1000 ), LoByte( MaxSingleCellNumber ), HiByte(  MaxSingleCellNumber), LoByte( MinSingleCellNumber ), HiByte( MinSingleCellNumber) ], 10, 0)
ensemblerspmsg.append(msg)

# 0x4240 Cell Temperatures
MaxCellTemp = 50
MinCellTemp = 0
MaxCellTempNumber = 1
MinCellTempNumber = 0

# 0x4240+0, 2x cell temp *10 -100, 2x cell number 
msg = cSendMsg( 0x42200, [ LoByte( -100 + MaxCellTemp *10  ), HiByte( -100 + MaxCellTemp *10 ) , LoByte( -100 + MinCellTemp *10  ), HiByte( -100 + MinCellTemp *10  ), LoByte( MaxCellTempNumber ), HiByte( MaxCellTempNumber ), LoByte( MinCellTempNumber ), HiByte( MinCellTempNumber ) ], 10, 0)
ensemblerspmsg.append(msg)



# 0x4220 
# 0x4220+0, 
#msg = cSendMsg( 0x42200, [ LoByte(  ), HiByte( ) , LoByte(  ), HiByte(  ), LoByte( ), HiByte( ), LoByte( ), HiByte() ], 0, 0)
#ensemblerspmsg.append(msg)

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
		rx_data = read_can()
		
		print (rx_data)
		if (rx_data.arbitration_id != 0):
			#print ('Message Received ' + format(rx_id,' 02x'))
			if (rx_data.arbitration_id == PID_INVERTER_QUERY):
				print('Received 4200')
				#check first byte is 0 or 2
				if (rx_data.msg_type == 0):
					for x in range(len(ensemblerspmsg)):
						msg = can.Message(arbitration_id=ensemblerspmsg[x].id, data=ensemblerspmsg[x].msgdata, extended_id=True)
						bus.send(msg)
						##print ('Response Sent ' + format(x,' 02x') + format(rspmsg[x].id,' 02x'))
						# send for loop delay
						time.sleep(ensemblerspmsg[x].interval/1000) # interval is in milliseconds
				

		# for x in range(len(sendmsg)):
		# 	if (timenow - sendmsg[x].time > sendmsg[x].interval):
		# 		sendmsg[x].time = int(round(time.time() * 1000))
		# 		msg = can.Message(arbitration_id=sendmsg[x].id, data=sendmsg[x].msgdata, extended_id=False)
		# 		bus.send(msg)
		# 		##print ('Message Sent ' + format(x,' 02x') + format(sendmsg[x].id,' 02x'))
		# 		# send for loop delay
		# 		time.sleep(0.001)

		# main loop delay
		time.sleep(0.001)

except KeyboardInterrupt:
	#Catch keyboard interrupt
	os.system("sudo /sbin/ip link set can0 down")
	print('\n\rKeyboard interrupt')
	