# -*- coding:gbk -*-

from echo import RawEcho
import client_info, msgs, url_pattern, utils
import time, sys

MESSAGE_LOG_PATH = "/home/zfy/mf/bigworld/tools/server/"
MESSAGE_LOG_ROOT = "/var/log/bigworld/message_logger"
if MESSAGE_LOG_PATH not in sys.path:
    sys.path.append(MESSAGE_LOG_PATH)
from message_logger import bwlog

INTERVAL = 1.0             ## ��һ�ε�INTERVAL��

class GetLog(RawEcho):
    def __init__(self, clientInfo):
        super(GetLog, self).__init__(clientInfo)
        self.outData = []
        self.flags = int("111111111", 2)
        self.stopQuery = False
        self.mlog = bwlog.BWLog( MESSAGE_LOG_ROOT )
        self.query = None
        self.startWriteMonitor()
        self.startReadLog()
    
    """
    ���Կͻ��˵�����
    """
    def read(self, data):
        if data == None:
            self.clientInfo.close()
        return

    def startWriteMonitor(self, timer=None):
        if self.stopQuery:
            timer.stop()
            timer.close()
            timer = None
            return
        for data in self.getOutput():
            self.clientInfo.write(data)
        utils.callback(INTERVAL, self.startWriteMonitor)

    def _writeEntry(self, callb):
        if self.stopQuery:
            callb = None
            return
        for result in self.query:
            self.setOutput( result.format( self.flags ) )
        self.query.resume()
        utils.callback(INTERVAL, callb)

    def _doGetLog(self, fromTime, toTime, uid, timer=None):
        if self.stopQuery:
            timer.stop()
            timer.close()
            timer = None
            return
        if fromTime >= toTime:
            self.setOutput("----finished!----\n")
            return
        endTime = fromTime + INTERVAL ##1��1�����
        endTime = min(endTime, toTime)
        kwargs = {
            "start" : fromTime,
            "end" : endTime,
            "uid" : uid,
        }
        self.query = self.mlog.fetch(**kwargs)
        callb = utils.Functor(self._doGetLog, endTime, toTime, uid)
        self._writeEntry(callb)

    def startReadLog(self, fromTime=None, toTime=None, uid=1001):
        nowTime = time.time()
        fromTime = fromTime or (nowTime - 1)
        toTime = toTime or (nowTime + 86400)
        if fromTime < toTime:
            utils.callback(INTERVAL, utils.Functor(self._doGetLog, fromTime, toTime, uid))
        else:
            self.setOutput("ʱ�����ô���from=%s, to=%s\n"%(fromTime, toTime))

    def close(self):
        self.stopQuery = True
        self.query = None
        self.mlog = None
