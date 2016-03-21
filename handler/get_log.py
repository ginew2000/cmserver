# -*- coding:gbk -*-

from base import HandlerBase, HttpHandlerBase
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

class GetLogBase(object):
    def initFilter(self):
        self.stopQuery = False
        self.mlog = bwlog.BWLog( MESSAGE_LOG_ROOT )
        self.query = None
        ## ����2��������������
        self.showCols = 0
        self.queryPara = {}

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
            self.write("ʱ�����ô���from=%s, to=%s\n"%(fromTime, toTime))

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
            "start"     : 0,    ##��ѯ��ʼʱ��
            "end"       : 0,    ##��ѯ����ʱ�䣨��������
            "uid"       : 1001, ##�û�id
            "procs"     : getProcMask(),     ##����������������
            "severities": FILTER_LOG_LEVELS, ##��������log����
            "message"   : "", ##������������
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
