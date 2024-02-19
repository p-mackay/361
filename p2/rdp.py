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
# RDP Receiver Class
class Rdp_receiver:
    def __init__(self):
        self.state = CLOSED
        self.next_byte_expected = 1  # The sequence number of the next expected byte

    def rcv_data(self, data):
        if data.startswith(b"SYN"):
            if self.state == CLOSED:
                print("Receiver: SYN received, sending ACK")
                self.send_ack()
                self.state = OPEN

        elif data.startswith(b"DAT"):
            seq_num = int(data.split(b"\n")[1].split(b":")[1])
            if seq_num == self.next_byte_expected:
                print("Receiver: Data received:", data)
                self.next_byte_expected += len(data.split(b"\n\n")[1])  # Update the expected sequence number
                self.send_ack()  # Send ACK for the next expected byte

        elif data.startswith(b"FIN"):
            if self.state == OPEN:
                print("Receiver: FIN received, closing connection")
                self.state = CLOSED

    def send_ack(self):
        ack_message = f"ACK\nSeq: {self.next_byte_expected}\n\n".encode()
        udp_sock.sendto(ack_message, (ip, port))

    def get_state(self):
        return self.state


# Design Ideas (Sender)
'''
 The messages that the sender are responsible are SYN, DAT, RST, FIN
'''
class Rdp_sender:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.setblocking(0)
        self.state = CLOSED
        self.next_seq_num = 0
        self.send_base = 0
        self.snd_buf = []
        self.timer_running = False
        self.timeout_interval = 5  # seconds

    def open(self):
        if self.state == CLOSED:
            self.state = SYN_SENT
            self.send_packet("SYN")

    def send_packet(self, data):
        if self.state == OPEN:
            segment = f"{data}\nSeq: {self.next_seq_num}\n\n".encode()
            print(f"Sender: Sent packet with Seq: {self.next_seq_num} data: {data} state: {self.state}")
            self.snd_buf.append((segment, self.next_seq_num))
            self.udp_sock.sendto(segment, (self.ip, self.port))

            if not self.timer_running:
                self.start_timer()
            self.next_seq_num += len(data)

    def start_timer(self):
        self.timer_running = True
        self.timer_start_time = time.time()

    def stop_timer(self):
        self.timer_running = False

    def check_timer(self):
        if self.timer_running and time.time() - self.timer_start_time > self.timeout_interval:
            self.retransmit()
            self.start_timer()

    def retransmit(self):
        if self.snd_buf:
            segment, seq_num = self.snd_buf[0]
            self.udp_sock.sendto(segment, (self.ip, self.port))

    def handle_ack(self, ack_num):
        if self.state == SYN_SENT:
            self.state = OPEN
        if ack_num > self.send_base:
            self.send_base = ack_num
            self.snd_buf = [s for s in self.snd_buf if s[1] >= ack_num]
            if self.snd_buf:
                self.start_timer()
            else:
                self.stop_timer()

    def close(self):
        if self.state == OPEN:
            self.send_packet("FIN")
            self.state = FIN_SENT

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

    def get_state(self):
        return self.state


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


rdp_sender = Rdp_sender(ip, port)
rdp_receiver = Rdp_receiver()

rdp_sender.open()

# Driver Code
while rdp_sender.get_state() != CLOSED or rdp_receiver.get_state() != CLOSED:
    readable, writable, _ = select.select([udp_sock], [udp_sock], [], 1)

    if udp_sock in readable:
        data, _ = udp_sock.recvfrom(1024)
        if data.startswith(b"ACK"):
            ack_num = int(data.split(b"\n")[1].split(b":")[1])
            rdp_sender.handle_ack(ack_num)
        else:
            rdp_receiver.rcv_data(data)

    if udp_sock in writable and rdp_sender.snd_buf:
        packet, seq_num = rdp_sender.snd_buf.pop(0)
        udp_sock.sendto(packet, (ip, port))
        print(f"Sent: {packet.decode()}")

    rdp_sender.check_timer()

    # Simulate sending data from the application
    if rdp_sender.get_state() == OPEN or rdp_sender.get_state() == SYN_SENT:
        rdp_sender.send_packet("Hello")
        rdp_sender.send_packet("Hello")
        rdp_sender.send_packet("Hello")
        rdp_sender.send_packet("Hello")
        rdp_sender.send_packet("Hello")
        time.sleep(1)  # Pause to simulate data being generated at intervals

