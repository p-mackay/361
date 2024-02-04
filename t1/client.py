#!/usr/bin/env python3

import socket
import sys

def send_request(host, port, path, keep_alive):
    # Determine the connection type based on the keep_alive flag
    if keep_alive:
        connection_type = "keep-alive"
    else:
        connection_type = "close"
    
    # Construct the HTTP request string
    request = "GET " + path + " HTTP/1.0\r\nHost: " + host + "\r\nConnection: " + connection_type + "\r\n\r\n"
    
    # Create a new socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))  # Connect to the server
    s.send(request.encode())  # Send the constructed request
    
    # Receive the response
    response = b""
    while True:
        part = s.recv(4096)
        response += part
        if len(part) < 4096:
            break
    
    s.close()  # Close the socket
    return response.decode()

def main():
    if len(sys.argv) < 4:
        print("Usage: python3 test_client.py <host> <port> <path> [<keep-alive>]")
        return

    host = sys.argv[1]
    port = int(sys.argv[2])
    path = sys.argv[3]
    keep_alive = len(sys.argv) >= 5 and sys.argv[4].lower() == "keep-alive"
    
    response = send_request(host, port, path, keep_alive)
    print(response)

if __name__ == "__main__":
    main()

