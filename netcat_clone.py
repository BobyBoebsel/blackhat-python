import argparse
import socket
import shlex
import subprocess
import sys
import textwrap
import threading

# Funktion zum Ausführen von Shell-Befehlen
def execute(cmd):
    cmd = cmd.strip()
    if not cmd:
        return
    try:
        output = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT)
        return output.decode()
    except Exception as e:
        return f"Command failed: {e}"

class NetCat:
    def __init__(self, args, buffer=None):
        self.args = args
        self.buffer = buffer
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        if self.args.listen:
            self.listen()
        else:
            self.send()

    def send(self):
        try:
            self.socket.connect((self.args.target, self.args.port))
        except ConnectionRefusedError as e:
            print(f"Connection failed: {e}")
            sys.exit(1)
        if self.buffer:
            self.socket.send(self.buffer)
        try:
            while True:
                recv_len = 1
                response = ""
                while recv_len:
                    data = self.socket.recv(4096)
                    recv_len = len(data)
                    response += data.decode()
                    if recv_len < 4096:
                        break
                if response:
                    print(response)
                    try:
                        buffer = input("")  # Benutzereingabe
                    except EOFError:  # EOF (Strg + D) abfangen
                        print("No more input. Exiting.")
                        break
                    buffer += "\n"
                    self.socket.send(buffer.encode())
        except KeyboardInterrupt:
            print("User terminated.")
        finally:
            self.socket.close()
            sys.exit()

    def listen(self):
        self.socket.bind((self.args.target, self.args.port))
        self.socket.listen(5)
        print(f"Listening as {self.args.target}:{self.args.port}")
        while True:
            client_socket, _ = self.socket.accept()
            client_thread = threading.Thread(target=self.handle, args=(client_socket,))
            client_thread.start()

    def handle(self, client_socket):
        try:
            if self.args.execute:
                output = execute(self.args.execute)
                client_socket.send(output.encode())
            elif self.args.upload:
                file_buffer = b""
                while True:
                    data = client_socket.recv(4096)
                    if data:
                        file_buffer += data
                    else:
                        break
                with open(self.args.upload, "wb") as f:
                    f.write(file_buffer)
                message = f"Saved file {self.args.upload}"
                client_socket.send(message.encode())
            elif self.args.command:
                cmd_buffer = b""
                while True:
                    try:
                        client_socket.send(b"BHP $ ")
                        while "\n" not in cmd_buffer.decode():
                            cmd_buffer += client_socket.recv(64)
                        response = execute(cmd_buffer.decode())
                        if response:
                            client_socket.send(response.encode())
                        cmd_buffer = b""
                    except Exception as e:
                        print(f"Error processing command: {e}")
                        client_socket.send(f"Error: {e}\n".encode())
        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            print("Closing client connection.")
            client_socket.close()

if __name__ == "__main__":
    print("NetCat Clone")
    parser = argparse.ArgumentParser(
        description="BHP Net Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''Example:
        netcat_clone.py -t 192.168.1.108 -p 5555 -l -c # command shell
        netcat_clone.py -t 192.168.1.108 -p 5555 -l -u=mytest.txt # upload to file
        netcat_clone.py -t 192.168.1.108 -p 5555 -l -e="cat /etc/passwd" # execute command
        echo 'ABC' | ./netcat_clone.py -t 192.168.1.108 -p 5555
        netcat_clone.py -t 192.168.1.108 -p 5555 # connect to server
        '''))
    parser.add_argument("-c", "--command", action="store_true", help="command shell")
    parser.add_argument("-e", "--execute", help="execute specified command")
    parser.add_argument("-l", "--listen", action="store_true", help="listen")
    parser.add_argument("-p", "--port", type=int, default=5555, help="specified port")
    parser.add_argument("-t", "--target", default="192.168.1.203", help="specified IP")
    parser.add_argument("-u", "--upload", help="upload file")
    args = parser.parse_args()
    if args.listen:
        buffer = ""
    else:
        try:
            buffer = sys.stdin.read()
        except EOFError:  # EOF (Strg + D) abfangen
            buffer = ""

    nc = NetCat(args, buffer.encode())
    nc.run()
