#create socket
#connect to server
#send data
#receive response
#close

import socket

HOST = '127.0.0.1'
PORT = 8888

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect((HOST, PORT))

client.sendall(b"Hello from client")

data = client.recv(1024)

print("Server says:", data.decode())

client.close()