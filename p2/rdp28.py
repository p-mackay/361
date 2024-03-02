import sys
import queue
import socket
import select
import random
import time
from enum import Enum

SERVER_HOST = "localhost"
SERVER_PORT = 8888

# Initialize UDP socket
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
udp_sock.bind((ip, port))

# RDP Sender Class

test_data = b'asl;kdfjs;lkdfjs;ladkfjs;aldkfj;salkfjjjjsldkfjsdf'

class State(Enum):
    CLOSED = "closed"
    SYN_SENT = "syn_sent"
    OPEN = "open"
    FIN_SENT = "fin_sent"

# Constants
MAX_PAYLOAD_SIZE = 1024
HEADER_LENGTH = 12
TIMEOUT = 1


class RdpSender:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.snd_buf = bytearray()
        self.data_buf = bytearray()
        self.snd_nxt = 0
        self.snd_una = 0
        self.snd_wnd = 1
        self.base_time = time.monotonic()

    def snd(self):
        # Read the file and fill the sending buffer
        with open("acks.txt", "rb") as file:
            while True:
                chunk = file.read(MAX_PAYLOAD_SIZE)
                if not chunk:
                    break
                self.data_buf += chunk

        # Send the data in packets
        while self.snd_nxt < len(self.data_buf):
            base = self.snd_una
            while self.snd_wnd < len(self.data_buf) - self.snd_nxt and self.snd_wnd < 2**16:
                self.snd_wnd *= 2
            for i in range(base, min(self.snd_nxt + self.snd_wnd, len(self.snd_buf))):
                packet = "DAT\nSequence: {}\nLength: {}\n\n{}".format(self.snd_nxt, sys.getsizeof(self.data_buf[i:]), self.data_buf[i:]).encode()
                self.udp_sock.sendto(packet, (self.host, self.port))
                print(f"Sent packet {i} with sequence number {i}, length {sys.getsizeof(self.data_buf[i:i + MAX_PAYLOAD_SIZE])}")
                self.snd_nxt = i + MAX_PAYLOAD_SIZE

            # Receive ACK packets during the send operation
            start_time = time.monotonic()
            elapsed_time = 0
            while (elapsed_time < TIMEOUT):
                readable, writable, exceptional = select.select([self.udp_sock], [], [], 0.1)
                if self.udp_sock in readable:
                    packet, addr = self.udp_sock.recvfrom(MAX_PAYLOAD_SIZE + HEADER_LENGTH)
                    lines = packet.decode().split('\n\n')
                    if lines[0][:3] == 'ACK':
                        ack_seq = int(lines[0].split(': ')[1])
                        if ack_seq >= base and ack_seq < self.snd_nxt:
                            self.snd_una = max(self.snd_una, ack_seq)
                            self.snd_wnd = self.snd_nxt - self.snd_una

                            # Slide the window
                            for j in range(ack_seq, self.snd_una):
                                self.data_buf[j - base:j - base + MAX_PAYLOAD_SIZE] = self.snd_buf[j - base:j - base + MAX_PAYLOAD_SIZE]

                        if ack_seq == self.snd_nxt - 1:
                            self.snd_una = self.snd_nxt
                            self.snd_wnd = self.snd_nxt - self.snd_una

                        # Break the loop if all data has been sent
                        if self.snd_una == len(self.data_buf):
                            break

                elapsed_time = time.monotonic() - start_time

            if elapsed_time >= TIMEOUT and self.snd_una < len(self.data_buf):
                # Retransmit packets if timeout happens
                self.snd_nxt = self.snd_una
                self.snd_wnd = min(self.snd_wnd, len(self.data_buf) - self.snd_nxt)

class RdpReceiver:
    def __init__(self):
        self.host = SERVER_HOST 
        self.port = SERVER_PORT 
        self.rcv_nxt = 0
        self.rcv_wnd = 1

        # Initialize the UDP socket
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Initialize the receiving buffer
        self.rcv_buf = bytearray()

        # Track the sequence number of the last received data packet
        self.last_seq_number = 0
        
    def rcv_data(self):
        while self.rcv_nxt < len(self.rcv_buf):
            base = self.rcv_nxt
            while self.rcv_wnd < len(self.rcv_buf) - self.rcv_nxt and self.rcv_wnd < 2**16:
                self.rcv_wnd *= 2
            while self.rcv_wnd > 0:
                packet, addr = self.udp_sock.recvfrom(MAX_PAYLOAD_SIZE + HEADER_LENGTH)
                lines = packet.decode().split('\n\n')

                # Extract the sequence number from the received data packet
                seq_number = int(lines[0].split(': ')[1])

                # Compare the sequence number with the last received data packet
                if seq_number <= self.last_seq_number:
                    # Drop the packet if it has a lower sequence number than the last received one
                    continue

                length = sys.getsizeof(lines[1])

                # Update the last received sequence number
                self.last_seq_number = seq_number

                # Construct the ACK packet
                ack_packet = "ACK\nAcknowledgment: {}\nWindow: {}\n\n".format(seq_number, self.window).encode()
                payload = ack_packet[HEADER_LENGTH:HEADER_LENGTH + length]

                # Send the ACK packet
                snd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                snd_sock.sendto(ack_packet, (self.host, self.port))

                # Copy the payload into the receiving buffer
                self.rcv_buf[self.rcv_nxt:self.rcv_nxt + length] = payload

                print(f"Received packet {self.rcv_nxt} with sequence number {seq_number}, length {length}")
                self.rcv_nxt += length
                self.rcv_wnd -= length

        # Save the received data to a file
        with open(filename, "wb") as file:
            file.write(self.rcv_buf)
def main():
    sender = RdpSender(SERVER_HOST, SERVER_PORT)
    receiver = RdpReceiver(SERVER_HOST, SERVER_PORT)

    # Bind the socket to the server IP and port
    receiver.udp_sock.bind((receiver.host, receiver.port))

    # Main loop
    while True:
        readable, writable, _ = select.select([receiver.udp_sock], [receiver.udp_sock], [], 1)

        if receiver.udp_sock in readable:
            message, addr = receiver.udp_sock.recvfrom(1024)
            if message.decode().startswith("ACK"):
                sender.rcv_ack()
            else: 
                receiver.rcv_data()

        if receiver.udp_sock in writable:
            try:
                msg = sender.snd_buf
                if len(msg) > 0:
                    bytes_sent = receiver.udp_sock.sendto(msg[:MAX_PAYLOAD_SIZE], (sender.host, sender.port))
                    sender.snd_buf = sender.snd_buf[bytes_sent:]
            except IndexError:
                break

if __name__ == "__main__":
    main()
