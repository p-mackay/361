import socket
import json

def serialize_packet(packet):
    # Convert the packet dictionary to a JSON string and encode it to bytes
    return json.dumps(packet).encode()

ip = "127.0.0.1"
port = 8888
port = int(port)  

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

snd_buf = [
    {
        "command": "SYN",
        "sequence": 0,
        "acknowledgment": 0,
        "window": 1024,
        "length": 0,
        "payload": "",
        "timestamp": 1652902500,
        "acknowledged": False
    },
    {
        "command": "DAT",
        "sequence": 1,
        "acknowledgment": 0,
        "window": 1024,
        "length": 5,
        "payload": "Hello",
        "timestamp": 1652902505,
        "acknowledged": False
    },
    {
        "command": "DAT",
        "sequence": 6,
        "acknowledgment": 0,
        "window": 1024,
        "length": 5,
        "payload": "World",
        "timestamp": 1652902510,
        "acknowledged": False
    },
    {
        "command": "FIN",
        "sequence": 11,
        "acknowledgment": 0,
        "window": 1024,
        "length": 0,
        "payload": "",
        "timestamp": 1652902515,
        "acknowledged": False
    }
]


message = serialize_packet(snd_buf[0])
client.sendto(message, (ip, port))

mod_msg, serv_address = client.recvfrom(2048)
print (mod_msg.decode())
client.close()

