import socket
import select
import time

# Define constants
CLOSED = "closed"
SYN_SENT = "syn_sent"
OPEN = "open"
FIN_SENT = "fin_sent"
TIMEOUT = 5  # seconds

# Initialize UDP socket
ip = "localhost"
port = 8888
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
udp_sock.setblocking(0)
udp_sock.bind((ip, port))

# Initialize buffers
snd_buf = []
rcv_buf = []

# RDP Sender class
class RDPSender:
    def __init__(self):
        self.state = CLOSED
        self.last_send_time = None
        self.base = 1
        self.nextseqnum = 1

    def open(self):
        if self.state == CLOSED:
            syn_message = b"SYN\n\n"
            snd_buf.append(syn_message)
            self.state = SYN_SENT
            self.last_send_time = time.time()

    def rcv_ack(self, message):
        if self.state == SYN_SENT and message == "ACK\n\n":
            print("Connection established.")
            self.state = OPEN
        # Add more conditions for other states

    def send_data(self, data):
        if self.state == OPEN:
            data_message = f"DAT\n\n{data}\n\n".encode()
            snd_buf.append(data_message)
            self.last_send_time = time.time()

    def close(self):
        if self.state == OPEN:
            fin_message = b"FIN\n\n"
            snd_buf.append(fin_message)
            self.state = FIN_SENT
            self.last_send_time = time.time()

    '''
    def check_timeout(self):
        if self.state != CLOSED and time.time() - self.last_send_time > TIMEOUT:
            # Resend all packets in snd_buf
            for packet in snd_buf:
                udp_sock.sendto(packet, (ip, port))
            self.last_send_time = time.time()
    '''

    def get_state(self):
        return self.state

# RDP Receiver class
class RDPReceiver:
    def __init__(self):
        self.state = CLOSED

    def rcv_data(self, data):

        if self.state == OPEN:
            if data.seq < rcv_exp:
                drop packet
            if data.seq > rcv_exp:
                put the rdp with seq into a buffer data_buf
                return an RDP packet with duplicate ack
            if data.seq == rcv_exp:
                check data_buf and update rcv_exp
                return an ack RDP packet
    # Implement logic to handle incoming data
        pass

    def get_state(self):
        return self.state

# Instantiate sender and receiver
rdp_sender = RDPSender()
rdp_receiver = RDPReceiver()

# Main loop
while rdp_sender.get_state() != CLOSED or rdp_receiver.get_state() != CLOSED:
    readable, writable, _ = select.select([udp_sock], [udp_sock], [], TIMEOUT)

    if udp_sock in readable:
        data, _ = udp_sock.recvfrom(1024)
        message = data.decode()
        if message.startswith("ACK"):
            rdp_sender.rcv_ack(message)
        else:
            rdp_receiver.rcv_data(message)

    if udp_sock in writable:
        while snd_buf:
            packet = snd_buf.pop(0)
            udp_sock.sendto(packet, (ip, port))

    rdp_sender.check_timeout()

# Close the socket
udp_sock.close()

