import socket
from threading import Thread
import time
import os

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

class client:
    def __init__(self, clientID, serverIP):
        self.clientID = clientID
        self.serverIP = serverIP
        self.regList = {}
        self.localIP = ''
        self.localSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.globalSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.online = False

    def inSameSubnet(self, c1Addr, c2Addr):
        client1Addr = c1Addr.split(':')
        client2Addr = c2Addr.split(':')
        client1IP = client1Addr[0]
        client2IP = client2Addr[0]
        client1IP = client1IP.split('.')
        client2IP = client2IP.split('.')

        del client1IP[-1]
        del client2IP[-1]

        if client1IP == client2IP:
            return True
        else:
            return False        


    def parseMsg(self, msg):
        data = msg.decode()
        data = data.split(';')
        if 'server' in data:
            self.parseAddr(data[1:])
        else:
            self.parseChat(data)

    def parseAddr(self, msg):
        if msg[0] == 'reg':
            self.regList[msg[1]] = msg[2]
            print(msg[1] + '\t\t' + msg[2])
        elif msg[0] == 'off-line':
            del self.regList[msg[1]]
            print(msg[1] + ' is off-line\t' + msg[2])
        elif msg[0] == 'unreg':
            if msg[1] == self.clientID:
                self.online = False
                self.close()
                return
            del self.regList[msg[1]]
            print(msg[1] +' is unregistered\t' + msg[2])
        
    def parseChat(self, msg):
        data = 'From ' + msg[0] + '\t\t' + '[' + msg[1] + ']'
        print(data)

    def parseText(self, text):
        if "@show_list" in text:
            for key in self.regList:
                print(key + "\t\t" + self.regList[key])
        elif "@chat" in text:
            self.chatTopeer(text[1:])
        elif "@exit" in text:
            self.unregistration()

    def conGlobal(self):
        msg = self.clientID + ';' + 'reg' + ';' + self.localIP + ':' + str(10081)
        self.online = True
        self.globalSock.sendto(msg.encode(), (self.serverIP, 10080))
        while self.online:
            msg = self.globalSock.recv(1024)
            self.parseMsg(msg)

    def unregistration(self):
        msg = self.clientID + ';' + 'unreg' + ';' + self.localIP + ':' + str(10081)
        self.globalSock.sendto(msg.encode(), (self.serverIP, 10080))
        self.online = False

    def close(self):
        self.globalSock.close()
        self.localSock.close()

    def keepAlive(self):
        prevTime = time.time()
        curTime = time.time()
        while self.online:
            curTime = time.time()
            if curTime - prevTime >= 10:
                prevTime = curTime
                msg = self.clientID + ';' + 'Keep Alive' + ';' + self.localIP + ':' + str(10081)
                try:
                    self.globalSock.sendto(msg.encode(), (self.serverIP, 10080))
                except:
                    break

    def conLocal(self):
        self.localSock.bind((self.localIP, 10081))
        while self.online:
            msg = self.localSock.recv(1024)
            self.parseMsg(msg)

    def chatTopeer(self, text):
        opponent = text[0]
        text = self.clientID + ';' + ' '.join(text[1:])
        try:
            peerAddr = self.regList[opponent].split(':')
            peerAddr = (peerAddr[0], int(peerAddr[1]))
            if self.inSameSubnet(self.localIP, peerAddr[0]):
                self.localSock.sendto(text.encode(), peerAddr)
            else:
                self.globalSock.sendto(text.encode(), peerAddr)
        except KeyError:
            print("There are no such client. Enter opponent again")

    def chatManager(self):
        print("%s - ONLINE!" %(self.clientID))

        self.localIP = get_ip_address()

        thConGlobal = Thread(target=self.conGlobal, args=())
        thConLocal = Thread(target=self.conLocal, args=())
        thKeepAlive = Thread(target=self.keepAlive, args=())
        
        thConGlobal.start()
        thConLocal.start()
        thKeepAlive.start()
        
        while self.online:
           text = input("\n")
           self.parseText(text.split()) 

        os._exit(0)

        thConGlobal.join()
        thConLocal.join()
        thKeepAlive.join()
