# -*- coding:gbk -*-

import signal
import pyuv

import client_info

def startServer():
    def signal_cb(handle, signum):
        client_info.closeAllClients()
        signal_h.close()
        server.close()

    print "PyUV version %s" % pyuv.__version__

    loop = pyuv.Loop.default_loop()
    server = pyuv.TCP(loop)
    server.bind(("0.0.0.0", 2222))
    server.listen(client_info.on_connection)

    signal_h = pyuv.Signal(loop)
    signal_h.start(signal_cb, signal.SIGINT)

    loop.run()
    print "Stopped!"

def main():
    startServer() 


if __name__ == "__main__":
    main()
