# SecureShellTTY
SecureShellTTY is an interactive and secure terminal tty tool that allows users to connect to a remote server using SSH. It supports basic operations, customizable commands, and netcut functionality.


Interactive Terminal TTY - README

This is an interactive terminal tty (TerminalTTY) that uses Paramiko to create secure connections between the client and server. The NetCut class is used to block network traffic between two IP addresses, and the add_netcut_command() method can be used to add a custom command to start or stop the netcut functionality.

Requirements


    Python 3.x

    Paramiko

    cryptography

    prompt_toolkit


How to use

To start a new interactive terminal session, first create a TerminalTTY object:

tty = TerminalTTY()


You can then add custom commands to the terminal tty using the add_command() method:

def my_custom_command(args):
    print(f"This is my custom command with args: {args}")

tty.add_command("mycmd", my_custom_command)


You can also add the netcut functionality using the add_netcut_command() method:

tty.add_netcut_command()


Once you have added your custom commands (and the netcut functionality if desired), you can then start the interactive terminal by calling the run() method:

tty.run()


If you want to connect to a remote server instead of running the terminal locally, you can specify the target IP address and port number when creating the TerminalTTY object:

tty = TerminalTTY(target_ip="192.168.1.100", target_port=22)


When running in client mode, the run() method will connect to the target server and start listening for user input. You can type any command supported by the remote shell, and it will be executed on the remote server. If you want to run a custom command that you have added to the terminal tty, simply enter the name of the command followed by any arguments:

> mycmd arg1 arg2
This is my custom command with args: ['arg1', 'arg2']


You can also download or upload files to/from the remote server using the download or upload commands:

> download file.txt
file.txt downloaded

> upload file.txt
file.txt uploaded


When running in server mode, the run() method will start listening for incoming connections and display the IP address of each client that connects. You can then type any command supported by the local shell, and it will be executed on the server. If you want to download or upload a file, simply enter the download or upload command followed by the name of the file:

192.168.1.100:3456 > ls
file1.txt
file2.txt

192.168.1.100:3456 > download file1.txt
file1.txt downloaded


If you have added the netcut functionality, you can use the netcut command to block network traffic between two IP addresses:

> netcut start 192.168.1.100
NetCut started

> netcut stop
NetCut stopped


Example

Here's an example of how to use the TerminalTTY class to connect to a remote server and perform some basic operations:

from terminaltty import TerminalTTY

tty = TerminalTTY(target_ip="192.168.1.100", target_port=22)
tty.add_netcut_command()
tty.run()


When the interactive terminal starts, you can type any command supported by the remote shell. For example, you can list the contents of a directory using the ls command:

> ls
file1.txt
file2.txt


If you want to download a file from the remote server, enter the download command followed by the name of the file:

> download file1.txt
file1.txt downloaded


If you want to upload a file to the remote server, enter the upload command followed by the name of the file:

> upload file3.txt
file3.txt uploaded


You can also use any custom commands that you have added to the terminal tty:

> mycmd arg1 arg2
This is my custom command with args: ['arg1', 'arg2']


Finally, if you want to block network traffic between two IP addresses, enter the netcut command followed by start and the target IP address:

> netcut start 192.168.1.100
NetCut started


To stop the netcut functionality, enter the netcut command followed by stop:

> netcut stop
NetCut stopped
