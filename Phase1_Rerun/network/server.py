import socket
# Create a simple TCP server and client:
# Write a Python script using socket library — 
# one that listens on port 8888, one that connects and sends a message. 
# See the three-way handshake in action.

HOST = "127.0.0.1"
PORT = 8888

#(address family, socket type(protocol behaviour))
#AF_INET - IPv4, SOCK_STREAM = TCP, SOCK_DGRAM = UDP
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#attach socket to port
server.bind((HOST, PORT))

#wait for connections - ready to receive connections
server.listen()

#Sending a message
print("Listening on Port:", PORT)

#conn - used to talk to that speciific client
#addr - client's network address
#accept() - return ( connection_socket, client_address)
conn, addr = server.accept()

print("Connected by", addr)

#read upto 1024 bytes from the socket buffer
#Network stores incoming data in a buffer
#?Program reads from the buffer using recv()
data = conn.recv(1024)

#We use decode() because data is sent in bytes so we need to convert into a string
print("Received:", data.decode())

# regular send() might send partial data sendall() guarantess everything is sent. 
#Send bytes to back to the sender b is byte string
conn.sendall(b"Message received")

conn.close()

#create socket
#bind to port
#listen
#wait for client
#accept connection
#receive data
#send response
#close connection