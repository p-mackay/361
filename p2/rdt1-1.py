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

snd_buf = {}
rcv_buf = {}
class State(Enum):
    CLOSED = "closed"
    SYN_SENT = "syn_sent"
    OPEN = "open"
    FIN_SENT = "fin_sent"

#----------------------------------------------------
class Rdp_sender:
    def __init__(self, udp_sock):
        self.udp_sock = udp_sock
        self.snd_una = None # oldest unacknowledged sequence number
        self.snd_nxt = None # next sequence number to be sent
        self.snd_wnd = None # The "usable window" is: U = SND.UNA + SND.WND - SND.NXT
        self.seg_ack = None # acknowledgment from the receiving TCP peer (next sequence number expected by the receiving TCP peer)
        self.seg_seq = None # first sequence number of a segment
        self.seg_len = None # the number of octets occupied by the data in the segment (counting SYN and FIN)
        self.state = State.CLOSED

    def open(self):
        if self.state == State.CLOSED:
            syn_packet = "SYN\nSequence: {}\nLength: {}\n\n".format(self.snd_nxt, self.seg_len).encode()

            self.state = State.SYN_SENT
            print("Sender: Sent SYN packet")

    def rdp_send(self, data):
        packet = b'DAT' + data
        self.udp_sock.sendto(packet, (ip, port))
        print("in sender")
        print(f"Sender: Sent {packet}")


    def rcv_ack(self):
        '''
        def rcv_ack(self):
        if self.state == syn_sent:
        if ack# is correct:
        self.state = open
        if self.state == open:
        if three duplicate received:
# rewrite the rdp packets into snd_buf
        if ack# is correct:
            # move the sliding window
                        # write the available window of DAT rdp packets into snd_buf 
            # if all data has been sent, call self.close()
        if self.state == fin_sent:
        if ack# is correct:
        self.state = close
        '''

    def getstate(self):
        return self.state

    def check_timeout(self):
        # Implement timeout and retransmission logic here
        pass



# RDP Receiver Class
'''
Arrival of in-order segment with expected sequence number. All  
data up to expected sequence number already acknowledged.
Delayed ACK. Wait up to 500 msec for arrival of another in-order segment.  
If next in-order segment does not arrive in this interval, send an ACK.
Arrival of in-order segment with expected sequence number. One  
other in-order segment waiting for ACK transmission.
One Immediately send single cumulative ACK, ACKing both in-order segments.
Arrival of out-of-order segment with higher-than-expected sequence 
number. Gap detected.
Immediately send duplicate ACK, indicating sequence number of next 
expected byte (which is the lower end of the gap).
Arrival of segment that partially or completely fills in gap in  
received data.
Immediately send ACK, provided that segment starts at the lower end  
of gap.
LastByteRead: the number of the last byte in the data stream read from the 
buffer by the application process in B
• LastByteRcvd: the number of the last byte in the data stream that has arrived 
from the network and has been placed in the receive buffer at B
Because TCP is not permitted to overflow the allocated buffer, we must have
LastByteRcvd – LastByteRead … RcvBuffer
The receive window, denoted rwnd is set to the amount of spare room in the buffer:
rwnd = RcvBuffer – [LastByteRcvd – LastByteRead]
Because the spare room changes with time, rwnd is dynamic. The variable rwnd is 
illustrated in Figure 3.38.
How does the connection use the variable rwnd to provide the flow-control 
service? Host B tells Host A how much spare room it has in the connection buffer 
by placing its current value of rwnd in the receive window field of every segment it 
sends to A. Initially, Host B sets rwnd = RcvBuffer. Note that to pull this off, 
Host B must keep track of several connection-specific variables.
    LastByteRead
    LastByteRcvd
    LastByteRcvd – LastByteRead <= RcvBuffer
    rwnd = RcvBuffer – [LastByteRcvd – LastByteRead]
'''
#----------------------------------------------------
class Rdp_receiver:
    def __init__(self, udp_sock):
        self.udp_sock = udp_sock
        self.rcv_nxt = None# next sequence number expected on an incoming segment, and is the left or lower edge of the receive window
        self.rcv_wnd = None
        self.seg_seq = None# first sequence number occupied by the incoming segment
        self.seg_ack = None
        self.seg_len = None

        #RCV.NXT+RCV.WND-1 = last sequence number expected on an incoming segment, and is the right or upper edge of the receive window
        #SEG.SEQ+SEG.LEN-1 = last sequence number occupied by the incoming segment 
        #A segment is judged to occupy a portion of valid receive sequence space if
        #RCV.NXT =< SEG.SEQ < RCV.NXT+RCV.WND
        #or
        #RCV.NXT =< SEG.SEQ+SEG.LEN-1 < RCV.NXT+RCV.WND


    def rdp_rcv(self):
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
        packet, addr = self.udp_sock.recvfrom(1024)
        print("in receiver")
        if packet.startswith(b'DAT'):
            data = packet
            print(f"Receiver: Received {data}")
            return data
        return None

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
