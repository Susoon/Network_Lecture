import sys
import socket
import time
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
def writeEnd(logFile, throughput, avgRTT):
    logFile.write('File transfer is finished.\n')
    logFile.write('Throughput : {:.2f} pkts/sec\n'.format(throughput))
    logFile.write('Average RTT : {:.5f} ms\n'.format(avgRTT))

def fileSender(recvAddr, windowSize, srcFilename, dstFilename):
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    clientSocket.connect((recvAddr, 10080))

    logfile = open(dstFilename + '_sending_log.txt', 'w')

    Pbuf = MyPacket.PacketBuffer(windowSize)
    shandler = MyPacket.SendHandler(Pbuf, clientSocket, logfile)
    
    thSend = Thread(target=shandler.sendto, args=((recvAddr, 10080), writePkt))
    thAck = Thread(target=shandler.check_acked, args=(writeAck,))
    thTimer = Thread(target=shandler.timer, args=(writeAck, writeEnd))
    
    firstpacket = MyPacket.Packet((dstFilename + ':' + shandler.myaddr[0] + ';' + str(shandler.myaddr[1])).encode(), False, 0)
    shandler.buf.append(firstpacket)
    
    filedata = open(srcFilename, 'rb')
    ackNum = 1
    retdata = None
    
    while True:
        retdata = filedata.read(1024)
        if not retdata:
            shandler.buf[-1].end = True
            break
        shandler.buf.append(MyPacket.Packet(retdata, False, ackNum))
        ackNum += 1
    filedata.close() 

    thSend.start()
    thAck.start()
    thTimer.start()

    thSend.join()
    thAck.join()
    thTimer.join()

    i = 0
    totalRTT = 0
    length = shandler.length
    print("[SENDER] goodput : %f, avgRTT : %f" %(shandler.goodput, shandler.avgRTT))
    writeEnd(logfile, shandler.goodput, shandler.avgRTT * 1000)
    logfile.close()
    clientSocket.close()


if __name__=='__main__':
    recvAddr = sys.argv[1]  #receiver IP address
    windowSize = int(sys.argv[2])   #window size
    srcFilename = sys.argv[3]   #source file name
    dstFilename = sys.argv[4]   #result file name

    fileSender(recvAddr, windowSize, srcFilename, dstFilename)
