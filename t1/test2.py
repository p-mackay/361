#!/usr/bin/env python3

import socket
import select
import queue
import os

HOST, PORT = 'localhost', 9000
FILE_DIR = os.path.dirname(os.path.abspath(__file__))

# Create TCP/IP socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.setblocking(0)  # Non-blocking mode
server.bind((HOST, PORT))
server.listen(5)

inputs = [server]  # Sockets from which we expect to read
outputs = []  # Sockets to which we expect to write
message_queues = {}  # Outgoing message queues
connection_headers = {}  # Track connection headers for persistence

def handle_client_connection(client_socket):
    data_buffer = ""
    while True:
        data = client_socket.recv(1024).decode()
        if not data:
            break  # Connection closed by client
        data_buffer += data
        # Check if we have at least one complete request (ending with double CRLF)
        while "\r\n\r\n" in data_buffer:
            request, data_buffer = data_buffer.split("\r\n\r\n", 1)
            request += "\r\n\r\n"  # Add the separator back for processing
            handle_connection(request, client_socket)
        # Handle keep-alive or close the connection based on the logic here

def handle_connection(client_socket, request_data):

    try:
        lines = request_data.split("\r\n")
        request_line = lines[0]
        headers = {line.split(": ")[0].lower(): line.split(": ")[1] for line in lines[1:] if ": " in line}
        
        method, path, version = request_line.split()
        if method != "GET" or version != "HTTP/1.0":
            raise ValueError("Unsupported method or version")
        filepath = os.path.join(FILE_DIR, path.lstrip("/"))
        if not os.path.isfile(filepath):
            raise FileNotFoundError

        with open(filepath, 'rb') as file:
            body = file.read()
            response = f"HTTP/1.0 200 OK\r\nContent-Length: {len(body)}\r\n\r\n".encode() + body

        # Decide if we keep the connection open
        if headers.get("connection") == "keep-alive":
            connection_headers[client_socket] = "keep-alive"
        else:
            connection_headers[client_socket] = "close"

    except (ValueError, FileNotFoundError):
        response = "HTTP/1.0 404 Not Found\r\n\r\n" if method == "GET" else "HTTP/1.0 400 Bad Request\r\n\r\n"
        response = response.encode()
        connection_headers[client_socket] = "close"
    
    except KeyError:
        response = "HTTP/1.0 400 Bad Request\r\n\r\n".encode()
    
    # Queueing the response message to be sent
    message_queues[client_socket].put(response)
    if client_socket not in outputs:
        outputs.append(client_socket)

def close_socket(s):
    if s in outputs:
        outputs.remove(s)
    if s in inputs:
        inputs.remove(s)
    if s in message_queues:
        del message_queues[s]
    if s in connection_headers:
        del connection_headers[s]
    s.close()

while inputs:
    readable, writable, exceptional = select.select(inputs, outputs, inputs)

    for s in readable:
        if s is server:
            conn, addr = s.accept()
            conn.setblocking(0)
            inputs.append(conn)
            message_queues[conn] = queue.Queue()
        else:
            data = s.recv(1024)
            if data:
                message_queues[s].put(data)
                # Process the first complete request from the queue
                if s in message_queues and not message_queues[s].empty():
                    request_data = message_queues[s].get()
                    handle_connection(s, request_data.decode())
            else:
                close_socket(s)

    for s in writable:
        if s in message_queues and not message_queues[s].empty():
            next_msg = message_queues[s].get_nowait()
            s.send(next_msg)
            if connection_headers.get(s) != "keep-alive":
                close_socket(s)

    for s in exceptional:
        close_socket(s)

