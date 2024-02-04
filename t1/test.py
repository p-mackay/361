import socket
import select
import os

HOST, PORT = 'localhost', 9000
FILE_DIR = '/var/www/html'

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen()
server_socket.setblocking(False)

# Lists to keep track of sockets
inputs = [server_socket]
connections = {}  # Dictionary to keep track of connection headers

def handle_connection(conn, data):
    lines = data.decode().split("\r\n")
    request_line = lines[0]
    headers = {line.split(": ")[0]: line.split(": ")[1] for line in lines[1:] if ": " in line}

    try:
        method, path, version = request_line.split()
        if method != "GET" or version != "HTTP/1.0":
            raise ValueError("Unsupported method or version")
        filepath = os.path.join(FILE_DIR, path.lstrip("/"))
        if not os.path.isfile(filepath):
            raise FileNotFoundError
        with open(filepath, 'rb') as file:
            body = file.read()
        response = f"HTTP/1.0 200 OK\r\nContent-Length: {len(body)}\r\n\r\n".encode() + body
        conn.sendall(response)
        if headers.get("Connection") != "keep-alive":
            conn.close()
            inputs.remove(conn)
    except (ValueError, FileNotFoundError):
        response = "HTTP/1.0 404 Not Found\r\n\r\n" if method == "GET" else "HTTP/1.0 400 Bad Request\r\n\r\n"
        conn.sendall(response.encode())
        conn.close()
        inputs.remove(conn)

while inputs:
    readable, _, exceptional = select.select(inputs, [], inputs)
    for s in readable:
        if s is server_socket:
            client_socket, _ = server_socket.accept()
            client_socket.setblocking(False)
            inputs.append(client_socket)
        else:
            data = s.recv(1024)
            if data:
                handle_connection(s, data)
            else:
                s.close()
                inputs.remove(s)

    for s in exceptional:
        inputs.remove(s)
        s.close()

