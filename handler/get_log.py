# -*- coding:gbk -*-

from base import HandlerBase, HttpHandlerBase
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
VALID_PROCS = set(["DBMgr", "Tools", "CellAppMgr", "BaseApp", "LoginApp", "CellApp", "BaseAppMgr"])
def getProcMask(procs=VALID_PROCS):
    mask = 0
    i = 0
    for line in open("%s/component_names"%MESSAGE_LOG_ROOT):
        line = line.strip()
        if line in procs:
            mask += 2**i
        i += 1
    return mask

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

class GetLogBase(object):
    def initFilter(self):
        self.stopQuery = False
        self.mlog = bwlog.BWLog( MESSAGE_LOG_ROOT )
        self.query = None
        ## 下面2个在子类中重载
        self.showCols = 0
        self.queryPara = {}

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
            self.close()
            return
        endTime = fromTime + MAX_LOG_DURATION
        endTime = min(endTime, toTime, nowTime)
        self.queryPara["start"] = fromTime
        self.queryPara["end"] = endTime
        self.query = self.mlog.fetch(**self.queryPara)
        callb = utils.Functor(self._doGetLog, endTime, toTime)
        self._writeEntry(callb)

    def startReadLog(self, fromTime=None, toTime=None):
        if not hasattr(self, "showCols") or not hasattr(self, "queryPara"):
            self.initFilter()
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


class GetLogFromRaw(GetLogBase, HandlerBase):
    def __init__(self, clientInfo):
        super(GetLogFromRaw, self).__init__(clientInfo)
        self.initFilter()

    def initFilter(self):
        super(GetLogFromRaw, self).initFilter()
        self.showCols = SHOW_COLS
        self.queryPara = {
            "start"     : 0,    ##查询开始时间
            "end"       : 0,    ##查询结束时间（不包括）
            "uid"       : 1001, ##用户id
            "procs"     : getProcMask(),     ##过滤器：进程掩码
            "severities": FILTER_LOG_LEVELS, ##过滤器：log级别
            "message"   : "", ##过滤器：内容
        }
        self.startReadLog()

    def read(self, data):
        if data == None:
            self.close()
            return
        keyWords = data.rstrip()
        if keyWords == STOP_WORD:
            self.close()

    def close(self):
        GetLogBase.close(self)
        HandlerBase.close(self)

class GetLogFromWeb(GetLogBase, HttpHandlerBase):
    def __init__(self, *args, **kwargs):
        super(GetLogFromWeb, self).__init__(*args, **kwargs)
        self.initFilter()
       
    def initFilter(self):
        super(GetLogFromWeb, self).initFilter()
        fromTime = self.req.get("fromtime", None)
        toTime  = self.req.get("totime", None)
        if fromTime:
            fromTime = float(fromTime[0])
        if toTime:
            toTime = float(toTime[0])
        uid = int(self.req.get("uid")[0])
        procs = self.req.get("procs")
        if procs:
            procs = getProcMask(set(procs))
        else:
            procs = getProcMask()
        logLevel = self.req.get("loglevel")
        if logLevel:
            logLevel = sum([2**int(i) for i in logLevel])
        else:
            logLevel = FILTER_LOG_LEVELS
        cols = self.req.get("cols")
        if cols:
            cols = sum([2**int(i) for i in cols])
        else:
            cols = SHOW_COLS
        message = self.req.get("message", [""])[0]

        self.showCols = cols
        self.queryPara = {
            "start"     : 0,
            "end"       : 0,
            "uid"       : uid,
            "procs"     : procs,
            "severities": logLevel,
            "message"   : message,
        }
        self.startReadLog(fromTime, toTime)

    def sendResponseHeader(self):
        super(GetLogFromWeb, self).sendResponseHeader()
        styleAndScript = """
<style>
.log {font-size: 9pt;}
.highlight {color: red; font-weight:bold}
</style>
<script>
document.domain = "pangu.netease.com"
scrollFlag = true
function scrollWindow(){
  if(scrollFlag){
    scroll(0, document.body.scrollHeight);
  }
  setTimeout('scrollWindow()', 200);
}
scrollWindow()

String.prototype.replaceAll = function(oldStr, newStr) {
   return this.replace(new RegExp(oldStr,"g"),newStr); 
}
highLightContent = ""
function s(line){
    if(highLightContent != ""){
        line = line.replaceAll(highLightContent, "<span class=highlight>"+highLightContent+"</span>")
    }
    document.write("<div class=log>"+line+"</div>")
}
</script>
""" 
        self.write(styleAndScript)
        self.startSendLog = True
        self.sendKeepAliveToClient()
        
    def sendKeepAliveToClient(self):
        if getattr(self, "stopQuery", False):
            return
        self.write("<!--  keep alive -->\n")
        utils.callback(30, self.sendKeepAliveToClient)

    def write(self, msg):
        if getattr(self, "startSendLog", False):
            msg = msg.replace("\"", "\\\"")
            super(GetLogFromWeb, self).write("<script>s(\"%s\")</script>"%msg.rstrip())
        else:
            super(GetLogFromWeb, self).write(msg)

    def close(self):
        GetLogBase.close(self)
        HttpHandlerBase.close(self)
