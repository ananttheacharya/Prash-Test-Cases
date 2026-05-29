import socket
s1 = socket.socket()
s1.bind(('127.0.0.1', 3000))
s2 = socket.socket()
s2.bind(('127.0.0.1', 3000))