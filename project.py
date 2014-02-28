#!/usr/bin/env python3
import socket
import sys
import threading
import time
import queue
import random


class TCPModel(threading.Thread):
    """Functions common in all TCP objects"""

    def on_new_msg(self, msg, connection):
        """Called when a new message is availible"""
        pass

    def log(self, msg):
        """Output log message"""
        print ("{0}: {1}".format(self.host_name, msg))

    def socket_mon(self, connection):
        """Monitor socket and get all data out of it"""
        try:
            # Receive the data in small chunks
            data = b""
            while True:
                try:
                    temp = connection.recv(64)
                except socket.timeout as e:
                    temp = None

                if not temp:
                    # Break out of the loop if the TCP object is shutting down
                    if self.stop.is_set():
                        break
                    else:
                        continue

                # Add recieved data to buffer
                data += temp
                
                # Process new lines
                if b"\x00" in data:
                    split_data = data.split(b"\x00")

                    # The last item will be '' (ended with a \x00) or a partial line
                    # Either way, set it as data without using it as a line
                    for x in range(len(split_data)-1):
                        self.on_new_msg(split_data[x], connection)
                    data = split_data[-1]
        except socket.error as e:
            pass
        finally:
            connection.close()


class Tracker(TCPModel):

    connections = {}
    server_map = {}
    client_map = {}

    matches = None
    stop = threading.Event()

    def __init__(self, host_name, server_address):
        self.host_name = host_name

        self.stop = threading.Event()

        # Create the socket and start serving
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(server_address)
        self.sock.settimeout(5)

        # Wait for incoming connections
        self.sock.listen(1)
        
        threading.Thread.__init__(self, target=self.serve_forever)
        self.start()

    def serve_forever(self):
        """Serves forever"""

        while not self.stop.is_set():
            try:
                connection, client_address = self.sock.accept()
            except socket.timeout as e:
                pass
            else:
                t = threading.Thread(target=self.socket_mon, args=(connection,))
                t.start()
                self.connections[connection.getpeername()] = (connection, t)

    def on_new_msg(self, msg, connection):
        """Called when a new message comes in"""

        msg = str(msg, "utf-8")
        cmd, params = msg.split(" ", 1)

        # Server hello
        if cmd == "HELLO":
            # Server saying hello, add it to the server map
            self.server_map[connection.getpeername()] = params
            self.log("Recieved 'Hello' from Server {0}".format(params))
            return

        # Client hi
        if cmd == "HI":
            # Client saying hi, add it to the client map
            self.client_map[connection.getpeername()] = params
            self.log("Recieved 'Hi' from Client {0}".format(params))
            return

        # Process search request from client
        if cmd == "SRCH":
            # Client requesting a search, send out a message to all connected servers
            client_name = self.client_map[connection.getpeername()]
            self.log("Process match request from {0}".format(client_name))
            self.match_request(params, connection)
            return

        # Process search result match from server
        if self.matches and cmd == "MTCH":
            self.matches.put(self.server_map[connection.getpeername()])

    def do_match_results(self, connection):
        """Process matches and send results to client"""
        temp = []
        while True:
            try:
                temp.append(self.matches.get(False))
            except queue.Empty as e:
                break

        # Send results to client
        self.log("Send match reply to {0}".format(self.client_map[connection.getpeername()]))
        msg = "RSLT {0}\x00".format(" ".join([x for x in temp]))

        connection.sendall(bytes(msg, "utf-8"))

    def match_request(self, srch, connection):
        """Start waiting for match results"""
        temp = bytes("SRCH {0}\x00".format(srch), "utf-8")
        for k in self.server_map:
            self.connections[k][0].sendall(temp)

        # Process all recieved match results in 2 seconds
        self.matches = queue.Queue()
        t = threading.Timer(2, self.do_match_results, args=(connection,))
        t.start()

    def shutdown(self):
        """Shutdown the tracker"""
        self.log("Shutting down")
        self.stop.set()
        for k, v in self.connections.items():
            v[1].join()


class TCPClient(TCPModel):

    def __init__(self, host_name, server_address):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(5)

        self.server_address = server_address
        self.host_name = host_name
        
        self.stop = threading.Event()
        
        threading.Thread.__init__(self, target=self.socket_mon, args=[self.sock])

    def shutdown(self):
        """Shut down the client"""
        self.log("Shutting down")
        self.stop.set()
        self.sock.close()


class Server(TCPClient):

    def __init__(self, host_name, server_address):
        TCPClient.__init__(self, host_name, server_address)

        self.num = random.randint(1, 10)
        self.log("Selected random number is {0}".format(self.num))

        self.connect()

    def on_new_msg(self, msg, connection):
        """Called when a new message comes in"""

        msg = str(msg, "utf-8")
        cmd, params = msg.split(" ", 1)

        # Recieved a request for a search
        if cmd == "SRCH":
            try:
                x = int(params)
            except ValueError as e:
                return
            if x == self.num:
                self.sock.sendall(b"MTCH \x00")

    def connect(self):
        """Connect to the tracker and send HELLO"""

        self.sock.connect(self.server_address)

        self.log("Sending HELLO to Tracker")

        msg = "HELLO {0}\x00".format(self.host_name)
        self.sock.sendall(bytes(msg, "utf-8"))
        self.start()


class Client(TCPClient):

    def __init__(self, host_name, server_address):
        TCPClient.__init__(self, host_name, server_address)

        self.waiting = threading.Event()

        self.connect()

    def on_new_msg(self, msg, connection):
        """Called when a new message comes in"""
        
        msg = str(msg, "utf-8")
        cmd, params = msg.split(" ", 1)

        # Got a result back from the search
        if cmd == "RSLT":
            if params:
                self.log("Match found on servers {0}".format(params))
            else:
                self.log("No match has been found")

            # Allow the search function to return
            self.waiting.set()

    def connect(self):
        """Connect to the tracker and send HI"""
        self.sock.connect(self.server_address)

        self.log("Sending HI to Tracker")

        msg = "HI {0}\x00".format(self.host_name)
        self.sock.sendall(bytes(msg, "utf-8"))
        self.start()

    def search(self):
        """Do a search for data"""
        self.waiting.clear()
        i = random.randint(1, 10)
        self.log("Find match of {0}".format(i))

        # Send a search request to the tracker
        msg = "SRCH {0}\x00".format(i)
        self.sock.sendall(bytes(msg, "utf-8"))

        # Wait for a response
        self.waiting.wait()

if __name__ == "__main__":
    """Program entry point"""

    if len(sys.argv) > 1 and int(sys.argv[1]) > 0:
        num = int(sys.argv[1])
    else:
        num = 3
    
    server_address = ("localhost", 8080)

    # Create tracker, servers, and clients
    tracker = Tracker("Tracker", server_address)
    servers = [Server("S{0}".format(x+1), server_address) for x in range(num)]
    clients = [Client("C{0}".format(x+1), server_address) for x in range(num)]

    # 5 iterations of each client performing a search
    for x in range(5):
        for c in clients:
            c.search()

    # Shutdown servers and clients
    for s in servers:
        s.shutdown()
    for c in clients:
        c.shutdown()

    # Wait for everything to exit
    for s in servers:
        s.join()
    for c in clients:
        c.join()

    # Shutdown tracker and wait for it to exit
    tracker.shutdown()
    tracker.join()
