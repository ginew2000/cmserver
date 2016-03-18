# -*- coding:gbk -*-

import utils, time

STOP_WORD = "end"
SHOW_TYPES = frozenset([str, int, float, list, dict])

class RawEcho(object):
    def __init__(self, clientInfo):
        self.clientInfo = clientInfo
        self.outData = ["handler: %s. type \"%s\" to quit"%(self.__class__.__name__, STOP_WORD)]

    def __str__(self):
        ret = ["(%s)"%(self.__class__.__name__)]
        for attrName in dir(self):
            attr = getattr(self, attrName)
            if attrName[0:2] == "__":
                continue
            if type(attr) not in SHOW_TYPES:
                continue
            ret.append("%s=%s"%(attrName, attr))
        return ",".join(ret)

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
        self.clientInfo.changeHandler()

    """
    子类请根据需求来通过data来获得需要输出的内容。
    结束就写个end在列表里面
    """
    def setOutput(self, data):
        self.outData.append(data)

    def getOutput(self):
        while self.outData:
            data = self.outData.pop(0)
            yield data
        return

    def close(self):
        return

class HttpEcho(RawEcho):
    def __init__(self, clientInfo):
        super(HttpEcho, self).__init__(clientInfo)
        self.outData = ["""HTTP/1.1 200 OK
Content-Type: text/html; charset=GBK
Connection: close
Server: HttpEcho by cmServer

welcome to my server. now handler is %s
\n\n"""%self.__class__.__name__]

    def setOutput(self, data):
        self.outData.append("<pre>")
        self.outData.append(data)
        self.outData.append("</pre>")
        self.outData.append(STOP_WORD)
