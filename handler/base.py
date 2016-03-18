# -*- coding:gbk -*-

import utils, time

SHOW_TYPES = frozenset([str, int, float, list, dict])

class HandlerBase(object):
    def __init__(self, clientInfo):
        self.clientInfo = clientInfo

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
            self.close()
            return

    def write(self, data):
        self.clientInfo.write(data)

    def close(self):
        self.clientInfo.close()

