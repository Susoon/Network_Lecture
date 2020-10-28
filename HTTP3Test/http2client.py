import sys
import time
from socket import *

serverIP = 'localhost'
serverPort = 10080
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverIP, serverPort))


