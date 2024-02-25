# Re-importing necessary libraries after execution state reset
import socket
import select
import random
import time

# Define IP and port for UDP socket communication
ip = "localhost"
port = 8888

# Initialize UDP socket, set reuse address option, and bind to the specified IP and port
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
udp_sock.bind((ip, port))

# RDP Sender Class
class Rdp_sender:
    def __init__(self, udp_sock):
        self.udp_sock = udp_sock
        self.base = 0  # LastByteAcked
        self.next_seq_num = 0  # LastByteSent
        self.window_size = 3  # Example window size
        self.send_buffer = {}  # Buffer to keep track of sent packets not yet acknowledged

    def send_packet(self, data, seq_num):
        # Prefix data with sequence number and send
        packet = f"{seq_num}:{data}".encode()
        self.udp_sock.sendto(packet, (ip, port))
        print(f"Sender: Sent packet {seq_num}")

    def rdp_send(self, data):
        # Implement Go-Back-N ARQ for sending data
        while self.next_seq_num < self.base + self.window_size:
            self.send_packet(data, self.next_seq_num)
            self.send_buffer[self.next_seq_num] = data
            self.next_seq_num += 1

# RDP Receiver Class
class Rdp_receiver:
    def __init__(self, udp_sock):
        self.udp_sock = udp_sock
        self.expected_seq_num = 0  # Expected sequence number
        self.acknowledged_packets = set()  # Keep track of acknowledged packets

    def rdp_rcv(self):
        packet, addr = self.udp_sock.recvfrom(1024)
        seq_num, data = packet.decode().split(':', 1)
        seq_num = int(seq_num)

        print(f"Receiver: Received packet {seq_num}")
        # Simulate ACK sending
        if seq_num == self.expected_seq_num:
            self.expected_seq_num += 1
            # Send ACK for the received packet
            ack_packet = f"ACK:{seq_num}".encode()
            self.udp_sock.sendto(ack_packet, addr)
            print(f"Receiver: Sent ACK for packet {seq_num}")
        elif seq_num > self.expected_seq_num:
            # Out-of-order packet received, send duplicate ACK for the last correctly received packet
            ack_packet = f"ACK:{self.expected_seq_num - 1}".encode()
            self.udp_sock.sendto(ack_packet, addr)
            print(f"Receiver: Sent duplicate ACK for packet {self.expected_seq_num - 1}")

# Main function to setup and run the RDP protocol simulation
def run_rdp_simulation():
    # Instantiate sender and receiver
    rdp_sender = Rdp_sender(udp_sock)
    rdp_receiver = Rdp_receiver(udp_sock)

    # Application message to send
    messages = [b"Hello", b"World", b"from", b"RDP", b"Simulation"]
    msg_index = 0

    # Main loop for sending and receiving messages
    while msg_index < len(messages):
        readable, writable, _ = select.select([udp_sock], [udp_sock], [], 0.5)

        if udp_sock in readable:
            rdp_receiver.rdp_rcv()

        if udp_sock in writable and msg_index < len(messages):
            rdp_sender.rdp_send(messages[msg_index])
            msg_index += 1

        time.sleep(1)  # Wait a bit before next send attempt to simulate network delay

    # Close the UDP socket
    udp_sock.close()

# Note: To run the simulation, the run_rdp_simulation() function call should be uncommented outside of this code block.

run_rdp_simulation()
