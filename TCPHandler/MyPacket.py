import time
import threading
import socket

alpha = 0.125

class Packet:
    def __init__(self, data, headerflag, ackNum = None):
        self.acked = 0
        self.retransmitt = False
        self.dropped = False
        self.sended = False
        self.sendTime = 0
        self.msg = None 
        self.end = False
        self.RTT = 0
        if headerflag is False:
            self.data = data
            self.ackNum = ackNum
        else:
            self.data = self.parse_data(data)

    def parse_data(self, data):
        header = data[:10].decode()
        mask = int(header[0])

        idx = header.find(' ')
        self.ackNum = int(data[1:idx])

        if mask == 1:
            self.end = True

        return data[10:]

    def make_pkt(self):
        # header byte num
        bytenum = 0
        # mask = X, X: last packet mask
        mask = str(int(self.end))

        header = mask
        bytenum = 1

        header += str(self.ackNum)
        bytenum += len(str(self.ackNum))
        
        empty_space = ''
        i = 0
        while i < 10 - bytenum:
            empty_space += ' '
            i += 1
        
        self.msg = header.encode() + empty_space.encode() + self.data

    def sendto(self, conSoc, recvAddr):
        self.make_pkt()
        conSoc.sendto(self.msg, recvAddr)
        self.sended = True


class PacketBuffer:
    def __init__(self, windowSize):
        self.buf = list()
        self.wnd = windowSize
        self.logfilename = None
        self.head = 0

    def __getitem__(self, index):
        return self.buf[index]

    def append(self, packet):
        self.buf.append(packet)


class SendHandler:
    def __init__(self, Pbuf, conSock, logfile):
        self.buf = Pbuf
        self.conSock = conSock
        self.myaddr = conSock.getsockname()
        self.buf.logfilename = None 
        self.logfile = logfile
        self.length = 0
        self.startTime = time.time()
        self.sended = 0
        self.RTO = 1
        self.avgRTT = 1
        self.RTTVAL = 0.5

    def calRTO(self, RTT):
        self.avgRTT = (1 - alpha) * self.avgRTT + alpha * RTT
        self.RTTVAL = 0.75 * self.RTTVAL + 0.25 * abs(RTT - self.avgRTT)
        self.RTO = self.avgRTT + self.RTTVAL * 4
        if self.RTO > 60:
            self.RTO = 60
        if self.RTO < 0.2:
            self.RTO = 0.2

    def calRTT(self, idx):
        return time.time() - self.buf[idx].sendTime

    def check_acked(self, writeAck):
        while True:
            if self.buf.head > self.length - 1:
                self.goodput = len(self.buf.buf) / (time.time() - self.startTime)
                #print("[CHECK] ENDED")
                break
            try:
                data = self.conSock.recv(2048)
            except ConnectionRefusedError:
                self.buf.head = self.length - 1
                self.goodput = len(self.buf.buf) / (time.time() - self.startTime)
                #print("[CHECK] ENDED")
                break

            tmp_pkt = Packet(data, True)
    
            self.buf[tmp_pkt.ackNum].acked += 1

            if self.buf[tmp_pkt.ackNum].acked == 4:
                self.buf.head = tmp_pkt.ackNum 
                self.sended = self.buf.head
                self.buf[tmp_pkt.ackNum + 1].retransmitt = True
                self.buf[tmp_pkt.ackNum + 1].dropped = True
                writeAck(self.logfile, time.time() - self.startTime, tmp_pkt.ackNum, "3 duplicated ACKs")
                continue

            writeAck(self.logfile, time.time() - self.startTime, tmp_pkt.ackNum, "received")

            if self.buf[tmp_pkt.ackNum].acked < 4:
                self.buf.head = tmp_pkt.ackNum + 1
                if self.buf[tmp_pkt.ackNum].acked == 1 and not self.buf[tmp_pkt.ackNum].retransmitt:
                    RTT = self.calRTT(tmp_pkt.ackNum)
                    self.buf[tmp_pkt.ackNum].RTT = RTT
                    self.calRTO(RTT)
                
    def sendto(self, recvAddr, writePkt):
        self.length = self.buf[-1].ackNum + 1
        end = False
        while True:
            if end and self.buf.head > self.length - 1:
                #print("[SENDTO] ENDED")
                break
            if self.sended - self.buf.head > self.buf.wnd:
                continue
            if self.sended == self.length - 1:
                end = True
            if self.buf[self.sended].sended == False:
                self.buf[self.sended].sendTime = time.time()
            try:
                self.buf[self.sended].sendto(self.conSock, recvAddr)
            except:
                self.buf.head == self.length - 1
                break

            if self.buf[self.sended].retransmitt == False:
                writePkt(self.logfile, time.time() - self.startTime, self.buf[self.sended].ackNum, "sent")
            else:
                writePkt(self.logfile, time.time() - self.startTime, self.buf[self.sended].ackNum, "retransmitt")
            self.sended += 1
            if self.sended == self.length:
                self.sended = self.buf.head

    def timer(self, writeAck, writeEnd):
        i = 0
        while True: 
            if self.buf.head == self.length - 1:
                #print("[TIMER] ENDED")
                break
            if not self.buf[i].sended:
                i = self.buf.head
                continue
            RTT = time.time() - self.buf[i].sendTime

            if RTT > self.RTO:
                writeAck(self.logfile, time.time() - self.startTime, self.buf[i].ackNum, "timeout since %.3f (timeout value %.3f)" %(self.buf[i].sendTime - self.startTime, self.RTO))
                self.RTO *= 2
                if self.RTO > 60:
                    self.RTO = 60
                self.sended = self.buf.head
                self.buf[i].retransmitt = True 
                i = self.buf.head
                continue

            i += 1

            if self.buf.head + self.buf.wnd < i:
                i = self.buf.head
            
            if i == len(self.buf.buf):
                i = self.buf.head


