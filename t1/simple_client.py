#!/usr/bin/env python3

import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("127.0.0.1", 9000)) 
s.send(b"GET /index.html HTTP/1.0\nhost: 127.0.0.1\nConnection: close\n\n")
data = s.recv(10000)
s.close()

print(data.decode())
