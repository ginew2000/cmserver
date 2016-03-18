# -*- coding:gbk -*-

from base import HandlerBase
import client_info, msgs, url_pattern
import time

class GetInfo(HandlerBase):
    def __init__(self, clientInfo):
        super(GetInfo, self).__init__(clientInfo)
        clientMgr = client_info.getClientMgr()
        self.write(msgs.NOW_CLIENTS_COUNT % len(clientMgr.clientsInfo))
        self.write(msgs.SERVER_ALREADY_RUN_TIME % clientMgr.getRunTimes())
        self.write("url: %s"%str(url_pattern.URL_PREFIX_RE))

    def write(self, msg):
        super(GetInfo, self).write(msg+"\n")
