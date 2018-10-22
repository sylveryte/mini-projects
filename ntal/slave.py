import hashlib
import socket  # Import socket module
import threading
import sys
from itertools import chain, product

import time


def brute_force(charset, maxlength):
    return (''.join(candidate)
            for candidate in chain.from_iterable(product(charset, repeat=i)
                                                 for i in range(1, maxlength + 1)))


def get_sha1(s):
    return hashlib.sha1(s.encode('utf-8')).hexdigest()


class Slave:
    """
    receives  : 1 q                     #kill
                2 rest                  #wait for instruction kill current task
                3 job:[to_break]:[task] #new job for

    responds  : 1 fail                        #no result
                2 pass:[job]:[decrypted str]  #result
                3 probe                       #probes when free [prober]
    """

    def __init__(self, host, port):
        self.limit = 2
        self.slave_socket = socket.socket()
        print("Connecting to {} on port {}".format(host, port))

        self.tasks = []
        self.task = ""
        self.to_break = ""
        self.slave_socket.connect((host, port))
        self.slave_socket.setblocking(0)
        self.slave_socket.settimeout(1)
        threading.Thread(target=self.connection_manager).start()
        
    def connection_manager(self):
        waiter_thread = threading.Thread(target=self.waiter)
        executioner_thread = threading.Thread(target=self.executioner)
        prober_thread = threading.Thread(target=self.prober)
        waiter_thread.start()
        executioner_thread.start()
        prober_thread.start()
        prober_thread.join()
        waiter_thread.join()
        executioner_thread.join()
        self.slave_socket.close()

    def prober(self):
        """
        probes master when free by sending 'probe'
        :return:
        """
        # print("prober in")
        while True:
            time.sleep(3)
            if len(self.tasks) <1:
                self.slave_socket.send("probe".encode())
                self.busy = True
                #print("probed!")


    def waiter(self):
        """
        receiver
        """
        while True:
            try:
               reply = self.slave_socket.recv(1024).decode().strip().split(":")
               if reply[0] == "job":
                    self.tasks.append(reply[1]+":"+reply[2])
                    print("********************\nNew job received : {}".format(reply[1]+":"+reply[2]))
                # print(reply)
            except socket.timeout:
                pass
        print("Receiver down")

    def executioner(self):
        """
        responder
        """
        while True:
                # print("BREAKING {} with {}".format(self.to_break, self.task))

                if len(self.tasks) > 0:
                    # rsa decode and then assign to self.task and self.to_break
                    tk=self.tasks.pop()
                    tk=tk.split(":")
                    self.task=tk[1]
                    self.to_break=tk[0]
                    print("---/ breaking {} with {}".format(self.to_break,self.task))
                    response = self.break_code()
                    time.sleep(37)
                    print("RESPONSE ({}) for BREAKING {} with {}".format(response, self.to_break, self.task))
                    if response:
                        self.slave_socket.send(response.rstrip().encode())
                time.sleep(3)
        print("Receiver down")

    def break_code(self, length=1):
        """
        just a tool of slave
        """
        #print("/ breaking {} with {}".format(self.to_break,self.task))
        print("/ ")
        for guess in brute_force(self.task, length):
            if get_sha1(guess) == self.to_break:
                return "pass:" + self.to_break + ':' + guess
        if length > self.limit:
            # print("LENGTH LIMIT REACHED {}".format(length))
            return "fail"
        else:
            return self.break_code(length + 1)


if __name__ == '__main__':
    Slave(sys.argv[1], int(sys.argv[2]))
