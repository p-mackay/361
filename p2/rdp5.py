import socket
import select
import time
from enum import Enum

ip = "localhost"
port = 8888
timeout = 1

# Initialize UDP socket
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
udp_sock.bind((ip, port))

# Define states using the Enum class
class State(Enum):
    CLOSED = "closed"
    SYN_SENT = "syn_sent"
    OPEN = "open"
    FIN_SENT = "fin_sent"

# RDP Sender Class
class Rdp_sender:
    def __init__(self, udp_sock, dest_ip, dest_port):
        self.udp_sock = udp_sock
        self.dest_ip = dest_ip
        self.dest_port = dest_port
        self.state = State.CLOSED
        self.snd_buf = []
        self.snd_una = 0  # Oldest unacknowledged sequence number
        self.snd_nxt = 0  # Next sequence number to be sent
        self.snd_wnd = 0  # Send window size

    def open(self):
        if self.state == State.CLOSED:
            syn_packet = "SYN\nSequence: {}\n\n".format(self.snd_nxt).encode()
            self.snd_buf.append(syn_packet)
            self.state = State.SYN_SENT
            print("Sender: Sent SYN packet")

    def close(self):
        if self.state == State.OPEN:
            fin_packet = "FIN\nSequence: {}\n\n".format(self.snd_nxt).encode()
            self.snd_buf.append(fin_packet)
            self.state = State.FIN_SENT
            print("Sender: Sent FIN packet")

    def send_data(self, data):
        '''
        rdt_send(data)
            if(snd_nxt<snd_una+snd_wnd){
               sndpkt[snd_nxt]=make_pkt(snd_nxt,data)
               udt_send(sndpkt[snd_nxt])
               if(snd_una==snd_nxt)
                  start_timer
               snd_nxt++
               }
            else
               refuse_data(data)
        '''
        if self.state == State.OPEN:
            while self.snd_nxt < self.snd_una + self.snd_wnd and len(data) > 0:
                # Calculate the length of the data to send in this packet
                data_len = min(len(data), self.snd_wnd - (self.snd_nxt - self.snd_una))

                # Create the packet
                dat_packet = "DAT\nSequence: {}\nLength: {}\n\n{}".format(self.snd_nxt, data_len, data[:data_len].decode()).encode()
                self.snd_buf.append(dat_packet)

                # Update the sequence number and the remaining data
                self.snd_nxt += data_len
                data = data[data_len:]

                print("Sender: Sent data packet with sequence number {}".format(self.snd_nxt - data_len))

    def rcv_ack(self, packet):
        if self.state == State.OPEN:
            lines = packet.decode().split('\n')
            if lines[0] == "ACK":
                ack_num = int(lines[1].split(': ')[1])
                '''
                if self.state == State.OPEN:
                    if ack_num == self.last_ack_num:
                        self.duplicate_acks += 1
                        if self.duplicate_acks == 3:
                            # Fast retransmit
                            print("Sender: Three duplicate ACKs received, fast retransmit")
                            for seq in range(self.snd_una, self.snd_nxt):
                                self.resend_packet(seq)
                '''
                self.last_ack_num = ack_num
                self.duplicate_acks = 0
                if ack_num > self.snd_una:
                    self.snd_una = ack_num
                    self.send_data(b'')  # Call send to potentially send new data

        elif self.state == State.SYN_SENT and ack_num == self.snd_nxt + 1:
            self.state = State.OPEN
            print("Sender: Connection established")
        elif self.state == State.FIN_SENT and ack_num == self.snd_nxt + 1:
            self.state = State.CLOSED
            print("Sender: Connection closed")


    '''
    def resend_packet(self, seq):
        if seq in self.packet_history:
            packet = self.packet_history[seq]
            self.udp_sock.sendto(packet, (self.dest_ip, self.dest_port))
            print(f"Sender: Resent packet with sequence number {seq}")
    '''

    def getstate(self):
        return self.state

    def check_timeout(self):
        # Implement timeout and retransmission logic here
        pass

# RDP Receiver Class
class Rdp_receiver:
    def __init__(self, udp_sock):
        self.udp_sock = udp_sock
        self.state = State.CLOSED
        self.rcv_nxt = 0  # Next sequence number expected

    def rcv_data(self, packet):
        lines = packet.decode().split('\n')
        header = lines[0]
        if header == "SYN":
            seq_num = int(lines[1].split(': ')[1])
            self.state = State.OPEN
            self.rcv_nxt = seq_num + 1
            ack_packet = "ACK\nAcknowledgment: {}\n\n".format(self.rcv_nxt).encode()
            self.udp_sock.sendto(ack_packet, (ip, port))
            print("Receiver: Sent ACK for SYN")
        elif header == "FIN":
            seq_num = int(lines[1].split(': ')[1])
            self.state = State.CLOSED
            self.rcv_nxt = seq_num + 1
            ack_packet = "ACK\nAcknowledgment: {}\n\n".format(self.rcv_nxt).encode()
            self.udp_sock.sendto(ack_packet, (ip, port))
            print("Receiver: Sent ACK for FIN")
        elif header == "DAT":
            seq_num = int(lines[1].split(': ')[1])
            length = int(lines[2].split(': ')[1])
            data = '\n'.join(lines[4:])
            if seq_num == self.rcv_nxt:
                self.rcv_nxt += length
                print("Receiver: Received data:", data)
                ack_packet = "ACK\nAcknowledgment: {}\n\n".format(self.rcv_nxt).encode()
                self.udp_sock.sendto(ack_packet, (ip, port))

    def getstate(self):
        return self.state

# Instantiate sender and receiver
rdp_sender = Rdp_sender(udp_sock, ip, port)
rdp_receiver = Rdp_receiver(udp_sock)

rdp_sender.open()

data = [b'Hello', b'World']

# Main loop
while rdp_sender.getstate() != State.CLOSED or rdp_receiver.getstate() != State.CLOSED:
    readable, writable, exceptional = select.select([udp_sock], [udp_sock], [udp_sock], timeout)

    if udp_sock in readable:
        packet, _ = udp_sock.recvfrom(1024)
        rdp_receiver.rcv_data(packet)
        rdp_sender.rcv_ack(packet)

    if udp_sock in writable:
        print(rdp_sender.getstate())
        print(rdp_receiver.getstate())
        if rdp_sender.getstate() == State.OPEN:
            rdp_sender.send_data(data)
        elif rdp_sender.snd_buf:
            packet = rdp_sender.snd_buf.pop(0)
            udp_sock.sendto(packet, (ip, port))

    time.sleep(1)
    rdp_sender.check_timeout()

# Close the socket
udp_sock.close()

