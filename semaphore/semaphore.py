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
HOST = '127.0.0.1'
PORT = 17083


class SemaphoreHolder(object):
    def __init__(self):
        self._default_sem = multiprocessing.Semaphore(0)
        self._lock = multiprocessing.Lock()
        self._sems = {}

    def get(self, tag):
        if tag is None:
            return self._default_sem

        with self._lock:
            sem = self._sems.get(tag)
            if sem is None:
                sem = multiprocessing.Semaphore(0)
                self._sems[tag] = sem

        return sem


semaphores = SemaphoreHolder()


class Handler(BaseHTTPRequestHandler):
    def _get_path(self):
        p = self.path
        if p.startswith(SCRIPT_PATH):
            return p[len(SCRIPT_PATH):]
        return p

    def _signal(self, tag):
        semaphores.get(tag).release()
        return True

    def _wait(self, tag):
        return semaphores.get(tag).acquire(True, TIMEOUT)

    def do_POST(self):
        tag = self.headers.getheader('X-iRunner-Worker-Tag', None)
        path = self._get_path()

        ok = False
        if path == '/signal':
            ok = self._signal(tag)
        elif path == '/wait':
            ok = self._wait(tag)

        self.send_response(httplib.OK if ok else httplib.NOT_FOUND)
        self.end_headers()

    def do_GET(self):
        path = self._get_path()

        if path == '/':
            self.send_response(httplib.OK)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write('OK')
        elif path in ('/signal', '/wait'):
            self.send_response(httplib.METHOD_NOT_ALLOWED)
            self.end_headers()
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
        self.server = ThreadedHTTPServer((HOST, PORT), Handler)

    # core logic of the service
    def SvcDoRun(self):
        self.server.serve_forever()

    # called when we're being shut down
    def SvcStop(self):
        # tell the SCM we're shutting down
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.server.shutdown()


def main():
    server = ThreadedHTTPServer((HOST, PORT), Handler)
    server.serve_forever()


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(PySvc)
    # main()
