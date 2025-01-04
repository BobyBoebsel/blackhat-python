import socket

target_host = "www.google.com"
target_port = 80

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((target_host, target_port))

# In the book it is mistakenly written as "GET / HTTP/1.1\r\nHost: google.com\r\n\r\n" without .encode() 
# so it will give an error about str and bytes (datatypes) so we need to encode it to bytes

client.send("GET / HTTP/1.1\r\nHost: google.com\r\n\r\n".encode())
response = client.recv(4096)
print(response.decode())

client.close()