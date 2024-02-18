import socket

ip_address = "127.0.0.1"
port_number = 8888
port_number = int(port_number)  

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((ip_address, port_number))

print("Server running")

while True:
    message, client_address = server.recvfrom(2048)
    mod_msg = message.decode().upper()
    server.sendto(mod_msg.encode(), client_address)

