from enum import Enum
import socket
import select
import random
import time


ip = "localhost"
port = 8888

# Initialize UDP socket
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
udp_sock.bind((ip, port))

class State(Enum):
    closed = 1
    syn_sent = 2
    open = 3
    fin_sent = 4

class Rdp_sender:
    def __init__(self, udp_sock, dest_ip, dest_port):
        self.udp_sock = udp_sock
        self.dest_ip = dest_ip
        self.dest_port = dest_port
        self.snd_una = 0  # Oldest unacknowledged sequence number
        self.snd_nxt = 0  # Next sequence number to be sent
        self.snd_wnd = 1024  # Send window size
        self.state = State.closed

    def rdp_send(self, data):
        if self.state == State.open:
            packet = f"DAT:{self.snd_nxt}:{data}".encode()
            self.udp_sock.sendto(packet, (self.dest_ip, self.dest_port))
            print(f"Sender: Sent {packet}")
            self.snd_nxt += len(data)

    def open(self):
        if self.state == State.closed:
            syn_packet = f"SYN:{self.snd_nxt}".encode()
            self.udp_sock.sendto(syn_packet, (self.dest_ip, self.dest_port))
            self.state = State.syn_sent
            print("Sender: Sent SYN packet")

    def close(self):
        if self.state == State.open:
            fin_packet = f"FIN:{self.snd_nxt}".encode()
            self.udp_sock.sendto(fin_packet, (self.dest_ip, self.dest_port))
            self.state = State.fin_sent
            print("Sender: Sent FIN packet")

    def rcv_ack(self, ack):
        if self.state == State.syn_sent and ack == self.snd_nxt + 1:
            self.state = State.open
            print("Sender: Connection established")
        elif self.state == State.fin_sent and ack == self.snd_nxt + 1:
            self.state = State.closed
            print("Sender: Connection closed")

class Rdp_receiver:
    def __init__(self, udp_sock):
        self.udp_sock = udp_sock
        self.rcv_nxt = 0
        self.rcv_wnd = 1024
        self.state = State.closed

    def rdp_rcv(self):
        packet, addr = self.udp_sock.recvfrom(1024)
        header, seq, data = packet.decode().split(':', 2)
        seq = int(seq)

        if header == "SYN" and self.state == State.closed:
            self.rcv_nxt = seq + 1
            ack_packet = f"ACK:{self.rcv_nxt}".encode()
            self.udp_sock.sendto(ack_packet, addr)
            self.state = State.open
            print("Receiver: Connection established")
        elif header == "FIN" and self.state == State.open:
            self.rcv_nxt = seq + 1
            ack_packet = f"ACK:{self.rcv_nxt}".encode()
            self.udp_sock.sendto(ack_packet, addr)
            self.state = State.closed
            print("Receiver: Connection closed")
        elif header == "DAT" and self.state == State.open:
            if seq == self.rcv_nxt:
                print(f"Receiver: Received {data}")
                self.rcv_nxt += len(data)
                ack_packet = f"ACK:{self.rcv_nxt}".encode()
                self.udp_sock.sendto(ack_packet, addr)
            else:
                print("Receiver: Out-of-order packet received")

rdp_sender = Rdp_sender(udp_sock, ip, port)
rdp_receiver = Rdp_receiver(udp_sock)
rdp_sender.open()

# app message to send
app_message = []
total = []
app_message.append(b"Hello")
count = 0

# Main loop
while True:
    readable, writable, _ = select.select([udp_sock], [udp_sock], [], 1)

    if udp_sock in readable:
        received_data = rdp_receiver.rdp_rcv()
        if received_data:
            count += 1

    if udp_sock in writable:
        for msg in app_message:
            if msg:
                count += 1
                rdp_sender.rdp_send(msg)
                total.append(msg)
                app_message.pop()
                some_data = random.randbytes(10)
                app_message.append(some_data)
                time.sleep(1)



# Close the socket
udp_sock.close()
