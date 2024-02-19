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
udp_sock.setblocking(0)
udp_sock.bind((ip, port))

snd_messages = {}
rcv_messages = {}
snd_buf = []
rcv_buf = []


OPEN = "open"
SYN_SENT = "syn_sent"
FIN_SENT = "fin_sent"
CLOSED = "closed"

chunk_size = 1024  # Define the chunk size
file_chunks = []   # Initialize an empty list to store the chunks


# Design Ideas (Driver) Cont’d
'''
The only messages that the receiver has to send_packet are ACK message to the sender
States: CLOSED, OPEN
Variables: 
rcv_buffer size 2048bytes
'''
class Rdp_receiver:
    def __init__(self):
        self.state = None
        self.next_byte_exp = 0
        self.last_byte_rcv = 0


    def rcv_data(self, data):
        if data.startswith("SYN"):
            print("receiver: ", self.state)
            message = b'ACK'
            rcv_buf.append(message)
            self.state = OPEN
        if data.startswith("DAT"):
            print("receiver data",data)
        

    def getstate(self):
        return self.state


# Design Ideas (Sender)
'''
 The messages that the sender are responsible are SYN, DAT, RST, FIN
'''
class Rdp_sender:
    def __init__(self):
        self.state = None 
        self.last_send_time = None
        print("sender: ", self.state)
    # closed -> syn_sent -> open -> fin_sent -> closed

    def open(self):
        syn_message = b'SYN\n\n'
        snd_buf.append(syn_message)
        # write SYN rdp packet into snd_buf
        self.state = SYN_SENT 
        print("sender: ", self.state)

    def rcv_ack(self, message):
        if self.state == SYN_SENT:
            if message.startswith("ACK"):
                print("con established")
                self.state = OPEN
                print(self.state)
            else:
                print("con failed")
        if self.state == OPEN:
            pass

    def send_packet(self):
        if self.state == OPEN:
            test_data = b'DAT: Hello World!'
            snd_buf.append(test_data)
            pass
    '''
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
    '''

    def getstate(self):
        return self.state


    def close(self):
        # write FIN packet to snd_buf
        self.state = CLOSED
        pass

    '''
    def check_timeout(self):
        if self.state != close and timeout has occurred:
    '''
            # rewrite the rdp packets into snd_buf
# Design Ideas (Sender)
# Open the file in binary mode
with open('example.txt', 'rb') as file:
    while True:
        chunk = file.read(chunk_size)  # Read a chunk of data
        if not chunk:
            break  # If the chunk is empty, end of file is reached
        file_chunks.append(chunk)  # Append the chunk to the list

# Print the number of chunks and the first chunk as an example
#print(f"Total chunks: {len(file_chunks)}")
#print(f"First chunk: {file_chunks[0]}")


rdp_sender = Rdp_sender()
rdp_receiver = Rdp_receiver()

rdp_sender.open()
print(snd_buf)

while (rdp_sender.getstate() != CLOSED) and (rdp_receiver.getstate()) != CLOSED:

    readable, writable, exceptional = select.select([udp_sock],
                                                          [udp_sock],
                                                          [udp_sock],
                                                          1)
    if udp_sock in readable:
        # Receive data and append it into rcv_buf
        data, _ = udp_sock.recvfrom(1024)
        rcv_buf.append(data)
        print("rcv_buf: ", rcv_buf)

        # Check if the message in rcv_buf is complete (detect a new line)
        if b'\n\n' in b''.join(rcv_buf):
            # Extract the message from rcv_buf
            complete_message = b''.join(rcv_buf).split(b'\n\n')[0]
            print("complete message: ", complete_message)
            rcv_buf.clear()  # Clear the buffer after extracting the message

            # Split the message into RDP packets
            packets = complete_message.split(b'\n\n')
            for packet in packets:
                # Decode and process each packet
                decoded_packet = packet.decode()
                if decoded_packet.startswith("ACK"):
                    rdp_sender.rcv_ack(decoded_packet)
                else:
                    rdp_receiver.rcv_data(decoded_packet)

# Design Ideas (Driver) Cont’d
    if udp_sock in writable and snd_buf:
        # send_packet the first packet in the buffer
        udp_sock.sendto(snd_buf[0], (ip, port))
        print("Sent: ", snd_buf[0])

        # Remove the packet that was just sent from the buffer
        snd_buf.pop(0)

    '''
    if udp_sock in writable:
        print("writable: ", snd_buf[0])
        udp_sock.sendto(snd_buf[0], (ip,port))
            # remove the bytes already sent from snd_buf
        #rdp_sender.check_timeout()
    '''
    time.sleep(1)
    print("----------------------")

