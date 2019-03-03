import httplib
import multiprocessing
import socket
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn

import win32service
import win32serviceutil

sem = multiprocessing.Semaphore(0)

TIMEOUT = 20
SCRIPT_PATH = ''
PORT = 17083


class Handler(BaseHTTPRequestHandler):
    def _get_path(self):
        p = self.path
        if p.startswith(SCRIPT_PATH):
            return p[len(SCRIPT_PATH):]
        return p

    def _signal(self):
        sem.release()
        return True

    def _wait(self):
        return sem.acquire(True, TIMEOUT)

    def do_POST(self):
        path = self._get_path()

        ok = False
        if path == '/signal':
            ok = self._signal()
        elif path == '/wait':
            ok = self._wait()

        self.send_response(httplib.OK if ok else httplib.NOT_FOUND)
        self.end_headers()

    def do_GET(self):
        path = self._get_path()

        if path == '/':
            self.send_response(httplib.OK)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write('OK')
        else:
            self.send_response(httplib.NOT_FOUND)
            self.end_headers()


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


class PySvc(win32serviceutil.ServiceFramework):
    # you can NET START/STOP the service by the following name
    _svc_name_ = "HttpSemaphore"
    # this text shows up as the service name in the Service
    # Control Manager (SCM)
    _svc_display_name_ = "HTTP Semaphore Service"
    # this text shows up as the description in the SCM
    _svc_description_ = "Semaphore with HTTP API"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        socket.setdefaulttimeout(60)
        self.server = ThreadedHTTPServer(('127.0.0.1', PORT), Handler)

    # core logic of the service
    def SvcDoRun(self):
        self.server.serve_forever()

    # called when we're being shut down
    def SvcStop(self):
        # tell the SCM we're shutting down
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.server.shutdown()


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(PySvc)
