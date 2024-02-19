import socket
import select
import queue
import os
import re
from datetime import datetime, timedelta
import sys

if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <ip_address> <port_number>")
    sys.exit(1)

ip_address, port_number = sys.argv[1], int(sys.argv[2])
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.setblocking(0)
server.bind((ip_address, port_number))
server.listen(5)

code400 = "HTTP/1.0 400 Bad Request"
code404 = "HTTP/1.0 404 Not Found"
code200 = "HTTP/1.0 200 OK"

inputs = [server]
outputs = []
response_message = {}
last_activity = {}
request_message = {}


class HTTP_handler:
    def __init__(self):
        self.keep_alive = False
        self.response = None
        self.code = None
        self.con_type = "close"

    def handle_request(self, message):
        new_line = "\r\n"
        request_lines = message.splitlines()
        
        # Ensure that the request has at least one line (the request line)
        if len(request_lines) < 1:
            return

        request_line = request_lines[0]
        headers = request_lines[1:]

        # Parse the request line
        parts = request_line.split()
        if len(parts) != 3:
            self.response = code400 + new_line + "Connection: close" + new_line * 2
            return

        method, path, version = parts
        if method != "GET":
            self.response = code400 + new_line + "Connection: close" + new_line * 2
            return

        self.con_type = "close"  # Default to close
        self.keep_alive = False  # Default to not keeping the connection alive
        for header in headers:
            if header.lower().startswith("connection:"):
                self.con_type = header.split(":")[1].strip().lower()
                if self.con_type == "keep-alive":
                    self.keep_alive = True  # Set the keep_alive flag
                break

        # Find the requested file
        file_path = path.strip("/")
        if not os.path.isfile(file_path):
            self.response = code404 + new_line + "Connection: " + self.con_type + new_line * 2
        else:
            with open(file_path, 'r') as file:
                content = file.read()
            self.response = code200 + new_line + "Connection: " + self.con_type + new_line * 2 + content

def close_socket(sock):
    inputs.remove(sock)
    if sock in outputs:
        outputs.remove(sock)
    sock.close()

connection = HTTP_handler()

while inputs:
    readable, writable, exceptional = select.select(inputs, outputs, inputs, 1)

    current_time = datetime.now()
    for sock in list(last_activity.keys()):
        if current_time - last_activity[sock] > timedelta(seconds=30):
            close_socket(sock)
            break

    for s in readable:
        if s is server:
            conn, addr = s.accept()
            conn.setblocking(0)
            inputs.append(conn)
            response_message[conn] = queue.Queue()
            last_activity[conn] = datetime.now()
            request_message[conn] = ''
        else:
            message = s.recv(1024).decode()
            if message:
                request_message[s] += message
                last_activity[s] = datetime.now()  # Update last activity time
                if "\r\n\r\n" in request_message[s] or "\n\n" in request_message[s]:
                    whole_message = request_message[s]
                    outputs.append(s)
                    connection.handle_request(whole_message)
                    response_message[s].put(connection.response)
                    request_message[s] = ''
            else:
                close_socket(s)

    for s in writable:
        try:
            next_msg = response_message[s].get_nowait()
        except queue.Empty:
            outputs.remove(s)
        else:
            s.send(next_msg.encode())
            last_activity[s] = datetime.now()  # Update last activity time
            if connection.con_type == "close":
                close_socket(s)

    for s in exceptional:
        close_socket(s)

