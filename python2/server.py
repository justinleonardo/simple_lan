import socket
import json
import SocketServer
import struct
from multiprocessing import Process, Queue, Pipe


class UDPDetectionHandler(SocketServer.BaseRequestHandler):
    """
    This class handles server detection over UDP broadcast.
    """

    def handle(self):
        data = self.request[0].strip()
        socket = self.request[1]
        print "{} wrote:".format(self.client_address[0])
        print data
        if data = "to":
            socket.sendto(self.server.server_name.ljust(16), self.client_address)


def UDP_Runner(q,udp_server):
    while True:
        udp_server.handle_request()
        try:
            q.get_nowait()
            break
        except Queue.Empty:
            continue

def lobby_receiver(pipe, max_players, timeout):
    # make a socket for the lobby
    try:
        socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.bind((self.ip, self.port))
        socket.listen(5)
        socket.setblocking(False)
        player_count = 0
        t_initial = time.clock()

        while player_count < max_players and time.clock()-t_initial < timeout:
            try:
                conn, addr = socket.accept()
                rec = conn.recv(16)
                conn.setblocking(False)
                pipe.send((rec.strip(), conn))
                player_count += 1

            except socket.error:
                continue
    finally:
        socket.close()
        pipe.close()


class Server(object):
    """Server(name, port[, ip=])
the name is sent to all clients requesting a server list. The detection port
is the port that clients will ping while looking for the server.  If it is not
set, it will default to the same port that the app will be running on.
"""
    def __init__(self, name, port, ip=None):
        self.port = port
        assert(len(name)<=16)
        self.name = name
        if ip == None:
            ip = _get_computer_ip()
        self.ip = ip
        self.players = {}


    def open_lobby(max_players, timeout=604800):
        """
        open_lobby(max_players, max_wait_time) -> waits until either
        max_players have joined or it times out
        """
        # make UDP server
        udp_server = Socket.UDPServer(
                (self.ip, self.port),
                UDPDetectionHandler)
        udp_server.server_name = self.name # allow broadcast of name
        udp_server.timeout = .05

        # start UDP server in another process

        self.udp_q = Queue()
        self.udp_p = Process(target=UDP_Runner, args=(self.udp_q,udp_server))
        self.udp_p.start()


        # make a socket for the loby
        # can we delete this now?
        socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.bind((self.ip, self.port))
        socket.listen(3)
        socket.setblocking(False)
        player_count = 0
        t_initial = time.clock()

        while player_count < max_players and time.clock()-t_initial < timeout:
            try:
                conn, addr = socket.accept()
                rec = json.loads(conn.recv(16))
                self.players[rec.strip()] = conn
                player_count += 1

            except socket.error:
                continue
        #until here?

        self.lobby_pipe, child_pipe = Pipe(False)
        self.lobby_process = Process(
            target=lobby_receiver, args=(child_pipe, max_players, timeout))
        self.lobby_process.start()

    def count_lobby():
        """
        Only use while the lobby is open retrieves any new players and returns
        the number of connected players
        """
        while self.lobby_pipe.poll():
            name, conn = self.lobby_pipe.recv()
            self.players[name] = conn
        return len(self.players.keys())

    def close_lobby():
        """
        Closes the lobby and retrieves the player connections
        Returns the number of connected players
        """
        # close UDP server
        self.udp_q.put(1);
        self.udp_p.join()
        self.lobby_process.join()
        # closes the other end of the pipe to prevent more data from being
        # added on to the end
        while self.lobby_pipe.poll():
            name, conn = self.lobby_pipe.recv()
            self.players[name] = conn
        return len(self.players.keys())

    def receive_from_all(self):
        """Receives json data from all of the connected clients"""
        results = {}
        for name in self.players.keys():
            data = self.receive_from(name)
            results[name] = data
        return results

    def receive_from_all_raw(self):
        """Receives raw data from all of the connected clients"""
        results = {}
        for name in self.players.keys():
            data = self.receive_from_raw(name)
            results[name] = data
        return results

    def receive_from_raw(self, name):
        """Receives a string of bytes from a given client"""
        conn = self.players[name]
        try:
            data = conn.recv(2)
            p_size = struct.unpack("!H", data)
            data = conn.recv(p_size)
            return data
        except socket.error:
            return None

    def receive_from(self, name):
        """Receives a list or dictionary from a player"""
        data = self.receive_from_raw(name)
        if data = None:
            return None
        return json.loads(data)

    def send_to_all(self, data):
        """Sends an array or dictionary to all of the connected clients"""
        msg = json.dumps(data)
        return self.send_to_all_raw(msg)

    def send_to_all_raw(self, msg):
        """Sends a string of bytes to all of the connected clients"""
        work = True
        for name in self.players.keys():
            work = work && self.send_to_raw(name, msg)
        return work

    def send_to(self, name, data):
        """Like send_to_all, but only sends to a single player"""
        msg = json.dumps(data)
        return self.send_to_raw(msg, name)

    def send_to_raw(self, name, msg):
        """Like send_to_all_raw, but only sends to a single player"""
        p_size = len(msg)
        p_size = struct.pack("!H", p_size)
        try:
            self.players[name].sendall(p_size)
            self.players[name].sendall(msg)
            return True
        except socket.error:
            return False

    def close_server(self):
        """
        Closes the server object.  It will stop working after this is called
        """
        for conn in self.players.values():
            conn.close()

    def _get_computer_ip(self):
        """
        Returns the ip address of this computer, should be platfrom agnostic
        """
        gws = netifaces.gateways()
        return gws['default'][netifaces.AF_INET][0]




