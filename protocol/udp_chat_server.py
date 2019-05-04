# -*- coding: utf-8 -*-
from twisted.internet.protocol import DatagramProtocol
from c2w.main.lossy_transport import LossyTransport
import logging
from c2w.protocol.type import types
import struct
from twisted.internet import reactor
import ipaddress
from c2w.main.constants import ROOM_IDS


logging.basicConfig()
moduleLogger = logging.getLogger('c2w.protocol.udp_chat_server_protocol')


class c2wUdpChatServerProtocol(DatagramProtocol):

    def __init__(self, serverProxy, lossPr):
        """
        :param serverProxy: The serverProxy, which the protocol must use
            to interact with the user and movie store (i.e., the list of users
            and movies) in the server.
        :param lossPr: The packet loss probability for outgoing packets.  Do
            not modify this value!

        Class implementing the UDP version of the client protocol.

        .. note::
            You must write the implementation of this class.

        Each instance must have at least the following attribute:

        .. attribute:: serverProxy

            The serverProxy, which the protocol must use
            to interact with the user and movie store in the server.

        .. attribute:: lossPr

            The packet loss probability for outgoing packets.  Do
            not modify this value!  (It is used by startProtocol.)

        .. note::
            You must add attributes and methods to this class in order
            to have a working and complete implementation of the c2w
            protocol.
        """
          
        self.managecount={}
        self.managerepeat = {}
        self.usserName=""
        self.manageackul={}
        self.manageuserseq={}       
        self.rejseq=0
 
        #: The serverProxy, which the protocol must use
        #: to interact with the server (to access the movie list and to 
        #: access and modify the user list).
        self.serverProxy = serverProxy
        self.lossPr = lossPr

    def startProtocol(self):
        """
        DO NOT MODIFY THE FIRST TWO LINES OF THIS METHOD!!

        If in doubt, do not add anything to this method.  Just ignore it.
        It is used to randomly drop outgoing packets if the -l
        command line option is used.
        """
        self.transport = LossyTransport(self.transport, self.lossPr)
        DatagramProtocol.transport = self.transport

        #verify username with the existing data
    def verifyName(self, userName):
        if self.serverProxy.userExists(userName):
            status=0
        else:
            status=1
        return status

        #function to send the login acceptance msg.
    def loginAcpMsg(self, host_port):
        sequ_type=(self.manageuserseq[host_port]<<4) | (types["Acceptation connexion"])
        buf=struct.pack('!HH',4,sequ_type)
        self.transport.write(buf,host_port)
        
        #retransmit the login acceptance msg if lost.
        if(self.managecount[host_port]<7):
            self.managerepeat[host_port] = reactor.callLater(1,self.loginAcpMsg,host_port)
            self.managecount[host_port]+=1

        #send login Refuse msg if username already exist.
    def sendLoginRefuse(self, host_port):
        sequ_type=(self.rejseq<<4) | (types["Refus connexion"])
        buf=struct.pack('!HH',4,sequ_type)
        self.transport.write(buf,host_port)
        
        #retransmit the login Refuse msg if lost.
        if(self.managecount[host_port]<7):
            self.managerepeat[host_port] = reactor.callLater(1,self.sendLoginRefuse,host_port)
            self.managecount[host_port]+=1
        

        #function to send movies list
    def sendMovieList(self, host_port):
        length = 4
        for f in self.serverProxy.getMovieList():
            length += 9 + len(f.movieTitle.encode('utf-8'))

        buf=bytearray(length)
        offset=4
        sequ_type=(self.manageuserseq[host_port]<<4) | (types["Envoi liste films"])
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
   
        self.transport.write(buf,host_port)

        #retransmit the movies list msg if lost.
        if(self.managecount[host_port]<7):
            self.managerepeat[host_port] = reactor.callLater(1,self.sendMovieList,host_port)
            self.managecount[host_port]+=1

        #function to send users list
    def sendUserList(self, host_port):
        length = 4
        for f in self.serverProxy.getUserList():
            length += 2 + len(f.userName.encode('utf-8'))

        buf=bytearray(length)
        offset=4
        sequ_type=(self.manageuserseq[host_port]<<4) | (types["Envoi liste users"])
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
   
        self.transport.write(buf,host_port)

        #retransmit the users list msg if lost.
        if(self.managecount[host_port]<7):
            self.managerepeat[host_port] = reactor.callLater(1,self.sendUserList,host_port)
            self.managecount[host_port]+=1
        
        #condition to send users list
    def sendUserListAll(self):
        print(self.serverProxy.getUserList())
        for f in self.serverProxy.getUserList():
            self.sendUserList(f.userAddress)

        #function to forward the chat msg
    def sendChatMsg(self,username,msg,host_port):
        lenuser=len(username.encode('utf-8'))
        length=4+1+lenuser+len(msg.encode('utf-8'))
        buf=bytearray(length)
        offset=4
        sequ_type=(self.manageuserseq[host_port]<<4) | (types["Message Chat"])
        struct.pack_into('!HH',buf,0,length,sequ_type)
        
        struct.pack_into('!B%is'%len(username.encode('utf-8')),buf,offset,lenuser,username.encode('utf-8'))
        offset+=1+lenuser
        struct.pack_into('!%is'%len(msg.encode('utf-8')),buf,offset,msg.encode('utf-8'))
        self.transport.write(buf,host_port)

        if(self.managecount[host_port]<7):
            self.managerepeat[host_port] = reactor.callLater(1,self.sendChatMsg,username,msg,host_port)
            self.managecount[host_port]+=1
        
        #condition to send chat msg
    def sendChatMsgAll(self,username,msg):
        user=self.serverProxy.getUserByName(username)
        print(self.serverProxy.getUserList())
        for f in self.serverProxy.getUserList():
            if f.userChatRoom == user.userChatRoom:
                self.sendChatMsg(username,msg,f.userAddress)
        

    def datagramReceived(self, datagram, host_port):
        """
        :param string datagram: the payload of the UDP packet.
        :param host_port: a touple containing the source IP address and port.
        
        Twisted calls this method when the server has received a UDP
        packet.  You cannot change the signature of this method.
        """
        #unpacking and extracting the length, sequence number, type and data  from the received msg.   
        lenght, seq_type, data = struct.unpack('!HH%is'%(len(datagram)-4), datagram)  
        seql=seq_type>>4
        typ=seq_type & 15

        #if type of the received msg is not an ACK, then it will send an ACK for the received msg.
        if(typ!=types["Acquittement"]):
            sequ_type=(seql<<4) | (types["Acquittement"])
            buf=struct.pack('!HH',4,sequ_type)
            self.transport.write(buf,host_port)

        #if Ack is received it will cancel the retransmission of the msg. 
        elif (typ==types["Acquittement"]):
            self.managerepeat[host_port].cancel()
            self.manageuserseq[host_port] += 1
            self.managecount[host_port] = 0

            #once received the ack for acceptance msg with its seql no, add the user to the server and send the movie list
            if(seql==0):
                self.serverProxy.addUser(self.usserName,ROOM_IDS.MAIN_ROOM,userChatInstance=None,userAddress=host_port)
                self.sendMovieList(host_port)
           
            elif(seql==1):
                self.sendUserList(host_port)

            elif(seql==2):
                self.sendUserListAll()                               

        if(typ==types["Envoi du Pseudo"]):
            self.usserName=data.decode('utf-8')
            stat = self.verifyName(self.usserName)  
          
            if(stat==1):
                self.manageuserseq[host_port]=0
                self.managecount[host_port]=0
                self.managerepeat[host_port]=None
                self.loginAcpMsg(host_port)
            else:
                self.sendLoginRefuse(host_port)            
        
        if(typ==types["Choix d’un film"]):
            roomName=data.decode('utf-8')
            self.serverProxy.updateUserChatroom((self.serverProxy.getUserByAddress(host_port)).userName, roomName)
            self.serverProxy.startStreamingMovie(roomName)
            self.sendUserListAll()      
         
        if(typ==types["Quitter salle film"]):
            self.serverProxy.updateUserChatroom((self.serverProxy.getUserByAddress(host_port)).userName, ROOM_IDS.MAIN_ROOM)
            self.sendUserListAll()  
                      
        if(typ==types["Quitter application"]):
            self.serverProxy.removeUser(self.serverProxy.getUserByAddress(host_port).userName)
            self.sendUserListAll()
            
        if(typ==types["Message Chat"]):
            lenuser=struct.unpack_from('!B',datagram,4)[0]
            username=struct.unpack_from('!%is'%lenuser,datagram,5)[0].decode('utf-8')
            lengthmsg=lenght-4-1-lenuser
            msg=struct.unpack_from('!%is'%lengthmsg,datagram,5+lenuser)[0].decode('utf-8')
            self.sendChatMsgAll(username,msg)
                
        pass
