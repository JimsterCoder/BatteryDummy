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

#Niall testing git abilities. I cloned the git to get it from github onto our Pi3. I'm now going to attempt to merge it back into github with this mod.

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
PID_INVERTER_QUERY  = 0x4200 #from inverter
PID_SLEEP_AWAKE_COMMAND = 0x8201 #from inverter, sent to battery 1
PID_SLEEP_AWAKE_COMMAND_Req_Sleep = 0x55
PID_SLEEP_AWAKE_COMMAND_Quit_sleep = 0xAA

BASIC_STATUS_SLEEP = 0
BASIC_STATUS_CHARGE = 1
BASIC_STATUS_DISCHARGE = 2
BASIC_STATUS_IDLE = 3
# initialize BasicStatus
global BasicStatus
BasicStatus = BASIC_STATUS_IDLE

#------------------------------------------------------------------------------
GPIO_POS_RELAY = 5
GPIO_NEG_RELAY = 6
GPIO.setup(GPIO_POS_RELAY, GPIO.OUT) 
GPIO.setup(GPIO_NEG_RELAY, GPIO.OUT) 
global ContactorsOpen

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
	time.sleep(2)
	GPIO.output(GPIO_POS_RELAY, GPIO.LOW)
	ContactorsOpen = False
	print('CONTACTORS CLOSED.')

#------------------------------------------------------------------------------
class cSendMsg:
	def __init__(self, id, msgdata, interval, time):
		self.id = id
		self.msgdata = msgdata
		self.interval = interval
		self.time = time

#------------------------------------------------------------------------------
class cCanRead:
  def __init__(self, msg_id, msg_type):
     self.msg_id = msg_id
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
		return cCanRead(0,0)
		
	for x in range(message.dlc):
		group_data.append(message.data[x])
		
	byte_str = format(message.arbitration_id,'03x') + ': '
	
	for x in range(len(group_data)):
		value = format(group_data[x],'02x')
		byte_str = byte_str + value + ' '

	return cCanRead( message.arbitration_id, group_data[0] )

#------------------------------------------------------------------------------
def LoByte(value):
	lobyte = value%256
	return int(lobyte)

def HiByte(value):
	hibyte = int(value/256)
	return int(hibyte)

#------------------------------------------------------------------------------
# LIST OF MESSAGES TO SEND IN RESPONSE TO INVERTER QUERY 'ENSEMBILE INFORMATION' byte 0 = 0
# TSUN doc says LSB so we will put lo byte first in the 2 byte values
# this is opposite of the AOS/SMA and done this way because LSB was not checked
# on SavvyCAN Signals from the AOS/SMA

ensemblerspmsg = []
sysinfomsg = []

# Battery Info 
BatPileTotVolt = 371
BatPileCur = 0
SecLvlBMSTemp = 15
BatSOC = 75
BatSOH = 60

# 0x421+1
msg = cSendMsg( 0x4211, [ LoByte( BatPileTotVolt *10 ), HiByte( BatPileTotVolt *10) , LoByte((3000 + BatPileCur) *10 ), HiByte((3000 + BatPileCur) *10 ), LoByte((100 + SecLvlBMSTemp) *10 ), HiByte((100 + SecLvlBMSTemp) *10),  int(BatSOC),  int(BatSOH) ], 10, 0)
ensemblerspmsg.append(msg)

# Charge Limits
ChargeCutoffVolt = 385
DischargeCutoffVolt = 360
MaxChargeCur = 2.5
MaxDischargeCur = -5.25 #Max we should do through the 10A socket it is currently wired into (2000W @380V)

# 0x422+1 
msg = cSendMsg( 0x4221, [ LoByte( ChargeCutoffVolt*10 ), HiByte( ChargeCutoffVolt*10) , LoByte( DischargeCutoffVolt *10 ), HiByte( DischargeCutoffVolt *10 ), LoByte((+3000 + MaxChargeCur) *10 ), HiByte((+3000 + MaxChargeCur) *10), LoByte((+3000 + MaxDischargeCur) *10), HiByte((+3000 + MaxDischargeCur) *10) ], 10, 0)
ensemblerspmsg.append(msg)

