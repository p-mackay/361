#!/usr/bin/env python3 

def main():
# Initial receive buffer
    rcv_buf = {
        1: {"command": "DAT", "sequence": 1, "payload": "Hello"},
        3: {"command": "DAT", "sequence": 3, "payload": "Data"}
    }

# Adding a new packet
    new_packet = {"command": "DAT", "sequence": 4, "payload": "World"}
    rcv_buf[new_packet["sequence"]] = new_packet

# Removing a packet
    '''
    sequence_to_remove = 1
    del rcv_buf[sequence_to_remove]
    '''

# Receive buffer after adding and removing packets
    print(rcv_buf)

if __name__ == "__main__":

    main()

