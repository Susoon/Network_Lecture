import sys
import os
from threading import Thread
import time
from socket import *

fbd = 403
not_found = 404

EOL = '\r\n'

code = { 101 : 'Switching Protocol', 200 : 'OK', 403 : 'Forbidden', 404 : 'Not Found' }

class HTTPhandler:
    def __init__(self, req_msg):
        self.path = ''
        self.res_msg = bytearray()
        self.req_msg = req_msg

    def do_method(self):
        self.parse_msg()
        method = self.req_msg[:4]
        if 'GET' in method:
            self.do_GET()
        else:
            self.do_POST()

#Followings are about data manipulation    
    def data(self, size):
        EOH = self.req_msg.find('\r\n\r\n')
        EOH = EOH + len('\r\n\r\n')
        return self.req_msg[EOH:EOH + size]

    def write_data(self, data):
        self.res_msg += data


#Followings are about adding header
    def send_status_code(self, status_code):
        self.res_msg += b'HTTP/2 '
        self.res_msg += (str(status_code) + ' ').encode()
        self.res_msg += (code[status_code] + ' ').encode()
        self.res_msg += EOL.encode()

    def send_header(self, header_type, header_content):
        self.res_msg += header_type.encode() + b': ' + header_content.encode()
        self.res_msg += EOL.encode()

    def end_headers(self):
        self.res_msg += EOL.encode()
        
#Followings are about parsing message
    def parse_msg(self):
        self.parse_path()

    def parse_path(self):
        path_idx = self.req_msg.find('/')
        end_of_path_idx = self.req_msg[path_idx:].find('H') + path_idx
        self.path = './testfiles/' + self.req_msg[path_idx:end_of_path_idx - 1]

    def headers(self, header_type):
        h_idx = self.req_msg.find(header_type)
        h_idx = h_idx + len(header_type) + 2
        EOL_idx = self.req_msg[h_idx:].find('\r\n') + h_idx
        return self.req_msg[h_idx:EOL_idx]

#Followings are about handling each method
    def do_GET(self): 
        if not os.path.exists(self.path):
            self.send_msg(not_found)
        elif '.html' in self.path:
            self.send_html()
        elif '.mp4' in self.path:
            self.send_mp4()
        else:
            self.send_img()

    def do_POST(self):
        cur_time = time.time()
        try:
            buf = self.data(int(self.headers('Content-Length')))
            self.secret()
        except ValueError:
            pass

#Followings are about sending data
    def send_msg(self, status_code):
        buf = str(status_code) + code[status_code]
        self.send_status_code(status_code)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.send_header('Content-length', str(len(buf)))
        self.end_headers()
        self.write_data(buf.encode())

    def send_img(self):
        ret_img = open(self.path, 'rb')
        buf = ret_img.read(10 * 1024 * 1024)
        ret_img.close()
        self.send_status_code(200)
        self.send_header('Content-type', 'image/jpeg')
        self.send_header('Content-length', str(len(buf)))
        self.end_headers()
        self.write_data(buf)

    def send_mp4(self):
        ret_mp4 = open(self.path, 'rb')
        buf = ret_mp4.read()
        ret_mp4.close()
        self.send_status_code(200)
        self.send_header('Content-type', 'video/mp4')
        self.send_header('Content-length', str(len(buf)))
        self.end_headers()
        self.write_data(buf)

    def send_html(self, status_code):
        ret_file = open(self.path, 'rb')
        buf = ret_file.read(10 * 1024 * 1024)
        ret_file.close()
        self.send_status_code(status_code)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Content-length', str(len(buf)))
        self.end_headers()
        self.write_data(buf)

def connect_http_persistent(serverSocket):
    connectionSocket, addr = serverSocket.accept()
    #print("Server Connected Persistently : Client Addr = %s, Client Port = %d" %(addr[0], addr[1]))
    accept_time = time.time()
    while True:
        req_msg = None
        while not req_msg:
            req_msg = connectionSocket.recv(10 * 1024)
            if time.time() - accept_time > 5:
                connectionSocket.close()
                #print("Time out : Client Addr = %s, Client Port = %d" %(addr[0], addr[1]))
                return
        http = HTTPhandler(req_msg.decode())
        http.do_method()
        connectionSocket.send(http.res_msg)
    connectionSocket.close()

def connect_http_non_persistent(serverSocket):
    while True:
        connectionSocket, addr = serverSocket.accept()
        #print("Server Connected Non-Persistently: Client Addr = %s, Client Port = %d" %(addr[0], addr[1]))
        req_msg = connectionSocket.recv(10 * 1024)
        http = HTTPhandler(req_msg.decode())
        http.do_method()
        connectionSocket.send(http.res_msg)
        connectionSocket.close()
        #print("Server Disconnected : Client Addr = %s, Client Port = %d" %(addr[0], addr[1]))

if __name__ == "__main__":
    serverPort = 10080
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(('', serverPort))
    serverSocket.listen(5)

    connect_http = (connect_http_non_persistent, connect_http_persistent)

    persi = int(input("If you want persistent mode, enter 1. If not, enter 0.\n"))
    print('The HTTP server is ready to receive.')

    while True:
        th = Thread(target = connect_http[persi], args = (serverSocket,))
        th.start()
