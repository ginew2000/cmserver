# -*- coding:gbk -*-

from base import HandlerBase
import utils
import time, sys

MESSAGE_LOG_PATH = "/home/zfy/mf/bigworld/tools/server/"
MESSAGE_LOG_ROOT = "/var/log/bigworld/message_logger"
if MESSAGE_LOG_PATH not in sys.path:
    sys.path.append(MESSAGE_LOG_PATH)
from message_logger import bwlog

INTERVAL = 1.0              ## 拿一次等INTERVAL秒
MAX_LOG_DURATION = 30       ## 如果可以 每次拿MAX_LOG_DURATION秒的log 
MAX_LOG_COUNT = 3000        ## 单次拿到的log上限，再多就怕显示不下了
STOP_WORD = "stop"

## 返回结果中的哪些列
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

##过滤器: 进程掩码，和/var/log/bigworld/message_logger/component_names中的顺序有关，每台机不一定一样
VALID_PROCS = ("DBMgr", "Tools", "CellAppMgr", "BaseApp", "LoginApp", "CellApp", "BaseAppMgr")
SERVER_LOG_DEFS = {}
i = 0
for line in open("%s/component_names"%MESSAGE_LOG_ROOT):
    line = line.strip()
    if line in VALID_PROCS:
        SERVER_LOG_DEFS[line] = 2**i
    i += 1

FILTER_PROCS = sum(SERVER_LOG_DEFS.values())

##过滤器：log级别
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
            "start"     : 0,    ##查询开始时间
            "end"       : 0,    ##查询结束时间（不包括）
            "uid"       : 1001, ##用户id
            "procs"     : FILTER_PROCS,     ##过滤器：进程掩码
            "severities": FILTER_LOG_LEVELS, ##过滤器：log级别
            "message"   : "", ##过滤器：内容
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
                self.write("[ERROR]log太多，本次获取只显示前面%d条，后面%d条忽略\n"%(MAX_LOG_COUNT, logCount - MAX_LOG_COUNT))
                break
            self.write( result.format( self.showCols ) )
            i += 1
        self.query.resume()
        utils.callback(INTERVAL, callb)

    def _doGetLog(self, fromTime, toTime):
        if self.stopQuery:
            return
        nowTime = time.time()
        if fromTime > nowTime - 2: ##文件系统需要2秒的缓存，所以至少要把起始时间设成2秒前，不然拿不到东西
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
            self.write("时间设置错误：from=%s, to=%s\n"%(fromTime, toTime))

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
