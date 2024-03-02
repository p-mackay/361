import sys
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
udp_sock.bind((SERVER_HOST, SERVER_PORT))

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
        self.base = 0

    def send_data(self, data):
        self.snd_buf = bytearray(data, encoding="utf-8")
        while self.snd_buf[self.base:]:
            for i in range(self.base, min(len(self.snd_buf), self.base + MAX_PAYLOAD_SIZE)):
                packet = f"DAT\nSequence: {self.base}\nLength: {sys.getsizeof(self.snd_buf[self.base:])}\n\n{self.snd_buf[self.base:i]}".encode()
                udp_sock.sendto(packet, (self.host, self.port))
                print(f"Sent packet {self.base} with sequence number {self.base}, length {sys.getsizeof(self.snd_buf[self.base:i])}")
                self.base = i

                # Wait for ACK
                self.wait_for_ack()

    def wait_for_ack(self):
        start_time = time.monotonic()
        elapsed_time = 0
        while elapsed_time < TIMEOUT:
            readable, writable, _ = select.select([udp_sock], [], [], 0.1)
            if udp_sock in readable:
                message, addr = udp_sock.recvfrom(MAX_PAYLOAD_SIZE + HEADER_LENGTH)
                if message.decode().startswith("ACK"):
                    ack_seq = int(message.decode().split("\n")[1].split(": ")[1])
                    if ack_seq == self.base:
                        return

            elapsed_time = time.monotonic() - start_time

        # Resend if timeout
        print("Resending...")
        self.send_data(self.snd_buf)

class RdpReceiver:
    def __init__(self):
        self.host = SERVER_HOST
        self.port = SERVER_PORT
        self.rcv_buf = bytearray()
        self.last_seq_number = 0

    def rcv_data(self):
        while self.rcv_buf:
            base = self.last_seq_number
            for i in range(base, len(self.rcv_buf)):
                packet = self.rcv_buf[base:i + HEADER_LENGTH]
                lines = packet.decode().split("\n")
                if len(lines) < 3:
                    break
                seq_number = int(lines[1].split(": ")[1])

                if seq_number <= self.last_seq_number:
                    continue

                length = int(lines[2].split(": ")[1])

                if i + length > len(self.rcv_buf):
                    break

                self.handle_packet(packet)
                self.last_seq_number = seq_number

                # Send ACK
                ack_packet = "ACK\nAcknowledgement: {}\n\n".format(seq_number).encode()
                udp_sock.sendto(ack_packet, (self.host, self.port))
                print(f"Sent ACK {seq_number}")

    def handle_packet(self, packet):
        print(f"Received packet {self.last_seq_number} with sequence number {self.last_seq_number}, length {len(packet)}")
        self.rcv_buf = self.rcv_buf[len(packet):]

def main():
    test_data = 'al;kdsfjal;skdfjlasdkjfla;skfjlaskjdf'
    sender = RdpSender(SERVER_HOST, SERVER_PORT)
    receiver = RdpReceiver()

    while True:
        readable, writable, _ = select.select([udp_sock], [udp_sock], [], 1)

        if udp_sock in writable:
            sender.send_data(test_data)

        if udp_sock in readable:
            receiver.rcv_data()

if __name__ == "__main__":
    main()
