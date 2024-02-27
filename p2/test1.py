# RDP Sender Class
class Rdp_sender:
    MAX_PAYLOAD = 1024  # Maximum payload size for RDP

    def __init__(self, udp_sock, dest_ip, dest_port, file_path):
        self.udp_sock = udp_sock
        self.dest_ip = dest_ip
        self.dest_port = dest_port
        self.file_path = file_path
        self.state = State.CLOSED
        self.snd_buf = queue.Queue()
        self.snd_nxt = 0  # Next byte to send
        self.snd_una = 0  # Oldest unacknowledged byte

    def send_file(self):
        with open(self.file_path, 'rb') as file:
            while True:
                chunk = file.read(self.MAX_PAYLOAD)
                if not chunk:
                    break
                self.snd_buf.put((self.snd_nxt, chunk))
                self.snd_nxt += len(chunk)

    def send_next(self):
        if not self.snd_buf.empty() and self.state == State.OPEN:
            seq, chunk = self.snd_buf.get()
            packet = f'DAT\nSequence: {seq}\nLength: {len(chunk)}\n\n'.encode() + chunk
            self.udp_sock.sendto(packet, (self.dest_ip, self.dest_port))

    # ... other methods ...

# RDP Receiver Class
class Rdp_receiver:
    def __init__(self, udp_sock, file_path):
        self.udp_sock = udp_sock
        self.file_path = file_path
        self.rcv_nxt = 0  # Next byte expected
        self.rcv_buf = {}  # Buffer to hold out-of-order packets

    def receive(self):
        packet, _ = self.udp_sock.recvfrom(2048)  # Buffer size larger than max payload
        header, payload = packet.split(b'\n\n', 1)
        headers = self.parse_headers(header)

        if headers['Sequence'] == self.rcv_nxt:
            self.write_payload(payload)
            self.rcv_nxt += len(payload)
            self.acknowledge(headers['Sequence'] + len(payload))
            self.check_buffer()
        else:
            self.rcv_buf[headers['Sequence']] = payload
            self.acknowledge(self.rcv_nxt)  # Send duplicate ACK

    def write_payload(self, payload):
        with open(self.file_path, 'ab') as file:
            file.write(payload)

    def acknowledge(self, seq):
        ack_packet = f'ACK\nAcknowledgment: {seq}\n\n'.encode()
        self.udp_sock.sendto(ack_packet, (self.dest_ip, self.dest_port))

    def check_buffer(self):
        while self.rcv_nxt in self.rcv_buf:
            payload = self.rcv_buf.pop(self.rcv_nxt)
            self.write_payload(payload)
            self.rcv_nxt += len(payload)

    def parse_headers(self, header_bytes):
        headers = {}
        header_lines = header_bytes.decode().split('\n')
        for line in header_lines:
            key, value = line.split(': ')
            headers[key] = int(value)
        return headers

    # ... other methods ...

# Driver Code
# Initialize UDP socket
ip = "localhost"
port = 8888
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.bind((ip, port))

# Instantiate sender and receiver
file_to_send = 'path/to/send_file'
file_to_write = 'path/to/receive_file'
rdp_sender = Rdp_sender(udp_sock, ip, port, file_to_send)
rdp_receiver = Rdp_receiver(udp_sock, file_to_write)

# Main loop
while True:
    readable, writable, exceptional = select.select([udp_sock], [udp_sock], [], 0.1)

    # Read from socket
    if udp_sock in readable:
        rdp_receiver.receive()

    # Write to socket
    if udp_sock in writable:
        rdp_sender.send_next()

    # Check if the file has been fully sent and acknowledged
    if rdp_sender.snd_una == rdp_sender.snd_nxt and rdp_sender.snd_buf.empty():
        break

# Close the socket
udp_sock.close()

