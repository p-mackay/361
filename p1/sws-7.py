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
        self.valid = True  # Added to track if the request is valid

    def handle_request(self, message):
        new_line = "\r\n"
        request_lines = message.splitlines()

        if len(request_lines) < 1:
            self.valid = False  # Mark request as invalid
            return code400 + new_line + "Connection: close" + new_line * 2

        request_line = request_lines[0]
        headers = request_lines[1:]

        parts = request_line.split()
        if len(parts) != 3:
            self.valid = False  # Mark request as invalid
            return code400 + new_line + "Connection: close" + new_line * 2

        command, path, version = parts
        if command != "GET" or not path.startswith("/") or version != "HTTP/1.0":
            self.valid = False  # Mark request as invalid
            return code400 + new_line + "Connection: close" + new_line * 2

        self.con_type = "close"
        for header in headers:
            if header.lower().startswith("connection:"):
                self.con_type = header.split(":")[1].strip().lower()
                break

        file_path = path.strip("/")
        if not os.path.isfile(file_path):
            return code404 + new_line + "Connection: " + self.con_type + new_line * 2
        else:
            with open(file_path, 'r') as file:
                content = file.read()
            return code200 + new_line + "Connection: " + self.con_type + new_line * 2 + content

def close_socket(sock):
    if sock in inputs:
        inputs.remove(sock)
    if sock in outputs:
        outputs.remove(sock)
    sock.close()

handler = HTTP_handler()
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
        else:
            message = s.recv(1024).decode()
            print("hello")
            if message:
                request_message[s] += message
                last_activity[s] = datetime.now()
                while "\r\n\r\n" in request_message[s] or "\n\n" in request_message[s]:
                    delimiter = "\r\n\r\n" if "\r\n\r\n" in request_message[s] else "\n\n"
                    end_index = request_message[s].find(delimiter) + len(delimiter)
                    whole_message = request_message[s][:end_index]
                    request_message[s] = request_message[s][end_index:]
                    msg = handler.handle_request(whole_message)
                    keep_alive[s] = handler.con_type == "keep-alive" and handler.valid  # Only keep alive if valid and keep-alive
                    if keep_alive[s]:
                        response_message[s].put(msg)
                    else:
                        response_message[s].put(msg)
                        break

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
            if not keep_alive[s]:
                close_socket(s)
        else:
            s.send(next_msg.encode())
            print("world")

    for s in exceptional:
        close_socket(s)

    current_time = datetime.now()
    for sock in list(last_activity.keys()):
        if current_time - last_activity[sock] > timedelta(seconds=30):
            close_socket(sock)
