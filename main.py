import server
import whitebored

if __name__ == '__main__':

    whitebored.hints()
    
    my_name = input('Your username: ')
    their_name = input('Their username: ')
    channel = input('Channel: ')
    
    client = server.IRCclient(my_name, channel)
    
    whitebored.WhiteBored(client, their_name).begin()
