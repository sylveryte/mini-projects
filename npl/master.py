import socket
import string
import threading
from queue import Queue

import sys

import time


class SlaveHandler:
    def __init__(self, slave_socket, address, breakroom):
        self.breakroom = breakroom
        self.address = address
        self.socket = slave_socket
        self.dead = False
        ready = self.socket.recv(1024).decode()

        if ready.strip() == "ready":
            threading.Thread(target=self.waiter).start()

    def waiter(self):
        self.send_new_job()
        while True:
            if self.dead:
                print("waiter down")
                self.socket.send("rest".encode())
                time.sleep(4)
                self.socket.close()
                break
            result = self.socket.recv(1024).decode()
            if result is ":":
                self.send_new_job()
                continue
            elif result:
                self.breakroom.got_result(result.encode())

    def send_new_job(self):
        print("sending new job to {}".format(self.address))
        self.socket.send(self.breakroom.get_next_task().encode())

    def close_connection(self):
        self.dead = True
        self.socket.send("rest".encode())


class BreakRoom:
    def __init__(self, hash_to_break, port):
        self.result = ""
        self.hash_to_break = hash_to_break

        nums = '1234567890'
        special = '`~!@#$%^&*()_+-='
        space = ' '

        self.result_received = False

        self.thequeue = Queue()
        self.thequeue.put(str(string.ascii_lowercase))
        self.thequeue.put(str(string.ascii_letters))
        self.thequeue.put(str(string.ascii_lowercase + nums))
        self.thequeue.put(str(string.ascii_letters + nums))
        self.thequeue.put(str(string.ascii_uppercase))
        self.thequeue.put(str(string.ascii_uppercase + nums))
        self.thequeue.put(str(string.ascii_lowercase + nums + special))
        self.thequeue.put(str(string.ascii_lowercase + special))
        self.thequeue.put(str(string.ascii_letters + special))
        self.thequeue.put(str(string.ascii_letters + nums + special))
        self.thequeue.put(str(string.ascii_uppercase + nums + special))
        self.thequeue.put(str(string.ascii_uppercase + special))
        self.thequeue.put(str(string.ascii_lowercase + nums + space))
        self.thequeue.put(str(string.ascii_uppercase + nums + space))
        self.thequeue.put(str(string.ascii_letters + nums + space))
        self.thequeue.put(str(string.ascii_lowercase + nums + space))
        self.thequeue.put(str(string.ascii_uppercase + nums + space))
        self.thequeue.put(str(string.ascii_letters + nums + space))

        print("Decrypting : {}".format(hash_to_break))

        self.slave_sockets = []

        self.master_socket = socket.socket()
        self.host = socket.gethostname()
        self.port = port
        self.master_socket.bind((self.host, self.port))

        threading.Thread(name="receiptionist", target=self.receive_incoming_request).start()

    def receive_incoming_request(self):
        self.master_socket.listen(20)
        self.master_socket.setblocking(0)
        self.master_socket.settimeout(2)
        while True:
            try:
                slave_socket, addr = self.master_socket.accept()
                slave_socket.send(self.hash_to_break.encode())
                print('Got connection from {}'.format(addr))
                self.slave_sockets.append(SlaveHandler(slave_socket, addr, self))
            except socket.timeout:
                if self.result_received:
                    break
        print("Receiptionist down.")
        print("Password is '{}'".format(self.result))

    def get_next_task(self):
        if self.thequeue.empty() or self.result_received:
            return "rest"
        else:
            return self.thequeue.get()

    def close_all_connections(self):
        for slave in self.slave_sockets:
            slave.close_connection()
        print("Slaves closed")

    def got_result(self, result):
        self.result_received = True
        self.result = result.decode()
        self.close_all_connections()


if __name__ == '__main__':
    BreakRoom(str(sys.argv[1]), 12356)