class RecvHandler:
    def __init__(self, Pbuf, conSock):
        self.buf = Pbuf
        self.conSock = conSock
        self.sendAddr = None
        self.dstFilename = None
        self.startTime = time.time()

    def parse_metadata(self, pkt):
        data = pkt.data.decode()
        idx = data.find(':')
        self.dstFilename = data[:idx]
        idx2 = data.find(';')
        self.sendAddr = (data[idx+1:idx2], int(data[idx2+1:]))
        self.buf.logfilename = self.dstFilename + '_receiving_log.txt'

    def recv(self, writePkt, writeAck, writeEnd, bufsize = 0):
        ackedNum = -1
        while True: 
            data = self.conSock.recv(bufsize)
            tmp_pkt = Packet(data, True)
            if tmp_pkt.ackNum == 0 and ackedNum == -1:
                self.parse_metadata(tmp_pkt)
                logfile = open(self.buf.logfilename, 'w')
            if tmp_pkt.ackNum != 0 and ackedNum == -1:
                continue
            if tmp_pkt.ackNum != ackedNum + 1:
                tmp_ack_pkt = Packet(b'ACK', False, ackedNum)
                writeAck(logfile, time.time() - self.startTime, tmp_ack_pkt.ackNum, "sent")
                tmp_ack_pkt.sendto(self.conSock, self.sendAddr)
                continue

            self.buf.append(tmp_pkt)
            writePkt(logfile, time.time() - self.startTime, tmp_pkt.ackNum, "received")

            tmp_ack_pkt = Packet(b'ACK', False, tmp_pkt.ackNum)
            tmp_ack_pkt.end = tmp_pkt.end
            tmp_ack_pkt.sendto(self.conSock, self.sendAddr)
            writeAck(logfile, time.time() - self.startTime, tmp_ack_pkt.ackNum, "sent")
            
            ackedNum += 1

            if tmp_pkt.end:
                goodput = len(self.buf.buf) / (time.time() - self.startTime)
                print("[RECEIVER] goodput : %f" %(goodput))
                writeEnd(logfile, goodput)
                logfile.close() 
                #print("[RECV] ENDED")
                break

    def write(self):
        dstfile = open(self.dstFilename, 'wb')
        i = 1
        while i < len(self.buf.buf):
            dstfile.write(self.buf[i].data)
            i += 1
        dstfile.close()



