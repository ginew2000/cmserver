# -*- coding:gbk -*-

from echo import RawEcho
import client_info, msgs, url_pattern, utils
import time, sys, os, traceback

class ReloadHandlers(RawEcho):
    def __init__(self, clientInfo):
        super(ReloadHandlers, self).__init__(clientInfo)
        self.outData = []
        self._reloadHandlers()

    def _reloadHandlers(self):
        def getOldModule (modName):
            if modName not in sys.modules:
                return None
            mod = sys.modules[modName]
            fileNamePy = mod.__file__
            fileNamePyc = fileNamePy
            if fileNamePy[-3:] == "pyc":
                fileNamePy = fileNamePy[0:-1]
            if fileNamePyc[-3:] == ".py":
                fileNamePyc = fileNamePyc + "c"
            if not os.path.exists(fileNamePyc):
                return mod
            if not os.path.exists(fileNamePy):
                return None
            mTimePyc = os.stat(fileNamePyc).st_mtime
            mTimePy = os.stat(fileNamePy).st_mtime
            if mTimePy > mTimePyc:
                return mod
            return None
 
        handlerPath = os.path.dirname(os.path.realpath(__file__))
        try:
            handlerFiles = [fName for fName in os.listdir(handlerPath)]
        except Exception, e:
            self.setOutput("[ERROR]%s\n"%str(traceback.format_exc()))
            return
        for fName in handlerFiles:
            if fName.startswith("__"):
                continue
            if fName[-3:] != ".py":
                continue
            
            modName = "handler.%s"%fName[0:-3]
            oldMod = getOldModule(modName)
            if oldMod:
                self.setOutput("%s reloading..."%modName)
                reload(oldMod)
            else:
                self.setOutput("%s no need reload."%modName)

class EvalHandler(RawEcho):
    def __init__(self, clientInfo):
        super(EvalHandler, self).__init__(clientInfo)
        self.codeLines = []
        self.outData = []

    def read(self, data):
        if data == None:
            self.clientInfo.close()
            return
        code = data.rstrip()
        if code == "/eval":
            self.clientInfo.write("input your code. 2 empty line will run your code\n")
            return
        if code == "" and self.codeLines[-1] == "":
            self._runCode()
            self.startWriteMonitor()
            return
        self.codeLines.append(code)

    def startWriteMonitor(self):
        for data in self.getOutput():
            self.clientInfo.write(data+"\n")
        self.clientInfo.changeHandler()

    def _runCode(self):
        code = "\n".join(self.codeLines)
        retCode = None
        try:
            retCode = eval(code)
        except Exception, e:
            self.setOutput("[ERROR]%s"%str(traceback.format_exc()))
        if retCode != None:    
            self.setOutput("return: %s"%retCode)
        self.codeLines = []

