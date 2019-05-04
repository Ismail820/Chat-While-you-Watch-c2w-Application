# -*- coding: utf-8 -*-
from twisted.internet.protocol import Protocol
import logging
from c2w.protocol.type import types
import struct
import ipaddress
from twisted.internet import reactor
from c2w.main.constants import ROOM_IDS


logging.basicConfig()
moduleLogger = logging.getLogger('c2w.protocol.tcp_chat_client_protocol')


class c2wTcpChatClientProtocol(Protocol):

    def __init__(self, clientProxy, serverAddress, serverPort):
        """
        :param clientProxy: The clientProxy, which the protocol must use
            to interact with the Graphical User Interface.
        :param serverAddress: The IP address (or the name) of the c2w server,
            given by the user.
        :param serverPort: The port number used by the c2w server,
            given by the user.

        Class implementing the UDP version of the client protocol.

        .. note::
            You must write the implementation of this class.

        Each instance must have at least the following attribute:

        .. attribute:: clientProxy

            The clientProxy, which the protocol must use
            to interact with the Graphical User Interface.

        .. attribute:: serverAddress

            The IP address of the c2w server.

        .. attribute:: serverPort

            The port number used by the c2w server.

        .. note::
            You must add attributes and methods to this class in order
            to have a working and complete implementation of the c2w
            protocol.
        """
        #initializing the sequence number to zero 
        self.seql=0
        #initializing the resend counter to zero
        self.count=0
        self.repeat = None
        self.movielist = []
        self.userlist = []
        self.ackcm= None
        self.ackleave= None
        self.username=None
        self.databuff=bytearray()

        #: The IP address of the c2w server.
        self.serverAddress = serverAddress
        #: The port number used by the c2w server.
        self.serverPort = serverPort
        #: The clientProxy, which the protocol must use
        #: to interact with the Graphical User Interface.
        self.clientProxy = clientProxy

    def sendLoginRequestOIE(self, userName):
        """
        :param string userName: The user name that the user has typed.

        The client proxy calls this function when the user clicks on
        the login button.
        """
        #total length of the loginrequest packet 
        length=len(userName)+4
        self.username=userName

        #combined sequence number and type number
        sequ_type=(self.seql<<4) | (types["Envoi du Pseudo"])

     
        buf=struct.pack('!HH%is'%len(userName),length,sequ_type,userName.encode('utf-8'))
        self.transport.write(buf)
  
        #retransmit the loginrequest if lost.
        if(self.count<7):
            self.repeat = reactor.callLater(1,self.sendLoginRequestOIE,userName)
            self.count+=1

        moduleLogger.debug('loginRequest called with username=%s', userName)

    def sendChatMessageOIE(self, message):
        """
        :param message: The text of the chat message.
        :type message: string

        Called by the client proxy when the user has decided to send
        a chat message

        .. note::
           This is the only function handling chat messages, irrespective
           of the room where the user is.  Therefore it is up to the
           c2wChatClientProctocol or to the server to make sure that this
           message is handled properly, i.e., it is shown only by the
           client(s) who are in the same room.
        """
        lenuser=len(self.username.encode('utf-8'))
        length=4+1+lenuser+len(message.encode('utf-8'))
        buf=bytearray(length)
        offset=4
        sequ_type=(self.seql<<4) | (types["Message Chat"])
        struct.pack_into('!HH',buf,0,length,sequ_type)
        struct.pack_into('!B%is'%len(self.username.encode('utf-8')),buf,offset,lenuser,self.username.encode('utf-8'))
        offset+=1+lenuser
        struct.pack_into('!%is'%len(message.encode('utf-8')),buf,offset,message.encode('utf-8'))
        
        self.transport.write(buf)

        #retransmit the chatmessage if lost.
        if(self.count<7):
            self.repeat = reactor.callLater(1,self.sendChatMessageOIE,message)
            self.count+=1


        pass

    def sendJoinRoomRequestOIE(self, roomName):
        """
        :param roomName: The room name (or movie title.)

        Called by the client proxy  when the user
        has clicked on the watch button or the leave button,
        indicating that she/he wants to change room.

        .. warning:
            The controller sets roomName to
            c2w.main.constants.ROOM_IDS.MAIN_ROOM when the user
            wants to go back to the main room.
        """
        if(roomName is ROOM_IDS.MAIN_ROOM):
             #total length of the Quitter salle film packet 
            length=4

            #combined sequence number and type number
            sequ_type=(self.seql<<4) | (types["Quitter salle film"])
            self.ackcm=self.seql
        
            #Packing and sending the Quitter salle film packet
            buf=struct.pack('!HH',length,sequ_type)
            self.transport.write(buf)

        else:
            #total length of the Choix d’un film packet 
            length=len(roomName)+4

            #combined sequence number and type number
            sequ_type=(self.seql<<4) | (types["Choix d’un film"])
            self.ackcm=self.seql
            
            #Packing and sending the Choix d’un film packet
            buf=struct.pack('!HH%is'%len(roomName),length,sequ_type,roomName.encode('utf-8'))
            self.transport.write(buf)
  
        #retransmit the Choix d’un film or Quitter salle film if lost.
        if(self.count<7):
            self.repeat = reactor.callLater(1,self.sendJoinRoomRequestOIE,roomName)
            self.count+=1


        pass

    def sendLeaveSystemRequestOIE(self):
        """
        Called by the client proxy  when the user
        has clicked on the leave button in the main room.
        """
         #total length of the leaveSystemRequest packet 
        length=4

        #combined sequence number and type number
        sequ_type=(self.seql<<4) | (types["Quitter application"])
        self.ackleave=self.seql
        
        #Packing and transmitting the leaveSystemRequest packet.
        buf=struct.pack('!HH',length,sequ_type)
        self.transport.write(buf)
  
        #retransmit the leaveSystemRequest packet if lost.
        if(self.count<7):
            self.repeat = reactor.callLater(1,self.sendLeaveSystemRequestOIE)
            self.count+=1        


        pass

    def dataReceived(self, data):
        """
        :param data: The data received from the client (not necessarily
                     an entire message!)

        Twisted calls this method whenever new data is received on this
        connection.
        """
        self.databuff=self.databuff+data
        lenbuff=len(self.databuff)
       
        if(len(self.databuff) >= 4):
            lenght,seq_type=struct.unpack_from('!HH',self.databuff)
            seql=seq_type>>4
            typ=seq_type & 15
            print(lenbuff)
            print(lenght)

            if(lenbuff>=lenght):
                print('here')
                datagram = self.databuff
                self.databuff = bytearray(0)               
                #unpacking and extracting the length, sequence number and type from the received data.
                lenght, seq_type, data = struct.unpack('!HH%is'%(len(datagram)-4), datagram)
                seql=seq_type>>4
                typ=seq_type & 15
                print(typ)
                offset = 4
                

                #if type of the received data is not an ACK, then it has to send an ACK for the received data.
                if(typ!=types["Acquittement"]):
                    sequ_type=(seql<<4) | (types["Acquittement"])
                    buf=struct.pack('!HH',4,sequ_type)
                    self.transport.write(buf)
                    self.seql+=1
                
                #retransmission cancelled if ACK is received
                elif(typ==types["Acquittement"]): 
                    print('ack')   
                    self.repeat.cancel()
                    self.count=0
                    self.seql+=1

                if(typ==types["Refus connexion"]):
                    self.clientProxy.connectionRejectedONE("user name already exists")

                #if received data is movielist then unpack and store it in the variable as defined. 
                if (typ==types["Envoi liste films"]):
                    
                    while offset < lenght:
                        print(offset, lenght)
                        cip,port,lenmovie,iid=struct.unpack_from('!IHHB',datagram,offset)
                        offset+=9
                        movietitle = struct.unpack_from('!%is'%(lenmovie-9),datagram,offset)[0].decode('utf-8')
                        offset+=lenmovie-9
                        aip=str(ipaddress.IPv4Address(cip))
                        stport=str(port)
                        stiid=str(iid)
                        self.movielist.append((movietitle, aip, stport, stiid))

                #if received data is userlist then unpack and store it in the variable as defined.
                if (typ==types["Envoi liste users"]):
                    userList = []
                    while offset < lenght:
                        lenuser,userstatus=struct.unpack_from('!BB',datagram,offset)
                        offset+=2
                        use = struct.unpack_from('!%is'%lenuser,datagram,offset)[0].decode('utf-8')
                        offset+=lenuser
                        #stuserstatus=str(userstatus)
                        if(userstatus==0):
                            auserstatus=ROOM_IDS.MAIN_ROOM
                        else:
                            
                            for movie in self.movielist:
                                if movie[3] ==str(userstatus):
                                    auserstatus=movie[0]
                        userList.append((use, auserstatus))

                    if self.userlist==[]:
                        self.userlist=userList
                        self.clientProxy.initCompleteONE(self.userlist,self.movielist)
                    else:
                        self.userlist=userList
                        self.clientProxy.setUserListONE(self.userlist)
                                       

                if(typ==types["Acquittement"]):
                    if(seql==self.ackcm):
                        self.clientProxy.joinRoomOKONE()
                    if(seql==self.ackleave):
                        self.clientProxy.leaveSystemOKONE()
                
                
                if(typ==types["Message Chat"]):
                    lenuser=struct.unpack_from('!B',datagram,4)[0]
                    username=struct.unpack_from('!%is'%lenuser,datagram,5)[0].decode('utf-8')
                    lengthmsg=lenght-4-1-lenuser
                    msg=struct.unpack_from('!%is'%lengthmsg,datagram,5+lenuser)[0].decode('utf-8')
                    if(self.username!=username):
                        self.clientProxy.chatMessageReceivedONE(username, msg)


        pass
