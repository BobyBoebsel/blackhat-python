import socket

target_host = "www.google.com"
target_port = 9997

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

client.sendto("AAABBBCCC".encode(), (target_host, target_port))

data, addr = client.recvfrom(4096)
print(data.decode())

client.close()