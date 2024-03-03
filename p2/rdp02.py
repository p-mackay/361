import socket
import os
import hashlib
import time

import sys
import queue
import socket
import select
import random
import time
from enum import Enum

# UDP IP address and port number
UDP_IP_ADDRESS = "127.0.0.1"
UDP_PORT_NO = 8888 

# Packet size and buffer size
PACKET_SIZE = 1024
BUFFER_SIZE = 65535

snd_buf = queue.Queue()
rcv_buf = queue.Queue()


# Timeout for receiving ACK message
TIMEOUT = 1.0

#Open file to send
filename = "rfc.txt"  # Replace with the name of the file you want to send
file_size = os.path.getsize(filename)
print(f"File size : {file_size}")

# Initialize the sequence number, packet count, and window size
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
udp_socket.bind((UDP_IP_ADDRESS, UDP_PORT_NO))
udp_socket.settimeout(TIMEOUT)

class rdp_sender:
    def __init__(self):
        self.sequence_number = 0
        self.packet_count = 0
        self.packets = []
        self.window_size = 1
        self.max_window_size = 5 


    def send_data(self):
        time.sleep(1)
        with open(filename, "rb") as file:
            #Socket creation and set the timeout

            #Loop to Send the file in self.packets
            while True:
                # Check if the window is full
                #print(self.packet_count)
                #print(self.sequence_number )
                #print(self.window_size)
                if self.packet_count - self.sequence_number >= self.window_size:
                    try:
                        # Wait for ACK message from the server to move the window forward
                        ack, server_address = udp_socket.recvfrom(BUFFER_SIZE)
                        print("ACK-----------------{}".format(ack.decode('utf-8') ))
                        ack_number = int(ack.decode('utf-8'))
                        print(f"Acknowledgement : {ack_number}")
                        if ack_number >= self.sequence_number:
                            # Update the window size dynamically based on the ACK received
                            self.window_size = min(self.max_window_size, ack_number - self.sequence_number + 1)
                            self.sequence_number = ack_number + 1
                            print(f"Sequence No : {self.sequence_number}")
                    except socket.timeout:
                        # Timeout occurred, resend the self.packets in the current window
                        print("Timeout occurred, resending self.packets in the current window")
                        for i in range(self.sequence_number, self.packet_count):
                            udp_socket.sendto(self.packets[i].encode('utf-8'), (UDP_IP_ADDRESS, UDP_PORT_NO))

                # Read a chunk of data from the file
                data = file.read(PACKET_SIZE)
                if not data:
                    break

                # Create the packet with header and payload
                header = str(self.packet_count).zfill(4)
                checksum = hashlib.md5(data).hexdigest()
                packet = header + checksum + data.decode('utf-8')

                # Send the packet to the receiver and add it to the window
                udp_socket.sendto(packet.encode('utf-8'), (UDP_IP_ADDRESS, UDP_PORT_NO))
                self.packets.append(packet)

                # Increment the packet count
                self.packet_count += 1
                print(f"Packet No  {self.packet_count}")

            # Wait for all self.packets to be acknowledged
            while self.sequence_number < self.packet_count:
                try:
                    # Wait for ACK message from the receiver to move the window forward
                    ack, server_address = udp_socket.recvfrom(BUFFER_SIZE)
                    ack_number = int(ack.decode('utf-8'))
                    print(f"Acknowledgement : {ack_number}")
                    if ack_number >= self.sequence_number:
                        # Update the window size dynamically based on the ACK received
                        self.window_size = min(self.max_window_size, ack_number - self.sequence_number + 1)
                        self.sequence_number = ack_number + 1
                        print(f"Sequence No : {self.sequence_number}")
                except socket.timeout:
                    # Timeout occurred, resend the self.packets in the current window
                    print("Timeout occurred, resending self.packets in the current window")
                    for i in range(self.sequence_number, self.packet_count):
                        udp_socket.sendto(self.packets[i], (UDP_IP_ADDRESS, UDP_PORT_NO))

        #Empty Packet to show end of file
        header = str(self.packet_count).zfill(4)
        checksum = hashlib.md5(b"").hexdigest()
        packet = header + checksum
        udp_socket.sendto(packet.encode('utf-8'), (UDP_IP_ADDRESS, UDP_PORT_NO))

        # Print the number of self.packets sent
        print(f"Sent {self.packet_count} self.packets")

        # Close the socket
        udp_socket.close()

class rdp_receiver:
    def read_data(self, packet):
        time.sleep(1)
        filename = "received_file.txt" 
        with open(filename, "w") as file:
            # Create a UDP socket

            # Initialize the expected sequence number
            expected_sequence_number = 0

            while True:
                # Extract the header, checksum, and payload from the packet
                header = packet[:4].decode('utf-8')
                checksum = packet[4:36].decode('utf-8')
                payload = packet[36:]

                # Check if the sequence number is as expected
                if int(header) != expected_sequence_number:
                    # If the sequence number is incorrect, request the sender to resend the packet
                    print("Sequence no is incorrect, request resend ")

                    udp_socket.sendto(header.encode('utf-8'), client_address)

                    continue

                # Write the payload to the file
                #print(f"Payload : {payload.decode('utf-8')}")
                payload = packet[36:].decode('utf-8')
                file.write(payload)

                # Send ACK message to the client
                udp_socket.sendto(header.encode('utf-8'), client_address)

                # Increment the expected sequence number
                expected_sequence_number += 1

                # If an empty packet is received, the file transfer is complete
                if not payload:
                    print("File has received completely")
                    break

            # Close the socket
            udp_socket.close()

            # Print the size of the received file
            received_file_size = os.path.getsize(filename)
            print(f"Received file size: {received_file_size} bytes")


def main():
    receiver = rdp_receiver()
    sender = rdp_sender()


    sender.send_data()
    receiver.read_data()
# Main loop
    while True:
        readable, writable, _ = select.select([udp_socket], [udp_sock], [], 1)

        if udp_socket in readable:
            message, addr = udp_socket.recvfrom(1024)
            if message.decode().startswith("ACK"):
                rdp_sender.rcv_ack(message)
            else: 
                rdp_receiver.rcv_data(message)

        if udp_socket in writable:

            try:
                msg = snd_buf.get_nowait()
            except queue.Empty:
                break

            else:
                bytes_sent = udp_socket.sendto(msg, (ip, port))


if __name__ == "__main__":
    main()

