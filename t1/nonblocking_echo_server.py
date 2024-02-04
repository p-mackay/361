'''
GET /small.html HTTP/1.0\r\nConnection: keep-alive\r\n\r\n
'''
#!/usr/bin/env python3

import socket
import select
import queue
import re
import os
from datetime import datetime, timedelta
from time import gmtime, strftime

response_400 = "HTTP/1.0 400 Bad Request\r\nConnection: close\r\n\r\n"
code400 = "HTTP/1.0 400 Bad Request"
code404 = "HTTP/1.0 404 Not Found"
code200 = "HTTP/1.0 200 OK"

# Create TCP/IP socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.setblocking(0)

#“python3 sws.py ip_address port_number
# Bind socket to address
server.bind(("", 9000))

# Start listening for incoming connections
server.listen(5)

inputs = [server]   # Sockets from which we expect to read
outputs = []        # Sockets to which we expect to write
message_queues = {} # Outgoing message queues
last_activity = {}



#HTTP/1.0 200 OK\r\nConnection: keep-alive\r\n\r\n
def handle_request(data, socket, ip, port):
    keep_alive = 0
    lnx = "\r\n"
    wds = "\r\n"
    
    re_det = r"^(.*?)\r\n(.*?)\r\n\r\n" 
    det = re.match(re_det, data)
    if  det:
        current_request = data.split('\r\n')
        request_line = current_request[0]
        header = current_request[1]
        con_type = header.split()[1]#.strip("\n")
    else:
        con_type = "close"
        current_request = data.split('\r\n\r\n')
        request_line = current_request[0]

    #f_header = request_line.strip("\r\n")
    method, f, version = request_line.split()
    file = f.strip("/")

    dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(dir,file)
    ## 400

    regex_400 = r"^(GET) (\/[^\s]+) (HTTP\/1\.0)" 
    match = re.match(regex_400, request_line)

    if not match:
        code = code400
        response = code400 + lnx + "Connection: close" +  "\r\n\r\n"
    elif not os.path.isfile(path):
        code = code404
        response = code404 + lnx + "Connection: " + con_type + "\r\n\r\n"
        if con_type == "keep-alive":
            keep_alive = 1
    else:
        code = code200
        with open(path, 'r') as file:
            buffer = file.read()

        file_content = buffer.strip("\r\n")
        response = code200 + lnx + "Connection: " + con_type + "\r\n\r\n" + buffer
        if con_type == "keep-alive":
            keep_alive = 1

    return response, code, keep_alive, ip, port


# Close a socket
def close_socket(s):
    if s in inputs:  inputs.remove(s)
    if s in outputs: outputs.remove(s)
    s.close()

    del message_queues[s]


# Main loop
while inputs:

    update_time = datetime.now()
    for sock in list(last_activity.keys()):
        if update_time - last_activity[sock] > timedelta(seconds=30):
            close_socket(sock)
            del last_activity[sock]

    # Wait for at least one of the sockets to be ready for processing
    readable, writable, exceptional = select.select(inputs, outputs, inputs,1)

    # Process the sockets

    for s in readable:
        if s is server:
            # A readable server socket is ready to accept a connection
            conn, addr = s.accept()
            conn.setblocking(0)
            inputs.append(conn)
            message_queues[conn] = queue.Queue()
            last_activity[conn] = datetime.now()
        else:
            # A readable client socket has data
            data = s.recv(1024).decode()
            all_data = data.split("\r\n\r\n")
            all_data = [item for item in all_data if item] #remove empty entries
            for this_data in all_data:
                if this_data:
                    last_activity[s] = datetime.now()
                    this_data = this_data + "\r\n\r\n"
                    this_data.encode()
                    message_queues[s].put(this_data)
                    if s not in outputs:
                        outputs.append(s)
                else:
                    # The connection has been closed
                    close_socket(s)
                    del last_activity[s]


    '''
    Format:
    ■
    time: client_ip:client_port request; response
    ○
    E.g.
    ■
    Wed Sep 15 21:44:35 PDT 2021: 192.168.1.100:54321 GET /sws.py HTTP/1.0; HTTP/1.0 200 OK
    '''
    for s in writable:
        try:
            next_msg = message_queues[s].get_nowait()
        except queue.Empty:
            # No messages, so stop checking for writability
            outputs.remove(s)
        else:
            current_time = strftime("%a %b %d %H:%M:%S %Z %Y")
            f_ip = conn.getpeername()[0]
            f_port = conn.getpeername()[1]
            msg = next_msg
            f_msg = msg
            f_msg = f_msg.split("\r\n")[0]
            response,code,conn_type, f_ip, f_port = handle_request(msg,s, f_ip, f_port)
            s.send(response.encode())

            print(f"{current_time}: {f_ip}:{f_port} {f_msg}; {code} ")
            if conn_type == 0:
                close_socket(s)
                del last_activity[s]


    for s in exceptional:
        close_socket(s)

