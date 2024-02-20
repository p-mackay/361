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
keep_alive = {}

class HTTP_handler:
    def __init__(self):
        self.response = None
        self.code = None
        self.con_type = "close"

    def handle_request(self, message):
        new_line = "\r\n"
        request_lines = message.splitlines()

        if len(request_lines) < 1:
            return

        request_line = request_lines[0]
        headers = request_lines[1:]

        parts = request_line.split()
        if len(parts) != 3 or parts[0] != "GET" or not parts[1].startswith("/") or parts[2] != "HTTP/1.0":
            self.response = code400 + new_line + "Connection: close" + new_line * 2
            return

        self.con_type = "close"
        for header in headers:
            if header.lower().startswith("connection:"):
                self.con_type = header.split(":")[1].strip().lower()
                break

        file_path = parts[1].strip("/")
        if not os.path.isfile(file_path):
            self.response = code404 + new_line + "Connection: " + self.con_type + new_line * 2
        else:
            with open(file_path, 'r') as file:
                content = file.read()
            self.response = code200 + new_line + "Connection: " + self.con_type + new_line * 2 + content

def close_socket(sock):
    if sock in inputs:
        inputs.remove(sock)
    if sock in outputs:
        outputs.remove(sock)
    sock.close()

http_handlers = {}  # Dictionary to store HTTP_handler objects for each connection

while inputs:
    readable, writable, exceptional = select.select(inputs, outputs, inputs, 1)

    for s in readable:
        if s is server:
            conn, addr = s.accept()
            conn.setblocking(0)
            inputs.append(conn)
            response_message[conn] = queue.Queue()
            last_activity[conn] = datetime.now()
            request_message[conn] = ''
            keep_alive[conn] = True
            http_handlers[conn] = HTTP_handler()
        else:
            message = s.recv(1024).decode()
            if message:
                request_message[s] += message
                last_activity[s] = datetime.now()
                if "\r\n\r\n" in request_message[s] or "\n\n" in request_message[s]:
                    while "\r\n\r\n" in request_message[s] or "\n\n" in request_message[s]:
                        delimiter = "\r\n\r\n" if "\r\n\r\n" in request_message[s] else "\n\n"
                        end_index = request_message[s].find(delimiter) + len(delimiter)
                        whole_message = request_message[s][:end_index]
                        request_message[s] = request_message[s][end_index:]
                        http_handlers[s].handle_request(whole_message)
                        response_message[s].put(http_handlers[s].response)
                        keep_alive[s] = http_handlers[s].con_type == "keep-alive"
                        if s not in outputs:
                            outputs.append(s)
            else:
                if not keep_alive[s]:
                    close_socket(s)

    for s in writable:
        try:
            next_msg = response_message[s].get_nowait()
        except queue.Empty:
            outputs.remove(s)
            if http_handlers[s].code == code400:
                close_socket(s)  # Close immediately for bad requests
        else:
            s.send(next_msg.encode())
            last_activity[s] = datetime.now()
            if not keep_alive[s]:
                close_socket(s)  # Close immediately after sending if not keep-alive

    for s in exceptional:
        close_socket(s)

    current_time = datetime.now()
    for sock in list(last_activity.keys()):
        if current_time - last_activity[sock] > timedelta(seconds=30):
            close_socket(sock)  # Close inactive connections
