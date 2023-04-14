import os
import socket
import subprocess
import select
from cryptography.fernet import Fernet
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import ProgressBar
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
import pickle
from threading import Thread
import paramiko


class TerminalTTY:
    """
    Interactive Terminal TTY Class using Paramiko for cross-platform compatibility
    """

    def __init__(self, target_ip=None, target_port=None, key=None):
        """
        Initialize the TerminalTTY object.

        :param target_ip: The target IP address as a string (default None).
        :param target_port: The target port number as an int (default None).
        :param key: The encryption key as a bytes object (default None).
        """
        self.commands = {}
        self.session = PromptSession(history=InMemoryHistory())
        self.completer = WordCompleter(list(self.commands.keys()))
        self.style = Style.from_dict({'prompt': '#0077ff bold'})
        self.target_ip = target_ip
        self.target_port = target_port
        self.key = key
        self.ssh_client = None

    def add_command(self, command_name, command_func):
        """
        Add a custom command to the terminal tty.

        :param command_name: The name of the command as a string.
        :param command_func: The function to execute when the command is run.
        """
        self.commands[command_name] = command_func
        self.completer = WordCompleter(list(self.commands.keys()))

    def _run_command(self, text):
        """
        Execute the command associated with the given input text.

        :param text: The user's input as a string.
        """
        args = text.split()
        command_name = args.pop(0)
        if command_name in self.commands:
            try:
                self.commands[command_name](args)
            except Exception as e:
                print(f"Error: {e}")
        else:
            _, stdout, stderr = self.ssh_client.exec_command(text)
            output_encrypted = Fernet(
                self.key).encrypt(stdout.read() + stderr.read())
            self.socket.send(output_encrypted)

    def run(self):
        """
        Start the interactive terminal tty.
        """
        if self.target_ip and self.target_port:
            # Client mode - connect to remote server
            try:
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(
                    paramiko.AutoAddPolicy())
                self.ssh_client.connect(
                    hostname=self.target_ip,
                    port=self.target_port,
                    username=os.getlogin(),
                    password=paramiko.Transport._read_password_input(
                        prompt='Password: '),
                    look_for_keys=False,
                    allow_agent=False
                )
                self.socket = self.ssh_client.invoke_shell()
            except Exception as e:
                print(
                    f"Failed to connect to {self.target_ip}:{self.target_port}")
                return

            while True:
                try:
                    cmd_encrypted = self.socket.recv(1024)
                    if cmd_encrypted.lower() == b'exit':
                        break
                    cmd = Fernet(self.key).decrypt(cmd_encrypted).decode()
                    args = cmd.split()

                    if args[0] in ['download', 'upload']:
                        filename = args[1]
                        with open(filename, 'wb') as f:
                            pb = ProgressBar()
                            data_size = int(self.socket.recv(1024).decode())
                            for i in pb(range(data_size // 1024 + 1)):
                                data = self.socket.recv(1024)
                                if not data:
                                    break
                                f.write(data)

                            if args[0] == 'download':
                                print(f"{filename} downloaded")
                            else:
                                print(f"{filename} uploaded")

                    elif args[0] == 'ls':
                        _, stdout, stderr = self.ssh_client.exec_command(cmd)
                        output_encrypted = Fernet(
                            self.key).encrypt(pickle.dumps(stdout.read()))
                        self.socket.send(output_encrypted)

                    elif args[0] == 'netcut':
                        self._netcut_command(args[1:])

                    else:
                        _, stdout, stderr = self.ssh_client.exec_command(cmd)
                        output_encrypted = Fernet(
                            self.key).encrypt(stdout.read() + stderr.read())
                        self.socket.send(output_encrypted)
                except (KeyboardInterrupt, EOFError):
                    continue

            self.socket.close()
            self.ssh_client.close()

        else:
            # Server mode - wait for incoming connections
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('0.0.0.0', self.target_port))
            server_socket.listen()

            while True:
                conn, addr = server_socket.accept()
                print(f"Connection from {addr[0]}:{addr[1]}")
                try:
                    while True:
                        text = self.session.prompt(f"{addr[0]}:{addr[1]} > ",
                                                   completer=self.completer, style=self.style)
                        if text.lower() == 'exit':
                            conn.send(b'exit')
                            break
                        else:
                            cmd_encrypted = Fernet(
                                self.key).encrypt(text.encode())
                            conn.send(cmd_encrypted)

                            if text.split()[0] in ['download', 'upload']:
                                filename = text.split()[1]
                                with open(filename, 'rb') as f:
                                    data = f.read()
                                    conn.send(str(len(data)).encode())
                                    pb = ProgressBar()
                                    for i in pb(range(len(data) // 1024 + 1)):
                                        conn.send(
                                            data[i * 1024:(i + 1) * 1024])
                            elif text.split()[0] == 'ls':
                                output_encrypted = conn.recv(1024)
                                output = pickle.loads(Fernet(
                                    self.key).decrypt(output_encrypted))
                                print(output.decode())
                            elif text.split()[0] == 'netcut':
                                self._netcut_command(text.split()[1:])
                            else:
                                output_encrypted = conn.recv(1024)
                                output = Fernet(
                                    self.key).decrypt(output_encrypted).decode()
                                print(output)
                except (KeyboardInterrupt, EOFError):
                    continue

            conn.close()

    def add_netcut_command(self):
        """
        Add a command to start or stop the netcut functionality.
        """
        self.add_command('netcut', self._netcut_command)

    def _netcut_command(self, args):
        """
        Start or stop the netcut functionality based on the given arguments.

        :param args: A list of command arguments.
        """
        if len(args) == 0:
            print("Usage: netcut <start|stop>")
        elif args[0] == 'start':
            if len(args) > 1:
                target_ip = args[1]
                self.netcut = NetCut(target_ip=target_ip)
            else:
                self.netcut = NetCut()
            self.netcut.start()
            print("NetCut started")
        elif args[0] == 'stop':
            if hasattr(self, 'netcut'):
                self.netcut.stop()
                print("NetCut stopped")
            else:
                print("NetCut is not running")
        else:
            print("Usage: netcut <start|stop>")


class NetCut:
    """
    NetCut class for blocking network traffic between two IP addresses.
    """

    def __init__(self, target_ip=None):
        """
        Initialize the NetCut object.

        :param target_ip: The target IP address as a string (default None).
        """
        self.target_ip = target_ip
        self.stop_event = False

    def start(self):
        """
        Start blocking the network traffic between the target IP and all other IPs.
        """
        # Create a new thread to run the netcut loop
        t = Thread(target=self._netcut_loop)
        t.start()

    def stop(self):
        """
        Stop blocking the network traffic.
        """
        self.stop_event = True

    def _netcut_loop(self):
        """
        The main netcut loop that listens for incoming connections and blocks the traffic
        between the target IP and all other IPs.
        """

        transport = None
        try:
            transport = paramiko.Transport((self.target_ip, 22))
            transport.connect(username=os.getlogin(),
                              password=paramiko.Transport._read_password_input(prompt='Password: '))
            channel = transport.open_channel("direct-tcpip",
                                             (self.target_ip, 0),
                                             ("0.0.0.0", 0))
            listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listen_socket.bind(('0.0.0.0', 0))
            listen_socket.listen(1)

            while not self.stop_event:
                client_socket, _ = listen_socket.accept()
                server_socket = channel.accept()[0]

                # Start a new thread to handle the connection
                t = Thread(target=self._netcut_connection,
                           args=(client_socket, server_socket))
                t.start()

            transport.close()
        except Exception as e:
            print(f"Error: {e}")

    def _netcut_connection(self, client_socket, server_socket):
        """
        Handle a single connection by copying data between the client and server sockets.

        :param client_socket: The client socket object.
        :param server_socket: The server socket object.
        """
        while not self.stop_event:
            rlist, _, _ = select.select([client_socket, server_socket], [], [])
            if client_socket in rlist:
                data = client_socket.recv(1024)
                if not data:
                    break
                server_socket.send(data)
            if server_socket in rlist:
                data = server_socket.recv(1024)
                if not data:
                    break
                client_socket.send(data)

        client_socket.close()
        server_socket.close()


tty = TerminalTTY(target_ip="google.com", target_port=22)
tty.add_netcut_command()
tty.run()
