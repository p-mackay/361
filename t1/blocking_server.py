#!/usr/bin/env python3

import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("", 9000))
s.listen(5)

while True:
    conn, addr = s.accept()
    print(f"Received connection from {addr[0]} on port {addr[1]}")
    conn.send(f"Hello {addr}\n".encode())
    conn.close()
