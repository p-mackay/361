import sys
import queue
import socket
import select
import random
import time
from enum import Enum

ip = "localhost"
port = 8888

# Initialize UDP socket
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
udp_sock.bind((ip, port))

# RDP Sender Class

snd_buf = queue.Queue() 
rcv_buf = queue.Queue() 
test_data = b'asl;kdfjs;lkdfjs;ladkfjs;aldkfj;salkfjjjjsldkfjsdf'
data_buf = queue.Queue()
data_buf.put(test_data)


def split_file(filename):
    chunk_size = 1024
    file_queue = queue.Queue()
    with open(filename, 'rb') as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            file_queue.put(chunk)
    return file_queue
f_queue = split_file("rfc.txt")


class State(Enum):
    CLOSED = "closed"
    SYN_SENT = "syn_sent"
    OPEN = "open"
    FIN_SENT = "fin_sent"

#----------------------------------------------------
class Rdp_sender:
    def __init__(self, udp_sock):
        self.snd_nxt = 0
        self.snd_base = 0 # oldest unacknowledged packet
        self.window = 0 #
        self.state = State.CLOSED
        self.LastByteSent = 0
        self.LastByteAcked = 0


    def open(self):
        syn_packet = "SYN\nSequence: {}\nLength: {}\n\n".format(0, 0).encode()
        snd_buf.put(syn_packet)
        self.state = State.SYN_SENT
        ##print("Sender: SYN\nSequence: {}\nLength: {}\n\n".format(0, 0).encode())

    def send(self):
        if self.state == State.OPEN:
            while True:
                if (self.snd_nxt < self.snd_base + self.window) and self.LastByteSent <= self.snd_nxt:
                    try:
                        msg = f_queue.get_nowait()
                    except queue.Empty:
                        break
                    dat_packet = "DAT\nSequence: {}\nLength: {}\n\n{}".format(self.snd_nxt, sys.getsizeof(msg), msg).encode()
                    print("SENDER;Sequence: {};Length: {};".format(self.snd_nxt, sys.getsizeof(msg)).encode())
                    snd_buf.put(dat_packet)
                    self.snd_nxt = self.snd_nxt + sys.getsizeof(msg)
                    self.LastByteSent = self.snd_nxt
                else:
                    break

    def rcv_ack(self, message):
        if self.state == State.SYN_SENT:
            parts = message.decode().split('\n')
            if parts[0] == "ACK":
                ack = int(parts[1].split(': ')[1])
                self.window = int(parts[2].split(': ')[1])
                self.state = State.OPEN
        if self.state == State.OPEN:
            #print(message)
            if message: 
                parts = message.decode().split('\n')
                if parts[0] == "ACK":
                    ack = int(parts[1].split(': ')[1])
                    wind = int(parts[2].split(': ')[1])
                    print("SENDER: Received;ACK: {};Window: {};".format(ack, wind))
                    time.sleep(1)

                    if ack > self.snd_base:
                        self.snd_base = ack
                    self.LastByteAcked = ack
                    self.window = wind
                    self.send()

    def getstate(self):
        return self.state

    def check_timeout(self):
        # Implement timeout and retransmission logic here
        pass

# RDP Receiver Class
#----------------------------------------------------
class Rdp_receiver:
    def __init__(self, udp_sock):
        self.seq_expected = 0
        self.state = State.CLOSED
        self.buf_size = 5120 
        self.RcvBuffer = 5120  # Total buffer size
        self.LastByteRcvd = 0  # Last byte received and stored in the buffer
        self.LastByteRead = 0  # Last byte read by the application
        self.rwnd = self.RcvBuffer
        self.packet_buffer = queue.Queue()
        self.count = 0

    def rcv_data(self, message):
        if self.state == State.CLOSED:
            lines = message.decode().split('\n')
            header = lines[0]
            if header == "SYN":
                seq_num = int(lines[1].split(': ')[1])
                self.seq_expected = seq_num
                self.rcv_nxt = seq_num + 1
                ack_packet = "ACK\nAcknowledgment: {}\nWindow: {}\n\n".format(self.rcv_nxt, self.RcvBuffer).encode()
                snd_buf.put(ack_packet)
                self.state = State.OPEN
        elif self.state == State.OPEN:

            self.packet_buffer.put(message)
            self.count += 1
            #print(self.count)
            lines = message.decode().split('\n\n')
            header = lines[0]
            data = lines[1]
            parts = header.split('\n')
            command = parts[0]
            seq = int(parts[1].split(': ')[1])
            len = int(parts[2].split(': ')[1])
            print("RECEIVER: Received;Sequence: {};Length: {};".format(seq, len))
            if command == "DAT":

                self.seq_expected = seq + len
                self.LastByteRcvd = seq + len

                with open('output.txt', 'a') as file:
                    file.write(data)
                    self.LastByteRead = self.LastByteRead + len

                self.rwnd = self.RcvBuffer - (self.LastByteRcvd - self.LastByteRead)
                #print(self.LastByteRcvd, self.LastByteRead)
                ack_packet = f"ACK\nAcknowledgment: {self.seq_expected}\nWindow: {self.rwnd}\n\n".encode()
                snd_buf.put(ack_packet)
                #time.sleep(1)



rdp_sender = Rdp_sender(udp_sock)
rdp_receiver = Rdp_receiver(udp_sock)
rdp_sender.open()

# Main loop
while True:
    readable, writable, _ = select.select([udp_sock], [udp_sock], [], 1)

    if udp_sock in readable:
        message, addr = udp_sock.recvfrom(1024)
        if message.decode().startswith("ACK"):
            rdp_sender.rcv_ack(message)
        else: 
            rdp_receiver.rcv_data(message)

    if udp_sock in writable:

        try:
            msg = snd_buf.get_nowait()
        except queue.Empty:
            break

        else:
            bytes_sent = udp_sock.sendto(msg, (ip, port))

    '''
    for s in readable:
        if s is udp_sock:
            packet, addr = udp_socket.recvfrom(1024)  # Assume 1024 is the packet size
            incoming_data_queue.append((packet, addr))  # Enqueue for processing

    # Handle writable sockets
    for s in writable:
        if s is udp_sock and outgoing_data_queue:
            data, addr = outgoing_data_queue.pop(0)
            udp_socket.sendto(data, addr)  # Send the packet
    '''


# Close the socket
udp_sock.close()
