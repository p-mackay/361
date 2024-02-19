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

# RDP Sender Class
class Rdp_sender:
    def __init__(self, udp_sock):
        self.udp_sock = udp_sock

    def rdp_send(self, data):
        packet = b'DAT' + data
        self.udp_sock.sendto(packet, (ip, port))
        print(f"Sender: Sent {packet}")

# RDP Receiver Class
class Rdp_receiver:
    def __init__(self, udp_sock):
        self.udp_sock = udp_sock

    def rdp_rcv(self):
        packet, addr = self.udp_sock.recvfrom(1024)
        if packet.startswith(b'DAT'):
            data = packet
            print(f"Receiver: Received {data}")
            return data
        return None

# Instantiate sender and receiver
rdp_sender = Rdp_sender(udp_sock)
rdp_receiver = Rdp_receiver(udp_sock)

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
            print("step: ", count)
            pass

    if udp_sock in writable:
        for msg in app_message:
            if msg:
                count += 1
                print("step: ", count)
                rdp_sender.rdp_send(msg)
                total.append(msg)
                app_message.pop()
                some_data = random.randbytes(10)
                app_message.append(some_data)
                time.sleep(1)
                print(total)



# Close the socket
udp_sock.close()
