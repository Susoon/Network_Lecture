import sys
import time
import socket
import MyPacket
from threading import Thread

"Use this method to write Packet log"
def writePkt(logFile, procTime, pktNum, event):
    logFile.write('{:1.3f} pkt: {} | {}\n'.format(procTime, pktNum, event))
    logFile.flush()

"Use this method to write ACK log"
def writeAck(logFile, procTime, ackNum, event):
    logFile.write('{:1.3f} ACK: {} | {}\n'.format(procTime, ackNum, event))
    logFile.flush()

"Use this method to write final throughput log"
def writeEnd(logFile, throughput):
    logFile.write('File transfer is finished.\n')
    logFile.write('Throughput : {:.2f} pkts/sec\n'.format(throughput))
    logFile.flush()


def fileReceiver():
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serverSocket.bind(('', 10080))

    Pbuf = MyPacket.PacketBuffer(0)
    rhandler = MyPacket.RecvHandler(Pbuf, serverSocket)

    rhandler.recv(writePkt, writeAck, writeEnd, 2048)
    
    rhandler.write()



if __name__=='__main__':
    fileReceiver()
