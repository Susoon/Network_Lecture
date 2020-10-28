import socket
from threading import Thread
import time

reg = 'reg'
offline = 'off-line'
unreg = 'unreg'

class server:
    def __init__(self):
        self.regList = {}
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.serverSocket.bind(('', 10080))

    def parseAddr(self, addr):
        split_addr = addr.split(':')
        return (split_addr[0], int(split_addr[1]))

    def makeMsg(self, clientid, clientAddr, state):
        msg = 'server;'
        msg += state + ';'
        msg += clientid + ';'
        msg += clientAddr
        return msg.encode()

    def sendList(self, id, addr):
        clientAddr = self.parseAddr(addr)
        for key in self.regList:
            clientData = self.regList[key][0]
            if self.inSameSubnet(self.regList[id][1], self.regList[key][1]):
                clientData = self.regList[key][1]
            msg = self.makeMsg(key, clientData, reg)
            self.serverSocket.sendto(msg, clientAddr)

    def recv(self):
        while True:
            msg, client = self.serverSocket.recvfrom(1024)
            msg = msg.decode()
            # data = [clientID, clientIP:clientPort(,exit)]
            data = msg.split(';')
            print(' '.join(data) + '\t' + client[0] + ':' + str(client[1]))
            if 'unreg' in data:
                self.propagate(data[0], unreg)
                del self.regList[data[0]]
            elif 'Keep Alive' in data:
                self.regList[data[0]] = (self.regList[data[0]][0], self.regList[data[0]][1], time.time())
            else:
                clientAddr = client[0] + ':' + str(client[1])
                self.regList[data[0]] = (clientAddr, data[2], time.time())
                self.propagate(data[0], reg)
                self.sendList(data[0], clientAddr)

    def inSameSubnet(self, c1Addr, c2Addr):
        client1Addr = c1Addr.split(':')
        client1IP = client1Addr[0]
        client2Addr = c2Addr.split(':')
        client2IP = client2Addr[0]

        client1IP = client1IP.split('.')
        client2IP = client2IP.split('.')

        del client1IP[-1]
        del client2IP[-1]

        if client1IP == client2IP:
            return True
        else:
            return False


    def propagate(self, clientid, state):
        clientAddr = self.regList[clientid][0]
        for key in self.regList:
            if state != 'unreg' and key == clientid:
                continue
            addr = self.parseAddr(self.regList[key][0])
            if self.inSameSubnet(self.regList[clientid][1], self.regList[key][1]):
                clientAddr = self.regList[clientid][1]
            self.serverSocket.sendto(self.makeMsg(clientid, clientAddr, state), addr)
            
    def checkClient(self):
        while True:
            try:
                for key in self.regList:
                    if time.time() - self.regList[key][2] >= 30:
                        self.propagate(key, offline)
                        print(key + ' off-line\t' + self.regList[key][0] + '\t' + self.regList[key][1])
                        del self.regList[key]
            except RuntimeError:
                continue
            except KeyError:
                continue

    def serverManager(self):
        print("Server - ONLINE!")
        myAddr = self.serverSocket.getsockname()
        print("Server IP : %s, Port : %d" %(myAddr[0], myAddr[1]))
        thCheck = Thread(target=self.checkClient, args=())
        try:
            thCheck.start()
        except KeyboardInterrupt:
            thCheck.join()
            return
        self.recv()
