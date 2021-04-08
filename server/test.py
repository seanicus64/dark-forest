#!/usr/bin/env python3
import socket
import threading
def loop(socket):
    while True:
        data = socket.recv(1024)
        print(data)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("127.0.0.1", 7777))
#s.sendall(b"hello world")
thread = threading.Thread(target=loop, args=((s,)))
thread.start()
while True:
    message = input("put in something")
    s.send(bytes(f"{message}\r\n".encode("utf-8")))

    if message == "q":
        break
thread.join()
