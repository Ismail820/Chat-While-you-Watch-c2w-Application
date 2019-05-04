# -*- coding: utf-8 -*-
from twisted.internet.protocol import Protocol
import logging
from c2w.protocol.type import types
import struct
from twisted.internet import reactor
import ipaddress
from c2w.main.constants import ROOM_IDS


logging.basicConfig()
moduleLogger = logging.getLogger('c2w.protocol.tcp_chat_server_protocol')


class c2wTcpChatServerProtocol(Protocol):

    def __init__(self, serverProxy, clientAddress, clientPort):
        """
        :param serverProxy: The serverProxy, which the protocol must use
            to interact with the user and movie store (i.e., the list of users
            and movies) in the server.
        :param clientAddress: The IP address (or the name) of the c2w server,
            given by the user.
        :param clientPort: The port number used by the c2w server,
            given by the user.

        Class implementing the TCP version of the client protocol.

        .. note::
            You must write the implementation of this class.

        Each instance must have at least the following attribute:

        .. attribute:: serverProxy

            The serverProxy, which the protocol must use
            to interact with the user and movie store in the server.

        .. attribute:: clientAddress

            The IP address of the client corresponding to this 
            protocol instance.

        .. attribute:: clientPort

            The port number used by the client corresponding to this 
            protocol instance.

        .. note::
            You must add attributes and methods to this class in order
            to have a working and complete implementation of the c2w
            protocol.

        .. note::
            The IP address and port number of the client are provided
            only for the sake of completeness, you do not need to use
            them, as a TCP connection is already associated with only
            one client.
        """
        #: The IP address of the client corresponding to this 
        #: protocol instance.
        self.clientAddress = clientAddress
        #: The port number used by the client corresponding to this 
        #: protocol instance.
        self.clientPort = clientPort
        #: The serverProxy, which the protocol must use
        #: to interact with the user and movie store in the server.
        self.serverProxy = serverProxy

        self.host_port=[]
        self.managecount=0
        self.managerepeat = None
        self.usserName=""
        self.manageackul=0
        self.manageuserseq=0       
        self.databuff=bytearray()

        #verify username with the existing data
    def verifyName(self, userName):
        if self.serverProxy.userExists(userName):
            status=0
        else:
            status=1
        return status

        #function to send the login acceptance msg.
    def loginAcpMsg(self):
        sequ_type=(self.manageuserseq<<4) | (types["Acceptation connexion"])
        buf=struct.pack('!HH',4,sequ_type)
        self.transport.write(buf)
        
        #retransmit the login acceptance msg if lost.
        if(self.managecount<7):
            self.managerepeat = reactor.callLater(1,self.loginAcpMsg)
            self.managecount+=1

        #send login Refuse msg if username already exist.
    def sendLoginRefuse(self):
        sequ_type=(self.manageuserseq<<4) | (types["Refus connexion"])
        buf=struct.pack('!HH',4,sequ_type)
        self.transport.write(buf)
        
        #retransmit the login Refuse msg if lost.
        if(self.managecount<7):
            self.managerepeat = reactor.callLater(1,self.sendLoginRefuse)
            self.managecount+=1
        

        #function to send movie list
    def sendMovieList(self):
        length = 4
        for f in self.serverProxy.getMovieList():
            length += 9 + len(f.movieTitle.encode('utf-8'))

        buf=bytearray(length)
        offset=4
        sequ_type=(self.manageuserseq<<4) | (types["Envoi liste films"])
        struct.pack_into('!HH',buf,0,length,sequ_type)

        for f in self.serverProxy.getMovieList():
                aip=f.movieIpAddress
                port=f.moviePort
                iid=f.movieId
                title=f.movieTitle
                cip=int(ipaddress.IPv4Address(aip))
                lenmovie=9+len(title)
                
                struct.pack_into('!IHHB%is'%len(title.encode('utf-8')),buf,offset,cip,port,lenmovie,iid,title.encode('utf-8'))
                offset += 9+len(title.encode('utf-8'))  
   
        self.transport.write(buf)

        #retransmit the movie list msg if lost.
        if(self.managecount<7):
            self.managerepeat = reactor.callLater(1,self.sendMovieList)
            self.managecount+=1

        #function to send user list
    def sendUserList(self):
        length = 4
        for f in self.serverProxy.getUserList():
            length += 2 + len(f.userName.encode('utf-8'))

        buf=bytearray(length)
        offset=4
        #print(self.manageuserseq[host_port])
        sequ_type=(self.manageuserseq<<4) | (types["Envoi liste users"])
        struct.pack_into('!HH',buf,0,length,sequ_type)

        for f in self.serverProxy.getUserList():
        
            use=f.userName
            us=f.userChatRoom
            print(use,us)
            if (us==ROOM_IDS.MAIN_ROOM):
                userstatus=0
            else:
                print(us)
                userstatus=self.serverProxy.getMovieByTitle(f.userChatRoom).movieId
            ip_port=f.userAddress
                
            lenuser=len(use)
            print(use,userstatus,ip_port)
                
            struct.pack_into('!BB%is'%len(use.encode('utf-8')),buf,offset,lenuser,userstatus,use.encode('utf-8'))
            offset += 2+len(use.encode('utf-8'))  
   
        self.transport.write(buf)

        #retransmit the user list msg if lost.
        if(self.managecount<7):
            self.managerepeat = reactor.callLater(1,self.sendMovieList)
            self.managecount+=1
        
    def sendUserListAll(self):
        print(self.serverProxy.getUserList())
        for f in self.serverProxy.getUserList():
            f.userChatInstance.sendUserList()

    def sendChatMsg(self,username,msg):
        lenuser=len(username.encode('utf-8'))
        length=4+1+lenuser+len(msg.encode('utf-8'))
        buf=bytearray(length)
        offset=4
        sequ_type=(self.manageuserseq<<4) | (types["Message Chat"])
        struct.pack_into('!HH',buf,0,length,sequ_type)
        
        struct.pack_into('!B%is'%len(username.encode('utf-8')),buf,offset,lenuser,username.encode('utf-8'))
        offset+=1+lenuser
        struct.pack_into('!%is'%len(msg.encode('utf-8')),buf,offset,msg.encode('utf-8'))
        self.transport.write(buf)

        if(self.managecount<7):
            self.managerepeat = reactor.callLater(1,self.sendChatMsg,username,msg)
            self.managecount+=1
        
    def sendChatMsgAll(self,username,msg):
        user=self.serverProxy.getUserByName(username)
        print(self.serverProxy.getUserList())
        for f in self.serverProxy.getUserList():
            if f.userChatRoom == user.userChatRoom:
                f.userChatInstance.sendChatMsg(username,msg)



    def dataReceived(self, data):
        """
        :param data: The data received from the client (not necessarily
                     an entire message!)

        Twisted calls this method whenever new data is received on this
        connection.
        """
        self.databuff=self.databuff + data
        lenbuff=len(self.databuff)

        self.host_port=(self.clientAddress,self.clientPort)

        if(len(self.databuff) >= 4):
            lenght,seq_type=struct.unpack_from('!HH',self.databuff)
            seql=seq_type>>4
            typ=seq_type & 15

            if(lenbuff==lenght):
                datagram = self.databuff
                self.databuff = bytearray(0)            
                #if type of the received msg is not an ACK, then it will send an ACK for the received msg.
                if(typ!=types["Acquittement"]):
                    sequ_type=(seql<<4) | (types["Acquittement"])
                    buf=struct.pack('!HH',4,sequ_type)
                    print("send ACK")
                    self.transport.write(buf)


                #if Ack is received it will cancel the retransmission of the msg. 
                elif (typ==types["Acquittement"]):
                    self.managerepeat.cancel()
                    print('ACK')
                    self.manageuserseq += 1
                    self.managecount = 0
          
                    if(seql==0):
                        self.serverProxy.addUser(self.usserName,ROOM_IDS.MAIN_ROOM,userChatInstance=self,userAddress=self.host_port)
                        print("send movie list")
                        self.sendMovieList()
                   
                    elif(seql==1):
                        self.sendUserList()
                        print("send user list")
                    elif(seql==2):
                        self.sendUserListAll()                               

                if(typ==types["Envoi du Pseudo"]):
                    self.usserName=struct.unpack_from('%is'%(lenght-4),datagram, 4)[0].decode('utf-8')
                    stat = self.verifyName(self.usserName)  
                  
                    #initializing the sequence, counter & repeat
                    if(stat==1):
                        self.manageuserseq=0
                        self.managecount=0
                        self.managerepeat=None
                        self.loginAcpMsg()
                    else:
                        self.sendLoginRefuse()            
                
                if(typ==types["Choix d’un film"]):
                    roomName=struct.unpack_from('!%is'%(lenght-4),datagram,4)[0].decode('utf-8')
                    self.serverProxy.updateUserChatroom((self.serverProxy.getUserByAddress(self.host_port)).userName, roomName)
                    self.serverProxy.startStreamingMovie(roomName)
                    self.sendUserListAll()      
                 
                if(typ==types["Quitter salle film"]):
                    self.serverProxy.updateUserChatroom((self.serverProxy.getUserByAddress(self.host_port)).userName, ROOM_IDS.MAIN_ROOM)
                    self.sendUserListAll()  
                              
                if(typ==types["Quitter application"]):
                    self.serverProxy.removeUser(self.serverProxy.getUserByAddress(self.host_port).userName)
                    self.sendUserListAll()
                    
                if(typ==types["Message Chat"]):
                    lenuser=struct.unpack_from('!B',datagram,4)[0]
                    username=struct.unpack_from('!%is'%lenuser,datagram,5)[0].decode('utf-8')
                    lengthmsg=lenght-4-1-lenuser
                    msg=struct.unpack_from('!%is'%lengthmsg,datagram,5+lenuser)[0].decode('utf-8')
                    self.sendChatMsgAll(username,msg)
                
          

            
                
                        



        pass
