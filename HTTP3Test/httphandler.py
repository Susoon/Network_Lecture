import sys
from threading import Thread
import time
from socket import *

img = 0
idx = 1
sct = 2
cki = 3
fbd = 403
not_found = 404

EOL = '\r\n'

code = { 200 : 'OK', 403 : 'Forbidden', 404 : 'Not Found' }

userdata = {}

class HTTPhandler:
    cookie_value = 0

    def __init__(self, req_msg):
        self.client_address = ()
        self.path = ''
        self.res_msg = bytearray()
        self.client_cookie = HTTPhandler.cookie_value + 100
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
        EOH = EOH + 4
        return self.req_msg[EOH:EOH + size]

    def write_data(self, data):
        self.res_msg += data


#Followings are about adding header
    def send_status_code(self, status_code):
        self.res_msg += b'HTTP/1.1 '
        self.res_msg += (str(status_code) + ' ').encode('utf-8')
        self.res_msg += (code[status_code] + ' ').encode('utf-8')
        self.res_msg += EOL.encode('utf-8')

    def send_header(self, header_type, header_content):
        self.res_msg += header_type.encode('utf-8') + b': ' + header_content.encode('utf-8')
        self.res_msg += EOL.encode('utf-8')

    def end_headers(self):
        self.res_msg += EOL.encode('utf-8')
        

#Following is about adding user
    def adduser(self, cur_time, cid, cpwd):
        self.client_cookie_time = cur_time
        userdata[self.client_cookie] = (self.client_address[0], self.client_address[1], self.client_cookie_time, cid, cpwd)
        self.client_cookie = HTTPhandler.cookie_value
        HTTPhandler.cookie_value += 1

#Followings are about parsing message
    def parse_msg(self):
        self.parse_addr()
        self.parse_path()
        self.parse_cookie()

    def parse_cookie(self):
        cookie_idx = self.req_msg.find('cookievalue=')
        if cookie_idx == -1:
            return
        cookie_idx = cookie_idx + 12
        EOL_idx = self.req_msg[cookie_idx:].find('\r\n') + cookie_idx
        self.client_cookie = int(self.req_msg[cookie_idx:EOL_idx])

    def parse_addr(self):
        host_idx = self.req_msg.find('Host: ') + 6
        EOL_idx = self.req_msg[host_idx:].find('\r\n') + host_idx
        self.client_address = self.req_msg[host_idx:EOL_idx].split(':')

    def parse_path(self):
        path_idx = self.req_msg.find('/')
        end_of_path_idx = self.req_msg[path_idx:].find('H') + path_idx
        self.path = self.req_msg[path_idx:end_of_path_idx - 1]

    def parse_userdata(self, data, cur_time):
        if self.client_cookie in userdata.keys():
            return
        id_idx = data.index('=')
        a_idx = data.index('&')
        uid = data[id_idx + 1:a_idx]
        pwd_idx = data[a_idx:].index('=')
        upwd = data[pwd_idx:]
        self.adduser(cur_time, uid, upwd)

    def headers(self, header_type):
        h_idx = self.req_msg.find(header_type)
        h_idx = h_idx + len(header_type) + 2
        EOL_idx = self.req_msg[h_idx:].find('\r\n') + h_idx
        return self.req_msg[h_idx:EOL_idx]

    def check_file_exist(self):
        try:
            file_path = "./testfiles/" + self.path
            f = open(file_path, 'rb')
            f.close()
            return 0
        except:
            return 1

#Followings are about handling each method
    def do_GET(self): 
        if self.check_file_exist():
            self.send_msg(not_found)
        elif self.path == '/' or self.path == "/secret.html":
            self.secret()
        elif self.path == "/cookie.html":
            self.cookie()
        elif 'mp4' in self.path:
            self.send_mp4()
        else:
            self.send_img()

    def do_POST(self):
        cur_time = time.time()
        try:
            buf = self.data(int(self.headers('Content-Length')))
            self.parse_userdata(buf, cur_time)
            self.secret()
        except ValueError:
            pass


