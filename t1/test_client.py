#!/usr/bin/env python3

import socket
import sys

def send_request(host, port, path, keep_alive=False):
    connection_type = "keep-alive" if keep_alive else "close"
    request = f"GET {path} HTTP/1.0\r\nHost: {host}\r\nConnection: {connection_type}\r\n\r\n"

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.send(request.encode())

        response = b""
        while True:
            part = s.recv(4096)
            response += part
            if len(part) < 4096:
                break

    return response.decode()

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 test_client.py <host> <port> <path> [<keep-alive>]")
    else:
        host = sys.argv[1]
        port = int(sys.argv[2])
        path = sys.argv[3]
        keep_alive = len(sys.argv) >= 5 and sys.argv[4].lower() == "keep-alive"
        response = send_request(host, port, path, keep_alive)
        response = send_request(host, port, path, keep_alive)
        response = send_request(host, port, path, keep_alive)
        print(response)

