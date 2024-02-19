import time
import sys
import socket
import select
import queue
import re
import os
from datetime import datetime, timedelta
from time import gmtime, strftime

ip = "localhost"
port = 8888
port = int(port)  

udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
udp_sock.bind((ip, port))

snd_buf = []
rcv_buf = []

class Rdp_sender:
    def __init__(self):
        pass

    def rdp_send(self, data):
        packet = 'DAT' + data  
        pass

# RDP Receiver Class
class Rdp_receiver:
    def __init__(self):
        pass

    def rcv_data(self, data):
        pass



rdp_sender = Rdp_sender()
rdp_receiver = Rdp_receiver()

application_message = b"Hello"
'''
Here is how this simple program should function:
The sending side of rdt simply accepts data from the upper layer via the 
rdt_send(data) event, creates a packet containing the data (via the action 
make_pkt(data)) and sends the packet into the channel. In practice, the  
rdt_send(data) event would result from a procedure call (for example, to 
rdt_send()) by the upper-layer application.

On the receiving side, rdt receives a packet from the underlying channel via 
the rdt_rcv(packet) event, removes the data from the packet (via the action 
extract (packet, data)) and passes the data up to the upper layer (via 
the action deliver_data(data)). In practice, the rdt_rcv(packet) event 
would result from a procedure call (for example, to rdt_rcv()) from the lower-
layer protocol.

'''
while True:
    readable, writable, _ = select.select([udp_sock], [udp_sock], [], 1)

    if udp_sock in readable:
        pass

    if udp_sock in writable:
        pass
