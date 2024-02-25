#!/usr/bin/env python3
import socket
import select
import queue
import os
import re
from datetime import datetime, timedelta
from time import gmtime, strftime
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
        self.valid = True
        self.req = None

    def handle_request(self, message):
        new_line = "\r\n"
        request_lines = message.splitlines()

        if len(request_lines) < 1:
            self.response = code400 + new_line + "Connection: close" + new_line * 2
            self.con_type = "close"
            self.code = code400
            return self.response

        request_line = request_lines[0]
        self.req = request_line
        headers = request_lines[1:]

        parts = request_line.split()
        if len(parts) != 3:
            self.response = code400 + new_line + "Connection: close" + new_line * 2
            self.con_type = "close"
            self.code = code400
            return self.response

        command, path, version = parts
        if command != "GET" or not path.startswith("/") or version != "HTTP/1.0":
            self.response = code400 + new_line + "Connection: close" + new_line * 2
            headers[0] = "Connection: close"
            self.con_type = "close"
            self.code = code400
            return self.response

        for header in headers:
            if header.lower().startswith("connection:"):
                self.con_type = header.split(":")[1].strip().lower()
                break
            else:
                self.con_type = "close"
                break

        file_path = path.strip("/")
        if not os.path.isfile(file_path):
            self.response = code404 + new_line + "Connection: " + self.con_type + new_line * 2
            self.code = code404
            return self.response
        else:
            with open(file_path, 'r') as file:
                content = file.read()
            self.response = code200 + new_line + "Connection: " + self.con_type + new_line * 2 + content
            self.code = code200
            return self.response

    def get_con_type(self):
        return self.con_type

    def set_con_type(self, type):
        self.con_type = type


def close_socket(sock):
    if sock in inputs:
        inputs.remove(sock)
    if sock in outputs:
        outputs.remove(sock)
    sock.close()

connection = HTTP_handler()
while inputs:
    readable, writable, exceptional = select.select(inputs, outputs, inputs, 1)

    current_time = datetime.now()
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
            if message:
                request_message[s] += message
                last_activity[s] = datetime.now()
                while "\r\n\r\n" in request_message[s] or "\n\n" in request_message[s]:
                    delimiter = "\r\n\r\n" if "\r\n\r\n" in request_message[s] else "\n\n"
                    end_index = request_message[s].find(delimiter) + len(delimiter)
                    whole_message = request_message[s][:end_index]
                    request_message[s] = request_message[s][end_index:]
                    msg = connection.handle_request(whole_message)
                    keep_alive[s] = connection.get_con_type() == "keep-alive"
                    if s not in outputs:
                        outputs.append(s)

                    tm = strftime("%a %b %d %H:%M:%S %Z %Y")
                    f_ip = s.getpeername()[0]
                    f_port = s.getpeername()[1]
                    print(f"{tm}: {f_ip}:{f_port} {connection.req}; {connection.code} ")

                    if keep_alive[s]:
                        response_message[s].put(msg)
                    else:
                        response_message[s].put(msg)
                        break

    for s in writable:
        try:
            next_msg = response_message[s].get_nowait()
            
        except queue.Empty:
            outputs.remove(s)
            if not keep_alive[s]:
                close_socket(s)
                break

        else:
            s.send(next_msg.encode())


    for s in exceptional:
        close_socket(s)

    for sock in list(last_activity.keys()):
        if current_time - last_activity[sock] > timedelta(seconds=30):
            close_socket(sock)
            del last_activity[sock]

