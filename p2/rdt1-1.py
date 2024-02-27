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
'''
look at page 280
we are using go-back-n plus 
fast re-transmit (if 3 duplicate ACK's received -> resend unACKed packets)
'''
'''
Host A in turn keeps track of two variables, LastByteSent and Last-
ByteAcked, which have obvious meanings. Note that the difference between these 
two variables, LastByteSent – LastByteAcked, is the amount of unac-
knowledged data that A has sent into the connection. By keeping the amount of 
unacknowledged data less than the value of rwnd, Host A is assured that it is not
overflowing the receive buffer at Host B. Thus, Host A makes sure throughout the 
connection’s life that
the sender has the following states(closed -> syn_sent -> open -> fin_sent -> closed)
    LastByteSent – LastByteAcked <= rwnd
    LastByteSent
    LastByteAcked,
'''

snd_buf = queue.Queue() 
rcv_buf = queue.Queue() 

class State(Enum):
    CLOSED = "closed"
    SYN_SENT = "syn_sent"
    OPEN = "open"
    FIN_SENT = "fin_sent"

#----------------------------------------------------
class Rdp_sender:
    def __init__(self, udp_sock):
        self.udp_sock = udp_sock
        self.snd_una = 0 # oldest unacknowledged sequence number
        self.snd_nxt = 0 # next sequence number to be sent
        self.snd_wnd = 0 # The "usable window" is: U = SND.UNA + SND.WND - SND.NXT
        self.snd_seq = 0 # first sequence number of a segment
        self.snd_len = 0 # the number of octets occupied by the data in the segment (counting SYN and FIN)

        self.seg_ack = 0 # acknowledgment from the receiving TCP peer (next sequence number expected by the receiving TCP peer)
        self.state = State.CLOSED

    def open(self):
        if self.state == State.CLOSED:
            syn_packet = "SYN\nSequence: {}\nLength: {}\n\n".format(self.snd_nxt, self.snd_len).encode()
            snd_buf.put(syn_packet)

            self.state = State.SYN_SENT
            print("Sender: Sent SYN packet")

    def rdp_send(self, message):
        if self.state == State.SYN_SENT:
            syn_packet = "DAT\nSequence: {}\nLength: {}\n\n".format(self.snd_nxt, self.snd_len).encode()
            snd_buf.put(syn_packet)
        if self.state == State.OPEN:
            if (self.snd_nxt < self.snd_una + self.snd_wnd):
                dat_packet = "DAT\nSequence: {}\nLength: {}\n\n".format(self.snd_nxt, self.snd_len).encode()
                snd_buf.put(dat_packet)


    def rcv_ack(self, message):
        if self.state == State.SYN_SENT:
            parts = message.split('\n')
            if parts[0] == "ACK":
                self.seg_ack = int(parts[1].split(': ')[1])
                self.snd_wnd = int(parts[2].split(': ')[1])
                self.snd_una = self.seg_ack + 1
                self.rdp_send(message)



            

    def getstate(self):
        return self.state

    def check_timeout(self):
        # Implement timeout and retransmission logic here
        pass



# RDP Receiver Class
#----------------------------------------------------
class Rdp_receiver:
    def __init__(self, udp_sock):
        self.udp_sock = udp_sock
        self.rcv_nxt = 0# next sequence number expected on an incoming segment, and is the left or lower edge of the receive window
        self.rcv_wnd = 2048 
        self.seg_seq = 0# first sequence number occupied by the incoming segment
        self.seg_ack = 0
        self.snd_len = 0
        self.state = State.CLOSED

        #RCV.NXT+RCV.WND-1 = last sequence number expected on an incoming segment, and is the right or upper edge of the receive window
        #SEG.SEQ+SEG.LEN-1 = last sequence number occupied by the incoming segment 
        #A segment is judged to occupy a portion of valid receive sequence space if
        #RCV.NXT =< SEG.SEQ < RCV.NXT+RCV.WND
        #or
        #RCV.NXT =< SEG.SEQ+SEG.LEN-1 < RCV.NXT+RCV.WND


    def rcv_data(self, message):
        '''
        if self.state == open:
            if data.seq < rcv_exp:
            drop packet
            if data.seq > rcv_exp:
            put the rdp with seq into a buffer data_buf
            return an RDP packet with duplicate ack
            if data.seq == rcv_exp:
            check data_buf and update rcv_exp
            return an ack RDP packet
        '''
        if self.state == State.CLOSED:
            lines = message.decode().split('\n')
            header = lines[0]
            if header == "SYN":
                seq_num = int(lines[1].split(': ')[1])
                self.state = State.OPEN
                self.rcv_nxt = seq_num + 1
                ack_packet = "ACK\nAcknowledgment: {}\nWindow: {}\n\n".format(self.rcv_nxt, self.rcv_wnd).encode()
                print("Receiver: Sent ACK for SYN")
                rcv_buf.put(ack_packet)





# Application layer
'''

'''
#----------------------------------------------------
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


    if udp_sock in writable:


# Close the socket
udp_sock.close()
