# -*- coding:gbk -*-

from echo import RawEcho
import client_info, msgs, url_pattern, utils
import time

class GetLog(RawEcho):
    def onReadCallback(self, handle, data, error):
        if data == None:
            return 
        self.outData.append(data)
        self.startWriteMonitor()

    def onDoneCallback(self, proc, exit_status, term_signal):
        self.outData.append("retcode: %d"%exit_status)
        self.startWriteMonitor()

    def onCb(self, startTime, timer):
        self.outData.append("timer:%s, time:%f"%(timer, time.time() - startTime))
        self.startWriteMonitor()

    def setOutput(self, data):
        utils.runCmd("python ../test/test.py", self.onReadCallback, self.onDoneCallback)
        utils.callback(1.1, utils.Functor(self.onCb, time.time()))
