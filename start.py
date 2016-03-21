# -*- coding:gbk -*-

import sys

import signal
import pyuv

import client_info, utils
#import gc
#gc.disable()

def startServer():
    def signal_cb(handle, signum):
        client_info.closeAllClients()
        signal_h.close()
        server.close()

    utils.log("PyUV version %s" % pyuv.__version__)

    loop = utils.getLibUVLoop()
    server = pyuv.TCP(loop)
    server.bind(("0.0.0.0", 2222))
    server.listen(client_info.on_connection)

    signal_h = pyuv.Signal(loop)
    signal_h.start(signal_cb, signal.SIGINT)

    loop.run()
    utils.log("Stopped!")

def main():
    sys.excepthook = utils.exceptHook
    startServer() 


if __name__ == "__main__":
    main()
