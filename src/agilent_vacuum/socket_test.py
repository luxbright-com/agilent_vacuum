import socket
import telnetlib


def tcp_test():
    host_ip, server_port = "168.129.1.230", 23
    data = b"\x02\x80\x31\x36\x33\x31000002\x0384"

    # Initialize a TCP client socket using SOCK_STREAM
    tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Establish connection to TCP server and exchange data
        tcp_client.settimeout(5)
        tcp_client.connect((host_ip, server_port))
        print("socket connected")
        tcp_client.sendall(data)
        print("data sent")

        # Read data from the TCP server and close the connection
        received = tcp_client.recv(1024)
    finally:
        tcp_client.close()

    print ("Bytes Sent:     {}".format(data))
    print ("Bytes Received: {}".format(received.decode()))


def telnet_test():
    tn = telnetlib.Telnet("192.168.1.230", 23)
    data = b"\x02\x80\x31\x36\x33\x31000002\x0384"
    tn.write(data)
    print(tn.read_until(b"\x03"))
    print(tn.read_eager())
    print(tn.read_eager())


if __name__ == '__main__':
    telnet_test()
    #tcp_test()
