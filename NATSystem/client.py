import clientModule

if __name__ == "__main__":
    print("Enter your ID and server IP address")
    clientID = input("ID : ")
    serverIP = input("Server IP :")

    clientHandler = clientModule.client(clientID, serverIP)

    clientHandler.chatManager()
