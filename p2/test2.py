import socket
import select
import time

ip = ""
port = 8888

udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
udp_sock.setblocking(0)
udp_sock.bind((ip, port))

# States
CLOSED = "closed"
SYN_SENT = "syn_sent"
OPEN = "open"
FIN_SENT = "fin_sent"

# Timeout
timeout = 5  # seconds

class RDPSender:
    def __init__(self):
        self.state = CLOSED
        self.snd_buf = []
        self.last_sent_time = None

    def open(self):
        # Write SYN RDP packet into snd_buf
        syn_packet = self.create_packet("SYN")
        self.snd_buf.append(syn_packet)
        self.state = SYN_SENT
        self.last_sent_time = time.time()

    def close(self):
        # Write FIN packet to snd_buf
        fin_packet = self.create_packet("FIN")
        self.snd_buf.append(fin_packet)
        self.state = FIN_SENT

    def check_timeout(self):
        if self.state != CLOSED and time.time() - self.last_sent_time > timeout:
            # Resend the packets in snd_buf
            for packet in self.snd_buf:
                udp_sock.sendto(packet.encode(), (ip, port))
            self.last_sent_time = time.time()

    def create_packet(self, command):
        # Create a packet with the given command
        return f"{command}\nSequence: 0\n\n"

    def get_state(self):
        return self.state

class RDPReceiver:
    def __init__(self):
        self.rcv_buf = {}

    def get_state(self):
        # Implement the logic to determine the receiver's state
        pass

rdp_sender = RDPSender()
rdp_receiver = RDPReceiver()

while rdp_sender.get_state() != CLOSED or rdp_receiver.get_state() != CLOSED:
    readable, writable, exceptional = select.select([udp_sock], [udp_sock], [udp_sock], timeout)

    if udp_sock in readable:
        data, addr = udp_sock.recvfrom(1024)
        print(f"Received: {data.decode()}")

    if udp_sock in writable and rdp_sender.snd_buf:
        packet = rdp_sender.snd_buf.pop(0)
        udp_sock.sendto(packet.encode(), (ip, port))
        print(f"Sent: {packet}")

    rdp_sender.check_timeout()

