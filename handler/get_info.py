# -*- coding:gbk -*-

from echo import RawEcho
import client_info, msgs, url_pattern
import time

class GetInfo(RawEcho):
    def setOutput(self, data):
        clientMgr = client_info.getClientMgr()
        self.outData.append(msgs.NOW_CLIENTS_COUNT % len(clientMgr.clientsInfo))
        self.outData.append(msgs.SERVER_ALREADY_RUN_TIME % clientMgr.getRunTimes())
        self.outData.append("url: %s"%str(url_pattern.URL_PREFIX_RE))
