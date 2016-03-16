# -*- coding:gbk -*-

import time, os
LOG_FILE_SERVER = "logs/server.log"
LOG_FILE_HANDLER = "logs/%s.log"

def log(msg, handler=None):
    logFile = LOG_FILE_SERVER
    if handler:
         logFile = LOG_FILE_HANDLER % handler

    if type(msg) != str:
        msg = str(msg)
    print handler or "SERVER", msg
    return

    if msg[-1] != "\n":
        msg = msg + "\n"

    nowTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    msg = "[%s]%s"%(nowTime, msg)

    dirName = os.path.dirname(logFile)
    if not os.path.exists(dirName):
        os.makedirs(dirName)
    fp = open(logFile, "a+")
    fp.write(msg)
    fp.close()

def logDebug (msg, handler=None):
    if type(msg) != str:
        msg = str(msg)
    log("[DEBUG]%s"%msg, handler)
       
def logError (errmsg, handler=None):
    if type(msg) != str:
        msg = str(msg)
    log("[ERROR]%s"%errmsg, handler)

