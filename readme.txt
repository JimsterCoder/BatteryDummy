command to start test program, this will start can0 and expects signals on can0
$ sudo python3 dummyTSUN.py 

The above is all you need if you're connected to the inverter, however...


IF can0 and can1 are connected for testing...
start can1

$ sudo /sbin/ip link set can1 up type can bitrate 500000

start can dump
candump can1

simulate the inverter by sending messages
4200/0

$ cansend can1 00004200#0000000000000000

4200/1

$ cansend can1 00004200#0200000000000000



Below is sample output displayed by the python program upon receiving messages for the inverter

Message Received  4200
Received:  4200   msg_type:  0
Ensemble Response Sent 
Message Received  4200
Received:  4200   msg_type:  2
System Info Response Sent 
