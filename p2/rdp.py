'''
Design Ideas (Driver)
●
Initialization:
    ○
Import packages such as socket, sys, etc.
○
Initialize a UDP socket: udp_sock
■
You will only need a single socket!
○
Initialize a sending buffer: snd_buf
○
Initialize a receiving buffer: rcv_buf
○
Initialize two classes: rdp_sender, rdp_receiver
'''
'''
kurose 3.1:
kurose 3.2:
kurose 3.3:
kurose 3.4-1:

                '''
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
udp_sock.setblocking(0)
udp_sock.bind((ip, port))

snd_messages = {}
rcv_messages = {}

CLOSED = "closed"
SYN_SENT = "syn_sent"
OPEN = "open"
FIN_SENT = "fin_sent"


# Design Ideas (Driver) Cont’d
class rdp_receiver:
    pass

# Design Ideas (Sender)
class rdp_sender:
    def __init__(self):
        self.state = CLOSED
        self.snd_buf = []
        self.last_send_time = None
    # closed -> syn_sent -> open -> fin_sent -> closed

    def open(self):
        syn_message = b'SYN\n\n'
        udp_sock.sendto(syn_message,ip)
        # write SYN rdp packet into snd_buf
        self.state = SYN_SENT 

    def rcv_ack(self):
        if self.state == SYN_SENT:
            ack_packet, _ = udp_sock.recvfrom(1024)
            message = ack_packet.decode()
            if message == "ACK":
                print("con established")
                self.state = OPEN
            else:
                print("con failed")

        if self.state == OPEN:
            if three duplicate received:
                # rewrite the rdp packets into snd_buf
        if ack# is correct:
            # move the sliding window
                        # write the available window of DAT rdp packets into snd_buf 
            # if all data has been sent, call self.close()
        if self.state == fin_sent:
            if ack# is correct:
        self.state = close

    def send(self):
        if self.state == OPEN:

    def close(self):
        # write FIN packet to snd_buf
        self.state = FIN_SENT

    def check_timeout(self):
        if self.state != close and timeout has occured:
            # rewrite the rdp packets into snd_buf
# Design Ideas (Sender)

while (rdp_sender.getstate() != close) or (rdp_receiver.getstate() != close):

    readable, writable, exceptional = select.select([udp_sock],
                                                          [udp_sock],
                                                          [udp_sock],
                                                          timeout)
    if udp_sock in readable:
        # receive data and append it into rcv_buf
        if the message in rcv_buf is complete (detect a new line):
            # extract the message from rcv_buf
            # split the message into RDP packets
            for each packet:
                if RDP packet is ACK:
                    rdp_sender.rcv_ack(message)
                else:
                    rdp_receiver.rcv_data(message)

# Design Ideas (Driver) Cont’d
    if udp_sock in writable:
        bytes_sent = udp_sock.sendto(snd_buf, ECHO_SRV)
            # remove the bytes already sent from snd_buf
        rdp_sender.check_timeout()


