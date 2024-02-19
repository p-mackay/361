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
response_message = {} # Outgoing message queues
last_activity = {}
request_buffer = {}
request_message = {}
response_message = {}


class HTTP_handler:
    def __init__(self):
        self.keep_alive = 0
        self.response = None
        self.code = None
        self.ip = None
        self.port = None
        self.con_type = None

    def get_keep_alive(self):
        return self.keep_alive

    def get_response(self):
        return self.response

    def get_code(self):
        return self.code
    def get_con_type(self):
        return self.con_type

    def handle_request(self, message):
        self.keep_alive = 0
        new_line = "\r\n"

        regex_400 = r"^(GET) (\/[^\s]+) (HTTP\/1\.0)" 
        match = re.match(regex_400, message)

        if not match:
            self.code = code400
            self.response = code400 + new_line + "Connection: close" + "\r\n\r\n"
        else:
            re_det = r"^(.*?)\r?\n(.*?)\r?\n\r?\n"
            has_header = re.match(re_det, message)
            if  has_header:
                current_request = re.split(r"\r\n|\n", message)
                request_line = current_request[0]
                header = current_request[1]
                self.con_type = header.split()[1]
            else:
                self.con_type = "close"
                current_request = re.split(r"\r\n\r\n|\n\n", message)
                request_line = current_request[0]

            _, f, _ = request_line.split()
            file = f.strip("/")

            dir = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(dir,file)

            if not os.path.isfile(path):
                self.code = code404
                self.response = code404 + new_line + "Connection: " + self.con_type + "\r\n\r\n"
                if self.con_type == "keep-alive":
                    self.keep_alive = 1
            else:
                self.code = code200
                with open(path, 'r') as file:
                    buffer = file.read()
                self.response = code200 + new_line + "Connection: " + self.con_type + "\r\n\r\n" + buffer
                if self.con_type == "keep-alive":
                    self.keep_alive = 1

            return self.response, self.code, self.keep_alive

def close_socket(sock):
    if sock in inputs:
        inputs.remove(sock)
    if sock in outputs:
        outputs.remove(sock)
    sock.close()

connection = HTTP_handler()

buffer_data = b''
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
            response_message[conn] = queue.Queue()
            last_activity[conn] = datetime.now()
            request_buffer[conn] = ''
        else:
            # A readable client socket has message
            message = s.recv(1024).decode()
            if message:
                request_message[s] += message
                if message.endswith("\r\n\r\n") or  message.endswith("\n\n"):
                    whole_message = request_message[s]
                    outputs.append(s)
                    connection.handle_request(whole_message)
                    response_message[s].push(connection.get_response())
            else:
                close_socket(s)


    for s in writable:

        try:
            next_msg = response_message[s].get_nowait()
        except queue.Empty:
            # No messages, so stop checking for writability
            outputs.remove(s)
        else:
            current_time = strftime("%a %b %d %H:%M:%S %Z %Y")
            f_ip = s.getpeername()[0]
            f_port = s.getpeername()[1]
            msg = next_msg
            f_msg = re.split(r"\r\n|\n", next_msg)[0]
            s.send(next_msg.encode())

            print(f"{current_time}: {f_ip}:{f_port} {next_msg.decode()}; {connection.get_code()} ")
            if connection.get_con_type() == 0:
                close_socket(s)

    for s in exceptional:
        close_socket(s)
