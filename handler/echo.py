# -*- coding:gbk -*-

import utils, time

STOP_WORD = "end"

class RawEcho(object):
    def __init__(self, clientInfo):
        self.clientInfo = clientInfo
        self.outData = ["welcome to my server. type \"%s\" to quit"%STOP_WORD]

    def log(self, msg):
        utils.log(msg, self.__class__.__name__)

    def debug(self, msg):
        utils.logDebug(msg, self.__class__.__name__)

    def error(self, msg):
        utils.logError(msg, self.__class__.__name__)

    def read(self, data):
        if not data:
            return
        data = data.rstrip()
        self.setOutput(data)
        self.startWriteMonitor()

    def startWriteMonitor(self):
        for data in self.getOutput():
            if data == STOP_WORD:
                self.clientInfo.write("Bye bye!\n")
                self.clientInfo.close()
                return
            self.clientInfo.write(data+"\n")

    def setOutput(self, data):
        self.outData.append(data)

    def getOutput(self):
        while self.outData:
            data = self.outData.pop(0)
            yield data
        return

class HttpEcho(RawEcho):
    def __init__(self, clientInfo):
        super(HttpEcho, self).__init__(clientInfo)
        self.outData = ["""HTTP/1.1 200 OK
Content-Type: text/html; charset=GBK
Connection: close
Server: HttpEcho by cmServer

welcome to my server
\n\n"""]

    def startWriteMonitor(self):
        for data in self.getOutput():
            if data == STOP_WORD:
                self.clientInfo.write("Bye bye!")
                self.clientInfo.close()
                return
            self.clientInfo.write(data+"<br>")
        self.clientInfo.close()
