import hashlib
import socket  # Import socket module
import threading
from itertools import chain, product

import time


def brute_force(charset, maxlength):
    return (''.join(candidate)
            for candidate in chain.from_iterable(product(charset, repeat=i)
                                                 for i in range(1, maxlength + 1)))


def get_sha1(s):
    return hashlib.sha1(s.encode('utf-8')).hexdigest()


class Slave:
    def __init__(self, host, port):
        self.slave_socket = socket.socket()
        print("Connecting to {} on port {}".format(host, port))

        self.dead = False
        self.killer_on = False

        self.slave_socket.connect((host, port))
        self.to_break = self.slave_socket.recv(1024).decode()
        self.slave_socket.setblocking(0)
        self.slave_socket.settimeout(1)
        print("to break : {}".format(self.to_break))

        self.slave_socket.send("ready".encode())

        threading.Thread(target=self.execution).start()

    def smart_killer(self):
        while True:
            try:
                job_str = self.slave_socket.recv(1024).decode()
                if job_str.strip() == "rest":
                    self.dead = True
                    break
            except socket.timeout:
                pass
                # print("smartkiller missed")

        print("smart killer killed again")
        time.sleep(3)
        self.slave_socket.close()
        print("Slave closed")

    def execution(self):
        while True:
            if self.dead:
                break
            try:
                job_str = self.slave_socket.recv(1024).decode()
                job_str = job_str.strip()
                if job_str == "rest":
                    break
                print("job is : {}".format(job_str))
                if not self.killer_on:
                    threading.Thread(target=self.smart_killer).start()
                    self.killer_on = True

                result = self.break_code(job_str)
                print("breaking result : {}".format(result))
                if result:
                    print("Sending result ({})".format(result))
                    self.slave_socket.send(result.encode())
                else:
                    print("Requesting for new job!! by sending : ")
                    self.slave_socket.send(":".encode())
            except socket.timeout:
                print("Executioner xpd a timeout")
        print("executioner down")

    def break_code(self, char_set, length=1):
        print("Entering with {}|{}".format(length, char_set))
        for g in brute_force(char_set, length):
            if self.dead:
                return
            if get_sha1(g) == self.to_break:
                return g
        if length > 5:
            print("LENGHT LIMIT REACHED {}".format(length))
            return None
        else:
            return self.break_code(char_set, length + 1)


if __name__ == '__main__':
    Slave(socket.gethostname(), 12356)
