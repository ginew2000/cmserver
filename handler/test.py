# -*- coding:gbk -*-

from base import HandlerBase
import utils
import time

class Test(HandlerBase):
    def __init__(self, clientInfo):
        super(Test, self).__init__(clientInfo)
        self._doTest()

    def onReadCallback(self, handle, data, error):
        if data == None:
            return 
        self.write(data)

    def onDoneCallback(self, proc, exit_status, term_signal):
        self.write("retcode: %d"%exit_status)

    def onCb(self, startTime):
        self.write("time:%f"%(time.time() - startTime))

    def _doTest(self):
        utils.runCmd("python utils.py", self.onReadCallback, self.onDoneCallback)
        utils.callback(1.1, utils.Functor(self.onCb, time.time()))
