# ===============================================================================
#  DESCRIPTION:  Remote debugger
#        USAGE:  1. Add the following lines into the program:
#                   from sstest import rdb; rdb.set_trace()
#                2. Run your program or run your tests (any environment and configuration will work)
#                3, telnet <hostname> 4444
#                4. Use all usual pdb's commands
#                5. Hit 'c' (continue) pdb's command when you finished debugging
# ===============================================================================

import pdb
# import signal
import socket
import sys


class Rdb(pdb.Pdb):
    def __init__(self, port=4444):
        self.old_stdout = sys.stdout
        self.old_stdin = sys.stdin
        self.skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        while 1:
            try:
                self.skt.bind(('0.0.0.0', port))
                break
            except Exception:
                port += 1
        self.skt.listen(1)
        (clientsocket, address) = self.skt.accept()
        handle = clientsocket.makefile('rw')
        pdb.Pdb.__init__(self, completekey='tab', stdin=handle, stdout=handle)
        sys.stdout = sys.stdin = handle

    def do_continue(self, arg):
        sys.stdout = self.old_stdout
        sys.stdin = self.old_stdin
        self.skt.close()
        self.set_continue()
        return 1

    do_c = do_cont = do_continue


def start(sig, frame):
    Rdb().set_trace(frame)


# signal.signal(signal.SIGUSR1, start)
