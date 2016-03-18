# -*- coding:gbk -*-

import utils, time
from base import HandlerBase

STOP_WORD = "end"

class RawEcho(HandlerBase):
    def __init__(self, clientInfo):
        super(RawEcho, self).__init__(clientInfo)
        self.outData = [self.getWelcomeInfo()]
        self.startWriteMonitor()

    def getWelcomeInfo(self):
        return "type \"%s\" to quit"%STOP_WORD

    def read(self, data):
        if not data:
            self.close()
            return
        _d = data.rstrip()
        if _d == STOP_WORD:
            self.write("Bye bye!\n")
            self.close()
        self.setOutput(data)

    def startWriteMonitor(self):
        if not self.clientInfo.handler:
            return
        for data in self.getOutput():
            self.write(data)
        utils.callback(0.5, self.startWriteMonitor)

    def setOutput(self, data):
        self.outData.append(data)

    def getOutput(self):
        while self.outData:
            data = self.outData.pop(0)
            yield data
        return

class HttpEcho(RawEcho):
    def getWelcomeInfo(self):
        return """%s
welcome to my server. now handler is %s
\n\n""" % (utils.getHttpHeader(), self.__class__.__name__)

    def setOutput(self, data):
        self.outData.append("<pre>")
        self.outData.append(data)
        self.outData.append("</pre>")
        utils.callback(2, self.close)

