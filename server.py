import socket

class IRCclient:

    def __init__(self, username, channel, server = 'irc.freenode.net', port = 6667):

        self.username = username
        self.channel = channel
        self.server = server
        self.port = port
        
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((self.server, self.port))

        ##Join the channel##

        while True:
            
            self.resp = self.receive()
            
            if 'No Ident response' in self.resp:
                self.set_nick()

            if '376' in self.resp:                              #We're accepted, now join the channel
                self.enter(self.channel)

            if '433' in self.resp:                              #Username prefixed with _ if already in use
                self.username = f'_{self.username}'
                self.set_nick()

            if 'PING' in self.resp:                             #If PING send PONG with name of the server
                self.ping()

            if '366' in self.resp:                              #User has joined
                break

    ##Sending bytes##

    def send(self, message):                                    #Formatting and sends message
        self.conn.send(f'{message}\r\n'.encode('utf-8'))

    def enter(self, channel):                                   #Joins a channel
        self.send(f'JOIN {channel}')

    def chat(self, user, message):                              #Sends a DM to a user (also can send messages to the whole channel by setting user = channel) (need to fix this)
        self.send(f'PRIVMSG {user} :{message}')

    def kick(self, channel, user):                              #Kicks a user out
        self.send(f'KICK {channel} {user}')

    def ping(self):                                             #Responds to PING requests
        self.send(f'PONG : {self.resp.split(":")[1]}')

    def set_nick(self):                                         #Fixes username
        self.send(f'NICK {self.username}')
        self.send(f'USER {self.username} * * :{self.username}')

    def leave(self, message):                                   #Exits the chatroom
        self.send(f'QUIT {message}')
        
    ##Recieving bytes##
        
    def receive(self):                                          #Recieves and formats message
        return self.conn.recv(512).decode('utf-8')

