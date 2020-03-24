#Main loop#
import turtle
import threading

#Screen Shotting#
import time

def hints():

    print('Welcome to WhiteBored, a really, *really* long project by Henry Jaspars\n')
    print('-'*71)
    print('Hints: ')
    print('* To draw, drag mouse on the screen')
    print('* To clear, press C')
    print('* To quit, press Q')
    print('* To capture screen, press K')
    print('* To change colors, press Left/Right arrows')
    print('* To change drawing size, press Up/Down arrows')
    print('-'*71, '\n')

def onmove(self, fun, add=None):

    if fun is None:
        self.cv.unbind('<Motion>')
    else:
        def eventfun(event):
            fun(self.cv.canvasx(event.x) / self.xscale, -self.cv.canvasy(event.y) / self.yscale)
        self.cv.bind('<Motion>', eventfun, add)

def user_text(resp):                                            #Finds the username and text of a private message

    username = resp[0][1:].split('!')[0]
    if len(resp) >= 4:
        text = resp[3][1:]
        text = text.strip()
    else:
        text = ''
    return username, text
       
class WhiteBored:

    def __init__(self, client, receiver_username, canvas_size = (1920, 1080), send_marker = turtle.Turtle(),
                 receive_marker = turtle.Turtle(), byte_packet_size = 64, verbose = False):

        '''
        Initialises a WhiteBoard class across an existing client, with
        an existing canvas, transmitting commands at a rate of byte_packet_size
        bytes per packet.
        '''
        
        self.canvas_size = canvas_size
        
        self.client = client
        self.receiver_username = receiver_username
        
        self.byte_packet_size = byte_packet_size//4
        self.stream = []
        self.byte_stream = None
        
        self.characters = [chr(index) for index in range(65, 91)] + [chr(index) for index in range(97, 123)]
        self.special_packets = {'$PUP',                         #Mouse release (marker pen-up)
                                '$PDW',                         #Mouse drag (marker pen-down)
                                '$LFT',                         #Left-key press (toggle marker color left)
                                '$RGT',                         #Right-key press (toggle marker color right)
                                '$UP_',                         #Up-key press (increase marker size)
                                '$DWN',                         #Down-key press (decrease marker size)
                                '$CLR',                         #c-key press (clear screen)
                                '$QUT'}                         #q-key press (quit)
        
        ##Turtle variables##
        
        self.colors = ['black', 'white', 'red', 'green', 'blue']
        self.MOVING, self.DRAGGING = 0, 1
        self.state = self.MOVING

        #The marker you have control over, which is sent#
        self.send_marker = send_marker
        self.send_marker.speed(0)
        self.send_color_index = 0
        self.send_pen_size = 8
        self.send_marker.pensize(self.send_pen_size)

        #The marker which is received over the IRC channel#
        self.receive_marker = receive_marker
        self.receive_marker.speed(0)
        self.receive_marker.penup()
        self.receive_color_index = 0
        self.receive_pen_size = 8
        self.receive_marker.pensize(self.receive_pen_size)

        self.verbose = verbose
        
    ##Mouse DND handler##

    def move_handler(self, x, y):
    
        if self.state != self.MOVING:                           #ignore stray events
            return
        onmove(self.canvas, None)                               #avoid overlapping events
        self.send_marker.penup()
        self.send_marker.setheading(self.send_marker.towards(x, y))
        self.send_marker.goto(x, y)
        onmove(self.canvas, self.move_handler)

    def click_handler(self, x, y):
        
        self.send_marker.onclick(None)                          #disable until release
        onmove(self.canvas, None)                               #disable competing handler
        self.send_marker.onrelease(self.release_handler)        #watch for release event
        self.send_marker.ondrag(self.drag_handler)              #motion is now self.DRAGGING until release
        self.state = self.DRAGGING
        self.append_to_stream((int(x), int(y)))
        self.append_to_stream('$PDW')

    def release_handler(self, x, y):
        
        self.send_marker.onrelease(None)                        #disable until click
        self.send_marker.ondrag(None)                           #disable competing handler
        self.send_marker.onclick(self.click_handler)            #watch for click event
        onmove(self.canvas, self.move_handler)                  #self.DRAGGING is now motion until click
        if self.state != self.MOVING:
            self.state = self.MOVING
            self.append_to_stream('$PUP')
            
    def drag_handler(self, x, y):
        
        if self.state != self.DRAGGING:                         #ignore stray events
            return
        self.append_to_stream((int(x), int(y)))
        self.send_marker.ondrag(None)                           #disable event inside event handler
        self.send_marker.pendown()
        self.send_marker.setheading(self.send_marker.towards(x, y))
        self.send_marker.goto(x, y)
        self.send_marker.ondrag(self.drag_handler)              #reenable event on event handler exit

    ##Appearance methods for the send_marker##
        
    def set_colour(self, marker, color_index):                  #Sets the color of a marker and its appearance

        marker.pencolor(self.colors[color_index])
        marker.color(self.colors[color_index])
            
    def change_marker_left(self):                               #Toggles the marker color left across self.colors

        self.append_to_stream('$LFT')
        self.send_color_index = (self.send_color_index - 1)%len(self.colors)
        self.set_colour(self.send_marker, self.send_color_index)

    def change_marker_right(self):                              #Toggles the marker color right across self.colors

        self.append_to_stream('$RGT')
        self.send_color_index = (self.send_color_index + 1)%len(self.colors)
        self.set_colour(self.send_marker, self.send_color_index)

    def increase_pensize(self):

        self.append_to_stream('$UP_')
        if self.send_pen_size < 50:
            self.send_pen_size += 1
        self.send_marker.pensize(self.send_pen_size)

    def decrease_pensize(self):

        self.append_to_stream('$DWN')
        if self.send_pen_size > 1:
            self.send_pen_size -= 1
        self.send_marker.pensize(self.send_pen_size)

    def clear(self):                                            #Clears all the work of the pen_marker

        self.append_to_stream('$CLR')
        self.send_marker.clear()

    def capture(self):

        time_string = f'Capture_{self.receiver_username}_{time.strftime("%d-%m-%Y %H-%M-%S")}'
        turtle.getscreen().getcanvas().postscript(file = time_string)

    ##Protocol methods##
        
    def to_unicode(self, command):

        '''
        Converts bytes from tuple to bytes using Unicode
        '''
        
        if type(command) is tuple:
            x1, x2 = divmod(command[0] + self.canvas_size[0]//2, len(self.characters))
            y1, y2 = divmod(command[1] + self.canvas_size[1]//2, len(self.characters))
            return (self.characters[x1] + self.characters[x2] + self.characters[y1] + self.characters[y2])
        else:
            return command
        
    def from_unicode(self, byte_chunk):

        '''
        Decodes the unicode generated as above into
        turtle actions and protocols
        '''

        if byte_chunk[0] == '$':                                #Special token
            
            if byte_chunk == '$PUP':
                self.receive_marker.penup()
            elif byte_chunk == '$PDW':
                self.receive_marker.pendown()
            elif byte_chunk == '$LFT':
                self.receive_color_index = (self.receive_color_index - 1)%len(self.colors)
                self.set_colour(self.receive_marker, self.receive_color_index)
            elif byte_chunk == '$RGT':
                self.receive_color_index = (self.receive_color_index + 1)%len(self.colors)
                self.set_colour(self.receive_marker, self.receive_color_index)
            elif byte_chunk == '$UP_':
                self.receive_pen_size += 1
                self.receive_marker.pensize(self.receive_pen_size)
            elif byte_chunk == '$DWN':
                self.receive_pen_size -= 1
                self.receive_marker.pensize(self.receive_pen_size)
            elif byte_chunk == '$CLR':
                self.receive_marker.clear()
            elif byte_chunk == '$QUT':
                self.quit_connection()

        else:                                                   #A tuple (coordinates)

            try:
                char_x1, char_x2, char_y1, char_y2 = byte_chunk
                x1 = self.characters.index(char_x1)
                x2 = self.characters.index(char_x2)
                x = len(self.characters)*x1 + x2 - self.canvas_size[0]//2
                
                y1 = self.characters.index(char_y1)
                y2 = self.characters.index(char_y2)
                y = len(self.characters)*y1 + y2 - self.canvas_size[1]//2

                self.receive_marker.setheading(self.receive_marker.towards(x, y))
                self.receive_marker.goto(x, y)
                
            except ValueError:
                pass

    def show_stream(self):      

        '''
        Reads a stream and copies the instructions onto the canvas
        '''

        while self.thread_running:
            resp = self.client.receive().strip().split('\n')
            if resp != ['']:
                for line in resp:
                    if 'PRIVMSG' in line:
                        user, text = user_text(line.split(' '))
                        text = text.replace(':', '').replace('\r', '')
                        if user == self.receiver_username and text != 'PONG':
                            for index in range(0, len(text), 4):
                                byte_chunk = text[index: index + 4]
                                self.from_unicode(byte_chunk)   #Carries out the received action
            
    def append_to_stream(self, command):

        '''
        Appends a command to the stream, and releases it along the client if
        it is of the required length
        '''

        self.stream.append(command)
        if len(self.stream) == self.byte_packet_size or command[0] == '$':
            self.byte_stream = ''.join([self.to_unicode(_command) for _command in self.stream])
            if self.verbose:
                print(self.byte_stream)
            self.client.chat(self.receiver_username, self.byte_stream)
            self.stream = []                                    #Resets the stream
        
    def handshake(self):                                        #Need to catch if user isn't there yet

        '''
        Begins conversation with receiver
        '''
        
        self.client.chat(self.receiver_username, 'PING')
        while True:
            resp = self.client.receive().strip().split(' ')
            user, text = user_text(resp)
            if user == self.receiver_username and 'PRIVMSG' in resp:
                self.client.chat(self.receiver_username, 'PONG')
                if text == 'PONG':
                    break                    
        print('Connection established')
        
    def quit_connection(self):

        '''
        Quits connection
        '''

        self.append_to_stream('$QUT')
        self.thread_running = False
        self.client.leave('Connection closed')
        try:
            turtle.bye()
        except turtle.Terminator:
            pass
        print('Connection closed')
        quit(1)

    ##Begins the WhiteBoard chat##
                    
    def begin(self):

        '''
        Starts up the screen and conversation handler.
        '''
        
        self.handshake()

        self.canvas = turtle.Screen()

        self.canvas.setup(500, 600)
        self.canvas.screensize(*self.canvas_size)
        
        self.canvas.listen()

        self.canvas.onkey(self.clear, 'c')                      #Clear screen
        self.canvas.onkey(self.quit_connection, 'q')            #Quit connection
        self.canvas.onkey(self.capture, 'k')                    #Capture
        self.canvas.onkey(self.change_marker_left, 'Left')      #Change marker colors
        self.canvas.onkey(self.change_marker_right, 'Right')
        self.canvas.onkey(self.increase_pensize, 'Up')          #Change pen size
        self.canvas.onkey(self.decrease_pensize, 'Down')

        onmove(self.canvas, self.move_handler)
        self.send_marker.onclick(self.click_handler)

        self.thread_running = True
        self.thread = threading.Thread(target = self.show_stream, daemon = True).start()

        self.canvas.mainloop()
        
        self.quit_connection()