#Followings are about handling html files
    def index(self):
        self.path = '/index.html'
        self.send_html(200, idx)

    def secret(self):
        cur_time = time.time()
        if self.client_cookie in userdata.keys():
            if cur_time - userdata[self.client_cookie][2] > 30:
                del userdata[self.client_cookie]
                self.index()
        self.path = '/secret.html'
        self.send_html(200, sct)

    def cookie(self):
        ucookie = 30 - (time.time() - userdata[self.client_cookie][2])
        if ucookie < 0:
            del userdata[self.client_cookie]
            self.index()
        cookie_html_data = """
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="utf-8">
                <title>Welcome %s</title>
            </head>
            <body>
                <p> Hello %s </p>
                <p> %d seconds left until your cookie expires. </p>
            </body>
        </html>
        """ % (userdata[self.client_cookie][3], userdata[self.client_cookie][3], ucookie)
        cookie_html = open('cookie.html', 'w')
        cookie_html.write(cookie_html_data)
        cookie_html.close()
        self.send_html(200, cki)

#Followings are about sending data
    def send_msg(self, status_code):
        buf = str(status_code) + code[status_code]
        self.send_status_code(status_code)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.send_header('Content-length', str(len(buf)))
        if self.client_cookie >= HTTPhandler.cookie_value:
            self.send_header('Set-Cookie', 'cookievalue=%d' %(HTTPhandler.cookie_value))
        else:
            self.send_header('Set-Cookie', 'cookievalue=%d' %(self.client_cookie))
        self.end_headers()
        self.write_data(buf.encode('utf-8'))

    def send_mp4(self):
        ret_img = open('./testfiles/' + self.path, 'rb')
        buf = ret_img.read()
        ret_img.close()
        self.send_status_code(200)
        self.send_header('Content-type', 'video/mp4')
        self.send_header('Content-length', str(len(buf)))
        print("Path = %s, Len = %d" %(self.path, len(buf)))
        if self.client_cookie >= HTTPhandler.cookie_value:
            self.send_header('Set-Cookie', 'cookievalue=%d' %(HTTPhandler.cookie_value))
        else:
            self.send_header('Set-Cookie', 'cookievalue=%d' %(self.client_cookie))
        self.end_headers()
        self.write_data(buf)

    def send_img(self):
        ret_img = open('./testfiles/' + self.path, 'rb')
        buf = ret_img.read()
        ret_img.close()
        self.send_status_code(200)
        self.send_header('Content-type', 'image/jpeg')
        self.send_header('Content-length', str(len(buf)))
        if self.client_cookie >= HTTPhandler.cookie_value:
            self.send_header('Set-Cookie', 'cookievalue=%d' %(HTTPhandler.cookie_value))
        else:
            self.send_header('Set-Cookie', 'cookievalue=%d' %(self.client_cookie))
        self.end_headers()
        self.write_data(buf)

    def send_html(self, status_code, status_idx):
        ret_file = open('./testfiles/' + self.path, 'rb')
        buf = ret_file.read()
        ret_file.close()
        self.send_status_code(status_code)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Content-length', str(len(buf)))
        if self.client_cookie >= HTTPhandler.cookie_value:
            self.send_header('Set-Cookie', 'cookievalue=%d' %(HTTPhandler.cookie_value))
        else:
            self.send_header('Set-Cookie', 'cookievalue=%d' %(self.client_cookie))
        self.end_headers()
        self.write_data(buf)

def connect_http_persistent(serverSocket):
    connectionSocket, addr = serverSocket.accept()
    print("Server Connected Persistently : Client Addr = %s, Client Port = %d" %(addr[0], addr[1]))
    accept_time = time.time()
    while True:
        req_msg = None
        while not req_msg:
            req_msg = connectionSocket.recv(10 * 1024)
            if time.time() - accept_time > 5:
                connectionSocket.close()
                print("Time out : Client Addr = %s, Client Port = %d" %(addr[0], addr[1]))
                return
        http = HTTPhandler(req_msg.decode())
        http.do_method()
        connectionSocket.send(http.res_msg)
    connectionSocket.close()

def connect_http_non_persistent(serverSocket):
    while True:
        connectionSocket, addr = serverSocket.accept()
        print("Server Connected Non-Persistently: Client Addr = %s, Client Port = %d" %(addr[0], addr[1]))
        req_msg = connectionSocket.recv(10 * 1024)
        http = HTTPhandler(req_msg.decode())
        http.do_method()
        connectionSocket.send(http.res_msg)
        connectionSocket.close()
        print("Server Disconnected : Client Addr = %s, Client Port = %d" %(addr[0], addr[1]))

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
