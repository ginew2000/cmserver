# -*- coding:gbk -*-

import url_pattern
import utils, msgs
import pyuv
clientsMgr = None

"""
客户端类。管理客户端的读写与初始化。
"""
class Client(object):
    def __init__(self, clientFd):
        self.fd = clientFd
        self.reqType = url_pattern.REQ_TYPE_RAW 
        self.handler = None

    def initHandler(self, data):
        handlerClass = url_pattern.getHandlerFromData(data)
        if not handlerClass:
            utils.logError(msgs.CAN_NOT_FIND_HANDLER % data)
            self.close()
        self.handler = handlerClass(self)

    def onRead(self, fd, data, error):
        if not self.handler:
            self.initHandler(data)
        self.handler.read(data)

    def write(self, data):
        self.fd.write(data)
        
    def startRead(self):
        utils.logDebug(msgs.CLIENT_CONNECTED % str(self.fd.getpeername()))
        utils.logDebug(msgs.NOW_CLIENTS_COUNT % len(getClientInfo().clientsInfo))
        self.fd.start_read(self.onRead)

    def close(self):
        getClientInfo().closeClient(self.fd)
"""
客户端管理类，全服唯一。
"""
class ClientsMgr(object):
    def __init__(self):
        self.clientsInfo = {}

    def getAllClients(self):
        return self.clientsInfo.iteritems()
            
    def newClient(self, fd):
        client = Client(fd)
        self.clientsInfo[fd] = client
        return client

    def closeClient(self, fd):
        if fd in self.clientsInfo:
            del self.clientsInfo[fd]
        fd.close()
        utils.logDebug(msgs.NOW_CLIENTS_COUNT % len(self.clientsInfo))

#-----------------------------------------------------#
#------------  对外接口 ------------------------------#
#-----------------------------------------------------#
def getClientInfo():
    global clientsMgr
    if not clientsMgr:
        clientsMgr = ClientsMgr()
    return clientsMgr

def on_read(client, data, error):
    if data is None:
        client.close()
        clients.remove(client)
        return
    print data
    client.write(data)

def on_connection(server, error):
    _clientFd = pyuv.TCP(server.loop)
    server.accept(_clientFd)
    clientInfo = getClientInfo().newClient(_clientFd)
    clientInfo.startRead()

def closeAllClients():
    if not clientsMgr:
        return
    [fd.close() for fd, _ in clientsMgr.getAllClients()]
