# -*- coding:gbk -*-

import re
import utils

REQ_TYPE_RAW = 0
REQ_TYPE_HTTP = 1

DEFAULT_RAW_HANDLER = "handler.echo.RawEcho"
DEFAULT_HTTP_HANDLER = "handler.echo.HttpEcho"

URL_PATTERN = [
    ## 请求前缀， 请求类型，对应处理器class
    ("^/info$", REQ_TYPE_RAW, "handler.get_info.GetInfo"),
    ("^/test$", REQ_TYPE_RAW, "handler.test.Test"),
    ("^/log$", REQ_TYPE_RAW, "handler.get_log.GetLog"),
]
HTTP_PREFIX_RE = re.compile("(?P<method>\w+?) (?P<uri>.+?) HTTP/1.\d")
URL_PREFIX_RE = {}

def getHandlerFromData(data):
    def getCls(handlerName):
        modName, clsName = handlerName.rsplit(".", 1)
        pkgName, fileName = modName.rsplit(".", 1)
        mod = __import__(modName, globals(), locals(), [pkgName] )
        if not mod:
            return None
        return getattr(mod, clsName, None)

    def initUrlPrefixRegexp():
        for prefix, reqType, handlerName in URL_PATTERN:
            prefixRe = re.compile(prefix)
            URL_PREFIX_RE[reqType][prefixRe] = (prefix, reqType, handlerName)

    if not URL_PREFIX_RE:
        URL_PREFIX_RE[REQ_TYPE_RAW] = {}
        URL_PREFIX_RE[REQ_TYPE_HTTP] = {}
        initUrlPrefixRegexp()

    firstLine = data.split("\n")[0]
    firstLine = firstLine.strip()

    httpMatch = HTTP_PREFIX_RE.search(firstLine)
    urlPrefixRe = URL_PREFIX_RE[REQ_TYPE_RAW]
    if httpMatch:
        groupDict = httpMatch.groupdict()
        uri = groupDict.get("uri")
        for prefixRe, urlInfo in URL_PREFIX_RE[REQ_TYPE_HTTP].iteritems():
            matchObj = prefixRe.search(uri)
            if matchObj:
                return getCls(urlInfo[2])
        utils.logDebug("use httpraw: [%s]"%uri)
        return getCls(DEFAULT_HTTP_HANDLER)

    for prefixRe, urlInfo in URL_PREFIX_RE[REQ_TYPE_RAW].iteritems():
        matchObj = prefixRe.search(firstLine)
        if not matchObj:
            continue
        return getCls(urlInfo[2])
    utils.logDebug("use raw: [%s]"%firstLine)
    return getCls(DEFAULT_RAW_HANDLER)