# Cell Data
MaxSingleCellVolt = 3.980
MinSingleCellVolt = 3.978
MaxSingleCellNumber = 1
MinSingleCellNumber = 2

# 0x423+1
msg = cSendMsg( 0x4231, [ LoByte( MaxSingleCellVolt *1000 ), HiByte( MaxSingleCellVolt *1000 ) , LoByte( MinSingleCellVolt *1000 ), HiByte( MinSingleCellVolt * 1000 ), LoByte( MaxSingleCellNumber ), HiByte(  MaxSingleCellNumber), LoByte( MinSingleCellNumber ), HiByte( MinSingleCellNumber) ], 10, 0)
ensemblerspmsg.append(msg)

# Cell Temperatures
MaxCellTemp = 16
MinCellTemp = 14
MaxCellTempNumber = 3
MinCellTempNumber = 4

# 0x424+1
msg = cSendMsg( 0x4241, [ LoByte((+100 + MaxCellTemp) *10  ), HiByte((+100 + MaxCellTemp) *10 ) , LoByte((+100 + MinCellTemp) *10  ), HiByte((+100 + MinCellTemp) *10  ), LoByte( MaxCellTempNumber ), HiByte( MaxCellTempNumber ), LoByte( MinCellTempNumber ), HiByte( MinCellTempNumber ) ], 10, 0)
ensemblerspmsg.append(msg)

# Status,Error,Alarm,Protection
#BasicStatus = initilzied above and modified by PID_SLEEP_AWAKE_COMMAND message
CyclePeriod = 0 #WTF is this?
Error = 0
Alarm = 0
Protection = 0

# 0x425+1
msg = cSendMsg( 0x4251, [  BasicStatus, LoByte( CyclePeriod), HiByte( CyclePeriod ) , Error , LoByte( Alarm ), HiByte( Alarm ), LoByte( Protection ), HiByte( Protection ) ], 10, 0)
ensemblerspmsg.append(msg)

# Module Volts
ModuleMaxVolt = 2 * MaxSingleCellVolt
ModuleMinVolt = 2 * MinSingleCellVolt
ModuleMaxVoltNumber = 1
ModuleMinVoltNumber = 2 
# 0x426+1
msg = cSendMsg( 0x4261, [ LoByte( ModuleMaxVolt *1000 ), HiByte( ModuleMaxVolt *1000 ) , LoByte( ModuleMinVolt *1000 ), HiByte( ModuleMinVolt *1000 ), LoByte( ModuleMaxVoltNumber ), HiByte( ModuleMaxVoltNumber ), LoByte( ModuleMinVoltNumber ), HiByte( ModuleMinVoltNumber ) ], 10, 0)
ensemblerspmsg.append(msg)

# Module Temps 
ModuleMaxTemp = 16
ModuleMinTemp = 14
ModuleMaxTempNumber = 3
ModuleMinTempNumber = 4
# 0x427+1
msg = cSendMsg( 0x4271, [ LoByte((+100 + ModuleMaxTemp) *10  ), HiByte((+100 + ModuleMaxTemp) *10 ) , LoByte((+100 + ModuleMinTemp) *10  ), HiByte((+100 + ModuleMinTemp) *10  ), LoByte( ModuleMaxTempNumber ), HiByte( ModuleMaxTempNumber ), LoByte( ModuleMinTempNumber ), HiByte( ModuleMinTempNumber ) ], 10, 0)
ensemblerspmsg.append(msg)

# Charge/Dis command 
ChargeForbidden = 0 # 170 (0xAA) for effect
DischargeForbidden = 0 # 170 (0xAA) for effect
# 0x428+1 
msg = cSendMsg( 0x4281, [ LoByte( ChargeForbidden ), LoByte( DischargeForbidden ), 0,0,0,0,0,0 ], 10, 0)
ensemblerspmsg.append(msg)

