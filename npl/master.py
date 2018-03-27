import socket
import string
import threading
from queue import Queue

import sys

import time

import os


class SlaveHandler:
    """
    recieves  : 1 fail                        #no result
                2 pass:[job]:[decrypted str]  #result
                3 probe                       #probes when free [prober]

    responds  : 1 q                     #kill
                2 rest                  #wait for instruction kill current task
                3 job:[to_break]:[task] #new job for
    """

    def __init__(self, slave_socket, break_room, job_master, slave_id):
        """

        :type job_master: JobMaster
        :type break_room: BreakRoom
        """
        self.slave_id = slave_id
        self.job_master = job_master
        self.break_room = break_room
        self.socket = slave_socket
        self.socket.setblocking(0)
        self.socket.settimeout(1)
        self.dead = False
        threading.Thread(target=self.connection_manager).start()

    def connection_manager(self):
        waiter_thread = threading.Thread(target=self.waiter)
        waiter_thread.start()
        waiter_thread.join()
        self.socket.close()
        self.break_room.remove_slave_handler(self)

    def waiter(self):
        """
        receiver + responder[jobs]
        """
        while True:
            try:
                if self.dead:
                    break
                reply = self.socket.recv(1024).decode()
                if reply == '':
                    self.dead = True
                reply = reply.split(":")
                # print("{} received {}".format(self.slave_id, reply))
                if reply[0] == "probe":
                    self.send_new_job()
                elif reply[0] == "fail":
                    pass
                    # print("One fail")
                elif reply[0] == "pass":
                    self.break_room.got_result(reply[1] + ":" + reply[2])
            except socket.timeout:
                pass
        print("Slave{} down ".format(self.slave_id))

    def dispatcher(self):
        """
        responder[kill(q)]
        """
        while True:
            if self.dead:
                self.socket.send("q".encode())
                break
            time.sleep(3)

    def send_new_job(self):
        self.socket.send(self.job_master.get_task().encode())

    def close_connection(self):
        self.dead = True

    def send_rest(self):
        self.socket.send("rest".encode())


class JobMaster:
    def __init__(self, sha1code, break_room):
        """

        :type break_room: BreakRoom
        """
        self.break_room = break_room
        self.the_queue = Queue()
        self.currentJob = None
        self.from_file = False
        self.jobs = []
        if os.path.isfile(sha1code):
            self.from_file = True
            self.result_file = open("decrypted" + sha1code + ".txt", 'w')
            print("Decrypting from file. Results in Decrypted+{}".format(sha1code))
            for x in open(sha1code, 'r').read().split():
                self.jobs.append(x)
        else:
            self.jobs.append(sha1code)

        # print("JOB MASTER'S JOBS : {}".format(self.jobs))
        self._new_job()

    def _generate_new_queue(self):
        nums = '1234567890'
        special = '`~!@#$%^&*()_+-='
        space = ' '
        self.the_queue = Queue()
        self.the_queue.put(str(string.ascii_lowercase))
        self.the_queue.put(str(string.ascii_letters))
        self.the_queue.put(str(string.ascii_lowercase + nums))
        self.the_queue.put(str(string.ascii_letters + nums))
        self.the_queue.put(str(string.ascii_uppercase))
        self.the_queue.put(str(string.ascii_uppercase + nums))
        self.the_queue.put(str(string.ascii_lowercase + nums + special))
        self.the_queue.put(str(string.ascii_lowercase + special))
        self.the_queue.put(str(string.ascii_letters + special))
        self.the_queue.put(str(string.ascii_letters + nums + special))
        self.the_queue.put(str(string.ascii_uppercase + nums + special))
        self.the_queue.put(str(string.ascii_uppercase + special))
        self.the_queue.put(str(string.ascii_lowercase + nums + space))
        self.the_queue.put(str(string.ascii_uppercase + nums + space))
        self.the_queue.put(str(string.ascii_letters + nums + space))
        self.the_queue.put(str(string.ascii_lowercase + nums + space))
        self.the_queue.put(str(string.ascii_uppercase + nums + space))
        self.the_queue.put(str(string.ascii_letters + nums + space))

    def _new_job(self):
        if len(self.jobs) > 0:
            self.currentJob = self.jobs.pop()
            self._generate_new_queue()
            print("Decrypting : {}".format(self.currentJob))
        elif len(self.jobs) == 0:
            self.currentJob = None
            self.break_room.we_are_done()

    def get_task(self):
        if not self.currentJob:
            temp_str = "q"
        elif self.the_queue.empty():
            self._new_job()
            temp_str = "rest"
        else:
            temp_str = "job:" + self.currentJob + ':' + self.the_queue.get()
        # print("JOb master : {}".format(temp_str))
        return temp_str

    def take_result(self, result):
        result = result.split(":")
        print("########### {} -> {}".format(result[0], result[1]))
        self.break_room.send_rest()
        self._new_job()
        if self.from_file:
            self.result_file.write(result[0] + " -> " + result[1] + '\n')


class BreakRoom:
    def __init__(self, host, port, sha1code):
        self.failure = 0
        self.we_are_done_switch = False
        self.jobMaster = JobMaster(sha1code, self)

        self.slave_handlers = []

        self.master_socket = socket.socket()
        self.master_socket.bind((host, port))

        threading.Thread(name="receiptionist", target=self.receive_incoming_request).start()

    def receive_incoming_request(self):
        self.master_socket.listen(20)
        self.master_socket.setblocking(0)
        self.master_socket.settimeout(2)
        slave_id = 0
        while True:
            try:
                slave_socket, addr = self.master_socket.accept()
                print('Got connection from {}'.format(addr))
                self.slave_handlers.append(SlaveHandler(slave_socket, self, self.jobMaster, slave_id))
                slave_id += 1
            except socket.timeout:
                if self.we_are_done_switch and not len(self.slave_handlers):
                    self._close_all_connections()
                    break
        print("Receiptionist down.")

    def _close_all_connections(self):
        for slave in self.slave_handlers:
            slave.close_connection()
        # print("Slaves closed")

    def got_result(self, result):
        self.jobMaster.take_result(result)

    def we_are_done(self):
        self.we_are_done_switch = True
        # print("WE ARE DONE!!")

    def remove_slave_handler(self, slave_handler):
        self.slave_handlers.pop(self.slave_handlers.index(slave_handler))

    def send_rest(self):
        for x in self.slave_handlers:
            x.send_rest()


if __name__ == '__main__':
    pass
    # print(sys.argv)
    if len(sys.argv) == 4:
        BreakRoom(sys.argv[1], int(sys.argv[2]), sys.argv[3])
    else:
        print("syntax : python3 master.py [local ip addr] [port] [sha1 code /sha1 file] optional[no of localslaves]\n "
              "eg     : python3 master.py 192.168.1.105 9987 e5acb1a96e34cd7f263aada0b69aa58bdd722a03 3 ")
