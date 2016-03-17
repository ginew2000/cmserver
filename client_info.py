# -*- coding:gbk -*-

import url_pattern
import utils, msgs
import pyuv
import time, weakref
clientsMgr = None
nowCls = weakref.WeakValueDictionary()
def onHandlerDone(obj):
    print "onHandlerDone", obj
    objId = id(obj)
    if objId in nowCls:
        del nowCls[objId]
    print "nowCls: %s"%nowCls.values()

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
        handler = handlerClass(self)
        weakR = weakref.ref(handler, onHandlerDone)
        nowCls[id(weakR)] = handler
        self.handler = handler

    def changeHandler(self):
        self.handler = None

    def onRead(self, fd, data, error):
        if not self.handler:
            if data != None:
                self.initHandler(data)
            else:
                self.close()
                return
        self.handler.read(data)

    def write(self, data):
        if not self.fd.closed:
            self.fd.write(data)
        
    def startRead(self):
        self.fd.start_read(self.onRead)

    def close(self):
        if self.handler:
            self.handler.close()
            self.handler = None
        getClientMgr().closeClient(self.fd)
        #utils.callback(1, doHunt)
        print "close  nowCls: %s"%nowCls.values()

def doHunt(timer):
    print "doHunt"
    import sys
    if "/home/zfy/cmserver" not in sys.path:
        sys.path.append("/home/zfy/cmserver")
    import leakHunter
    leakHunter.hunt()

"""
客户端管理类，全服唯一。
"""
class ClientsMgr(object):
    def __init__(self):
        self.clientsInfo = {}
        self.startTime = time.time()

    def getRunTimes(self):
        return time.time() - self.startTime

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
def getClientMgr():
    global clientsMgr
    if not clientsMgr:
        clientsMgr = ClientsMgr()
    return clientsMgr

def on_connection(server, error):
    _clientFd = pyuv.TCP(server.loop)
    server.accept(_clientFd)
    clientInfo = getClientMgr().newClient(_clientFd)
    clientInfo.startRead()

def closeAllClients():
    if not clientsMgr:
        return
    [fd.close() for fd, _ in clientsMgr.getAllClients()]
