#!/usr/bin/env python3

import sys
import socket
import select
import queue
import re
import os
from datetime import datetime, timedelta
from time import gmtime, strftime

if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <ip_address> <port_number>")
    sys.exit(1)
else:
    _, ip_address, port_number = sys.argv
    port_number = int(port_number)  
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setblocking(0)
    server.bind((ip_address, port_number))
    server.listen(5)

code400 = "HTTP/1.0 400 Bad Request"
code404 = "HTTP/1.0 404 Not Found"
code200 = "HTTP/1.0 200 OK"

# Create TCP/IP socket

inputs = [server]   # Sockets from which we expect to read
outputs = []        # Sockets to which we expect to write
message_queues = {} # Outgoing message queues
last_activity = {}
request_buffer = {}


def handle_request(data, socket, ip, port):
    keep_alive = 0
    new_line = "\r\n"

    regex_400 = r"^(GET) (\/[^\s]+) (HTTP\/1\.0)" 
    match = re.match(regex_400, data)

    if not match:
        code = code400
        response = code400 + new_line + "Connection: close" + "\r\n\r\n"
        return response, code, keep_alive, ip, port
    else:
        re_det = r"^(.*?)\r?\n(.*?)\r?\n\r?\n"
        has_header = re.match(re_det, data)
        if  has_header:
            current_request = re.split(r"\r\n|\n", data)
            request_line = current_request[0]
            header = current_request[1]
            con_type = header.split()[1]
        else:
            con_type = "close"
            current_request = re.split(r"\r\n\r\n|\n\n", data)
            request_line = current_request[0]

        _, f, _ = request_line.split()
        file = f.strip("/")

        dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(dir,file)

        if not os.path.isfile(path):
            code = code404
            response = code404 + new_line + "Connection: " + con_type + "\r\n\r\n"
            if con_type == "keep-alive":
                keep_alive = 1
        else:
            code = code200
            with open(path, 'r') as file:
                buffer = file.read()
            response = code200 + new_line + "Connection: " + con_type + "\r\n\r\n" + buffer
            if con_type == "keep-alive":
                keep_alive = 1

        return response, code, keep_alive, ip, port

def close_socket(sock):
    if sock in inputs:
        inputs.remove(sock)
    if sock in outputs:
        outputs.remove(sock)
    sock.close()
    if sock in message_queues:
        del message_queues[sock]
    if sock in last_activity:
        del last_activity[sock]
    if sock in request_buffer:
        del request_buffer[sock]



# Main loop
while inputs:

    update_time = datetime.now()
    for sock in list(last_activity.keys()):
        if update_time - last_activity[sock] > timedelta(seconds=30):
            close_socket(sock)

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
            request_buffer[conn] = ''
        else:
            # A readable client socket has data
            data = s.recv(1024).decode()
            all_data= re.split(r"\r\n\r\n|\n\n", data)
            all_data = [item for item in all_data if item] #remove empty entries
            for this_data in all_data:
                if this_data:
                    last_activity[s] = datetime.now()
                    this_data = this_data + "\r\n\r\n"
                    message_queues[s].put(this_data)
                    if s not in outputs:
                        outputs.append(s)
                else:
                    # The connection has been closed
                    close_socket(s)

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
            f_msg = re.split(r"\r\n|\n", next_msg)[0]
            response, code, conn_type, f_ip, f_port = handle_request(msg, s, f_ip, f_port)
            s.send(response.encode())

            print(f"{current_time}: {f_ip}:{f_port} {f_msg}; {code} ")
            if conn_type == 0:
                close_socket(s)

    for s in exceptional:
        close_socket(s)
