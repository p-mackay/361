#!/usr/bin/env python3

import socket
import select
import queue
import time
import re
import os

FILE_DIR = '/var/www/html'

def handle_request(data, client_socket):
    lines = data.decode().splitlines()
    first_line = lines[0]
    method, path, _ = re.split(r'\s+', first_line)
    
    if method == "GET":
        filepath = os.path.join(FILE_DIR, path.lstrip("/"))
        if os.path.exists(filepath) and os.path.isfile(filepath):
            file_size = os.path.getsize(filepath)
            file_extension = os.path.splitext(filepath)[1]
            content_type = get_content_type(file_extension)

            # Reading the file content
            with open(filepath, 'rb') as f:
                file_content = f.read()

            # Building the response header
            headers = {
                "Content-Type": content_type,
                "Content-Length": str(file_size),
                "Connection": "close"  # Adjust as needed for keep-alive
            }

            send_response(client_socket, "HTTP/1.0 200 OK", headers, file_content)
        else:
            send_response(client_socket, "HTTP/1.0 404 Not Found", {"Connection": "close"})
    else:
        send_response(client_socket, "HTTP/1.0 400 Bad Request", {"Connection": "close"})

def send_response(client_socket, status_line, headers=None, body=None):
    response_parts = [status_line + "\r\n"]
    if headers:
        for header, value in headers.items():
            response_parts.append(f"{header}: {value}\r\n")
    header_str = "".join(response_parts) + "\r\n"  # Ensure this ends with double CRLF
    response_header = header_str.encode()  # Encode the headers to bytes
    
    # Concatenate headers and body
    if body is not None:  # If there's a body, it's already in bytes
        response = response_header + body
    else:
        response = response_header

    client_socket.sendall(response)


def get_content_type(extension):
    """Simple function to return the content type based on file extension."""
    if extension in ['.html', '.htm']:
        return "text/html"
    elif extension == '.css':
        return "text/css"
    elif extension == '.js':
        return "application/javascript"
    elif extension == '.jpg' or extension == '.jpeg':
        return "image/jpeg"
    elif extension == '.png':
        return "image/png"
    elif extension == '.gif':
        return "image/gif"
    elif extension == '.txt':
        return "text/plain"
    else:
        return "application/octet-stream"  # Default for unknown types


def handle_404(client_socket):
    response = b"HTTP/1.0 404 Not Found\r\n\r\n"
    client_socket.send(response)

def handle_400(client_socket):
    response = b"HTTP/1.0 400 Bad Request\r\n\r\n"
    client_socket.send(response)


# Create TCP/IP socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.setblocking(False)

# Bind socket to address
server.bind(("", 9000))

# Start listening for incoming connections
server.listen(5)

inputs = [server]   # Sockets from which we expect to read
outputs = []        # Sockets to which we expect to write
message_queues = {} # Outgoing message queues

# Close a socket
def close_socket(s):
    if s in inputs:  inputs.remove(s)
    if s in outputs: outputs.remove(s)
    s.close()

    del message_queues[s]

# Main loop
while inputs:
    readable, writable, exceptional = select.select(inputs, [], inputs)

    for s in readable:
        if s is server:
            # A readable server socket is ready to accept a connection
            conn, addr = s.accept()
            conn.setblocking(False)
            inputs.append(conn)
        else:
            # A readable client socket has data
            data = s.recv(1024)
            if data:
                # Process the request immediately
                handle_request(data, s)
                # Close the connection after sending the response
                close_socket(s)
            else:
                # No data, close the connection
                close_socket(s)

    for s in exceptional:
        close_socket(s)
