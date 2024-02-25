from enum import Enum
import socket
import select

ip = "localhost"
port = 8888

# Initialize UDP socket
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
udp_sock.bind((ip, port))

# Define states using the Enum class
class State(Enum):
    CLOSED = 1
    SYN_SENT = 2
    OPEN = 3
    FIN_SENT = 4

# RDP Sender Class
class Rdp_sender:
    def __init__(self, udp_sock, dest_ip, dest_port):
        self.udp_sock = udp_sock
        self.dest_ip = dest_ip
        self.dest_port = dest_port
        self.snd_una = 0  # Oldest unacknowledged sequence number
        self.snd_nxt = 0  # Next sequence number to be sent
        self.snd_wnd = 1024  # Send window size
        self.state = State.CLOSED

    def rdp_send(self, data):
        if self.state == State.OPEN:
            packet = f"DAT:{self.snd_nxt}:{data}".encode()
            self.udp_sock.sendto(packet, (self.dest_ip, self.dest_port))
            print(f"Sender: Sent {packet}")
            self.snd_nxt += len(data)

    def open(self):
        if self.state == State.CLOSED:
            syn_packet = f"SYN\n{self.snd_nxt}".encode()
            self.udp_sock.sendto(syn_packet, (self.dest_ip, self.dest_port))
            self.state = State.SYN_SENT
            print("Sender: Sent SYN packet")

    def close(self):
        if self.state == State.OPEN:
            fin_packet = f"FIN:{self.snd_nxt}".encode()
            self.udp_sock.sendto(fin_packet, (self.dest_ip, self.dest_port))
            self.state = State.FIN_SENT
            print("Sender: Sent FIN packet")

    def rcv_ack(self, ack):
        if self.state == State.SYN_SENT and ack == self.snd_nxt + 1:
            self.state = State.OPEN
            print("Sender: Connection established")
        elif self.state == State.FIN_SENT and ack == self.snd_nxt + 1:
            self.state = State.CLOSED
            print("Sender: Connection closed")

# RDP Receiver Class
class Rdp_receiver:
    def __init__(self, udp_sock):
        self.udp_sock = udp_sock
        self.rcv_nxt = 0
        self.rcv_wnd = 1024
        self.state = State.CLOSED

    def rdp_rcv(self):
        packet, addr = self.udp_sock.recvfrom(1024)
        print(packet)
        header, seq, data = packet.decode().split(':', 2)
        seq = int(seq)

        if header == "SYN" and self.state == State.CLOSED:
            self.rcv_nxt = seq + 1
            ack_packet = f"ACK:{self.rcv_nxt}".encode()
            self.udp_sock.sendto(ack_packet, addr)
            self.state = State.OPEN
            print("Receiver: Connection established")
        elif header == "FIN" and self.state == State.OPEN:
            self.rcv_nxt = seq + 1
            ack_packet = f"ACK:{self.rcv_nxt}".encode()
            self.udp_sock.sendto(ack_packet, addr)
            self.state = State.CLOSED
            print("Receiver: Connection closed")
        elif header == "DAT" and self.state == State.OPEN:
            if seq == self.rcv_nxt:
                print(f"Receiver: Received {data}")
                self.rcv_nxt += len(data)
                ack_packet = f"ACK:{self.rcv_nxt}".encode()
                self.udp_sock.sendto(ack_packet, addr)
            else:
                print("Receiver: Out-of-order packet received")

# Instantiate sender and receiver
rdp_sender = Rdp_sender(udp_sock, ip, port)
rdp_receiver = Rdp_receiver(udp_sock)

# Application message to send
app_message = b"Hello"

rdp_sender.open()

# Main loop
while True:
    readable, writable, _ = select.select([udp_sock], [udp_sock], [], 1)

    if udp_sock in readable:
        rdp_receiver.rdp_rcv()

    if udp_sock in writable:
        rdp_sender.rdp_send(app_message)

# Close the socket
udp_sock.close()

