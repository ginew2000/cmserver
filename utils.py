# -*- coding:gbk -*-

import pyuv
import time, os, sys, traceback

LOG_FILE_SERVER = "logs/server.log"
LOG_FILE_HANDLER = "logs/%s.log"

loop = None
def getLibUVLoop():
    global loop
    if not loop:
        loop = pyuv.Loop.default_loop()
    return loop

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
    if type(errmsg) != str:
        errmsg = str(errmsg)
    log("[ERROR]%s"%errmsg, handler)

def exceptHook(ty, val, tb):
    sys.__excepthook__(ty, val, tb)
    localVars = None
    try:
        tag = tb.tb_frame.f_locals.get('__name__')
        tbNext = tb
        while tbNext.tb_next:
            tbNext = tbNext.tb_next
        if tbNext.tb_frame.f_locals:
            varDict = {}
            for k, v in tbNext.tb_frame.f_locals.iteritems():
                sv = str(v)
                if len(sv) > 200:
                    varDict[k] = sv[:200] + '...(more)'
                else:
                    varDict[k] = sv
            varMsg = str(varDict)
            if len(varMsg) > 1000:
                varMsg = varMsg[:1000] + '...(more)'
            localVars = 'Locals (only top stack frame):\n%s\n' % varMsg
    except:
        print "unknow exception", str(traceback.format_exc())
    
    content = [localVars or "\n"]
    for e in traceback.format_exception(ty, val, tb):
        content.append(e)
    logError("".join(content))

class Functor(object):
    def __init__( self, fn, *args ):
        self.fn = fn
        self.args = args
    
    def __call__( self, *args ):
        try:
            return self.fn( *(self.args + args) )
        except:
            logError("Functor error: fn=%s, args=%s, error=%s"%(self.fn, self.args + args, str(traceback.format_exc())))

"""
def onDoneCallback(proc, exit_status, term_signal)
def onReadCallback(handle, data, error)
"""
def runCmd(cmd, onReadCallback=None, onDoneCallback=None):
    stdio = None
    loop = getLibUVLoop()
    if onReadCallback:
        stdout_pipe = pyuv.Pipe(loop)
        stdio = []
        stdio.append(pyuv.StdIO(flags=pyuv.UV_IGNORE))
        stdio.append(pyuv.StdIO(stream=stdout_pipe, flags=pyuv.UV_CREATE_PIPE|pyuv.UV_WRITABLE_PIPE))

    proc = pyuv.Process.spawn(loop, args=cmd.split(" "), exit_callback=onDoneCallback, stdio=stdio)
    if onReadCallback:
        stdout_pipe.start_read(onReadCallback)

"""
def cb(timer)
"""
def callback(waitTime, cb):
    loop = getLibUVLoop()
    timer = pyuv.Timer(loop)
    timer.start(cb, waitTime, 0)