#------------------------------------------------------------------------------
# LIST OF MESSAGES TO SEND IN RESPONSE TO INVERTER QUERY 'SYSTEM EQUIPMENT INFORMATION' byte 0 = 2

# Version Info - see documentaion
# 0x731+1 
msg = cSendMsg( 0x7311, [ 0X10, 0X10, 0X10, 0X10, 0X10, 0X10, 0X10, 0 ], 10, 0)
sysinfomsg.append(msg)

# 0x732+1
BatteryModuleQuantity = 48
BatteryModuleInSeries = 48
CellQuantityInModule = 2
VoltLevel = 4
AHNumber = 66 * BatSOH/100 # 66 AH Leaf battery capacity
# last 1 byte reserve

# 0x732+1 
msg = cSendMsg( 0x7321, [ LoByte( BatteryModuleQuantity ), HiByte( BatteryModuleQuantity ) , BatteryModuleInSeries, CellQuantityInModule, LoByte( VoltLevel ),  HiByte( VoltLevel ), int(AHNumber), 0 ], 10, 0)
sysinfomsg.append(msg)

# 0x4220 
# 0x4220+0 
#msg = cSendMsg( 0x42200, [ LoByte(  ), HiByte( ) , LoByte(  ), HiByte(  ), LoByte( ), HiByte( ), LoByte( ), HiByte() ], 10, 0)
#ensemblerspmsg.append(msg)

#------------------------------------------------------------------------------
# MAIN
#------------------------------------------------------------------------------
##loggingbasicConfig(filename='can.log',format='%(levelname)s:%(message)s', level=#loggingWARN) # INFO-WARN
#loggingbasicConfig(filename='batterydummy.log',format='%(asctime)s %(levelname)s:%(message)s', level=#loggingINFO)
#loggingdebug('Debug Message')
#logginginfo('Info Message')
#loggingwarning('Warning Message')

# open contactors on startup
OpenContactors()

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
		#print (rx_data)
		
		if (rx_data.msg_id != 0):
			print ('Message Received ' + format(rx_data.msg_id,' 02x'))
			if (rx_data.msg_id == PID_INVERTER_QUERY):
				print('Received: ',format(rx_data.msg_id, '02x'),'  msg_type: ', rx_data.msg_type)
				#check first byte is 0 or 2
				if (rx_data.msg_type == 0):
					if (ContactorsOpen):
						CloseContactors()

					for x in range(len(ensemblerspmsg)):
						msg = can.Message(arbitration_id=ensemblerspmsg[x].id, data=ensemblerspmsg[x].msgdata, extended_id=True)
						bus.send(msg)
						# send for loop delay
						time.sleep(ensemblerspmsg[x].interval/1000) # interval is in milliseconds
					print ('Ensemble Response Sent ')

				elif (rx_data.msg_type == 2):
					for x in range(len(sysinfomsg)):
						msg = can.Message(arbitration_id=sysinfomsg[x].id, data=sysinfomsg[x].msgdata, extended_id=True)
						bus.send(msg)
						# send for loop delay
						time.sleep(sysinfomsg[x].interval/1000) # interval is in milliseconds
					print ('System Info Response Sent ')

			elif (rx_data.msg_id == PID_SLEEP_AWAKE_COMMAND):
				if (rx_data.msg_type == PID_SLEEP_AWAKE_COMMAND_Req_Sleep):
					BasicStatus = BASIC_STATUS_SLEEP
					ensemblerspmsg[4].msgdata[0] = BasicStatus
					print('Status set to SLEEP')
				elif (rx_data.msg_type == PID_SLEEP_AWAKE_COMMAND_Quit_sleep):
					BasicStatus = BASIC_STATUS_IDLE
					ensemblerspmsg[4].msgdata[0] = BasicStatus
					print('Status set to IDLE')

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
	print('\n\rKeyboard interrupt')
	#Catch keyboard interrupt
	OpenContactors()
	# Reset GPIO settings
	GPIO.cleanup()
	os.system("sudo /sbin/ip link set can0 down")
	print('\n\rShutdown')

