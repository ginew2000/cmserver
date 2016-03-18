# -*- coding:gbk -*-

from base import HandlerBase
import utils
import time, sys

MESSAGE_LOG_PATH = "/home/zfy/mf/bigworld/tools/server/"
MESSAGE_LOG_ROOT = "/var/log/bigworld/message_logger"
if MESSAGE_LOG_PATH not in sys.path:
    sys.path.append(MESSAGE_LOG_PATH)
from message_logger import bwlog

INTERVAL = 1.0              ## ��һ�ε�INTERVAL��
MAX_LOG_DURATION = 30       ## ������� ÿ����MAX_LOG_DURATION���log 
MAX_LOG_COUNT = 3000        ## �����õ���log���ޣ��ٶ������ʾ������
STOP_WORD = "stop"

## ���ؽ���е���Щ��
SHOW_COLS_LIST = reversed([
    "0", #d: SHOW_DATE
    "1", #t: SHOW_TIME
    "0", #h: SHOW_HOST
    "0", #u: SHOW_USER
    "0", #i: SHOW_PID
    "0", #a: SHOW_APPID
    "1", #p: SHOW_PROCS
    "1", #s: SHOW_SEVERITY
    "1", #m: SHOW_MESSAGE
])
SHOW_COLS = int("".join(SHOW_COLS_LIST), 2)

##������: �������룬��/var/log/bigworld/message_logger/component_names�е�˳���йأ�ÿ̨����һ��һ��
VALID_PROCS = ("DBMgr", "Tools", "CellAppMgr", "BaseApp", "LoginApp", "CellApp", "BaseAppMgr")
SERVER_LOG_DEFS = {}
i = 0
for line in open("%s/component_names"%MESSAGE_LOG_ROOT):
    line = line.strip()
    if line in VALID_PROCS:
        SERVER_LOG_DEFS[line] = 2**i
    i += 1

FILTER_PROCS = sum(SERVER_LOG_DEFS.values())

##��������log����
FILTER_LOG_LEVELS_LIST = reversed([
    "0", #TRACE
    "0", #DEBUG
    "0", #INFO
    "0", #NOTICE
    "0", #WARNING
    "0", #ERROR
    "0", #CRITICAL
    "0", #HACK
    "1", #SCRIPT
]) 
FILTER_LOG_LEVELS = int("".join(FILTER_LOG_LEVELS_LIST), 2)

class GetLog(HandlerBase):
    def __init__(self, clientInfo):
        super(GetLog, self).__init__(clientInfo)
        self.showCols = SHOW_COLS
        self.queryPara = {
            "start"     : 0,    ##��ѯ��ʼʱ��
            "end"       : 0,    ##��ѯ����ʱ�䣨��������
            "uid"       : 1001, ##�û�id
            "procs"     : FILTER_PROCS,     ##����������������
            "severities": FILTER_LOG_LEVELS, ##��������log����
            "message"   : "", ##������������
        }
        self.stopQuery = False
        self.mlog = bwlog.BWLog( MESSAGE_LOG_ROOT )
        self.query = None
        self.startReadLog()
    
    def read(self, data):
        if data == None:
            self.close()
            return
        keyWords = data.rstrip()
        if keyWords == STOP_WORD:
            self.close()

    def _writeEntry(self, callb):
        if self.stopQuery:
            return
        logCount = self.query.getProgress()[1]
        i = 0
        for result in self.query:
            if i >= MAX_LOG_COUNT:
                self.write("[ERROR]log̫�࣬���λ�ȡֻ��ʾǰ��%d��������%d������\n"%(MAX_LOG_COUNT, logCount - MAX_LOG_COUNT))
                break
            self.write( result.format( self.showCols ) )
            i += 1
        self.query.resume()
        utils.callback(INTERVAL, callb)

    def _doGetLog(self, fromTime, toTime):
        if self.stopQuery:
            return
        nowTime = time.time()
        if fromTime > nowTime - 2: ##�ļ�ϵͳ��Ҫ2��Ļ��棬��������Ҫ����ʼʱ�����2��ǰ����Ȼ�ò�������
            fromTime = nowTime - 2
        if fromTime >= toTime:
            self.write("----finished!----\n")
            return
        endTime = fromTime + MAX_LOG_DURATION
        endTime = min(endTime, toTime, nowTime)
        self.queryPara["start"] = fromTime
        self.queryPara["end"] = endTime
        self.query = self.mlog.fetch(**self.queryPara)
        callb = utils.Functor(self._doGetLog, endTime, toTime)
        self._writeEntry(callb)

    def startReadLog(self, fromTime=None, toTime=None):
        nowTime = time.time()
        fromTime = fromTime or (nowTime - 2)
        toTime = toTime or (nowTime + 86400)
        if fromTime < toTime:
            self._doGetLog(fromTime, toTime)
        else:
            self.write("ʱ�����ô���from=%s, to=%s\n"%(fromTime, toTime))

    def close(self):
        self.stopQuery = True
        self.query = None
        self.mlog = None
        super(GetLog, self).close()

class GetLogFromWeb(GetLog):
    def startReadLog(self, fromTime=None, toTime=None):
        self.sendResponseHead()
        super(GetLogFromWeb, self).startReadLog(fromTime, toTime)

    def sendResponseHead(self):
        HTTP_HEAD = """%s
<style>
.log {font-size: 9pt;}
</style>
<script>
function scrollWindow(){
  scroll(0, 100000);
  setTimeout('scrollWindow()', 200);
}
scrollWindow()
</script>
""" % utils.getHttpHeader(title="showlog service")

        self.write(HTTP_HEAD)
        self.sendKeepAliveToClient()

    def sendKeepAliveToClient(self):
        if self.stopQuery:
            return
        self.write("<!--  keep alive -->\n")
        utils.callback(30, self.sendKeepAliveToClient)

    def write(self, msg):
        super(GetLogFromWeb, self).write(("<div class=log>%s</div>"%msg)
