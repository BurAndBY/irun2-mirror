# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
import logging
import os
import subprocess
import time
import urllib2

DIRECTORY = 'printouts'


class IPrinter(object):
    def __init__(self, endpoint, token, printers):
        self.endpoint = endpoint
        self.token = token
        self.printers = printers

        logging.info('endpoint: %s', endpoint)
        logging.info('rooms: %s', ', '.join(printers.keys()))

        if not os.path.isdir(DIRECTORY):
            os.mkdir(DIRECTORY)

    def make_headers(self):
        headers = {}
        if self.token is not None:
            headers['Worker-Token'] = self.token
        return headers

    def get(self):
        logging.info('< requesting new printouts...')

        request = urllib2.Request(self.endpoint, headers=self.make_headers())
        response = urllib2.urlopen(request).read()
        result = json.loads(response, encoding='utf-8')

        logging.info('> got printouts: %d', len(result))
        return result

    def post(self, pk):
        logging.info('> finalizing printout %d...', pk)

        url = '{0}/{1}'.format(self.endpoint, pk)
        request = urllib2.Request(url, headers=self.make_headers(), data='')
        urllib2.urlopen(request).read()

        logging.info('< done')

    def process(self, printout, printer):
        pk = printout['id']
        text = printout['text']
        room = printout['room']

        logging.info('printing #%d (%d bytes) to room %s ("%s")', pk, len(text), room, printer)

        data = [
            'Team: {0} — {1} (room {2})'.format(printout['username'], printout['user'], printout['room']),
            'Time: {0}'.format(printout['timestamp']),
            '_' * 80,
            '',
        ] + text.splitlines()

        fn = os.path.join(DIRECTORY, '%04d.txt' % (pk,))
        with open(fn, 'wb') as fd:
            fd.write(b'\xEF\xBB\xBF')
            for s in data:
                fd.write(s.encode('utf-8') + b'\r\n')

        if printer:
            # WARNING: Do not use check_call(['notepad.exe', fn, ...]):
            # it does not work because notepad.exe requires quoted arguments.
            subprocess.check_call('notepad.exe /PT "{0}" "{1}"'.format(fn, printer))

    def run(self):
        printouts = self.get()
        for printout in printouts:
            pk = printout['id']
            printer = self.printers.get(printout['room'])
            if printer is not None:
                self.process(printout, printer)
                self.post(pk)
                return


def load_config():
    with open('config.json', 'r') as fd:
        return json.load(fd, encoding='utf-8')


def main():
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)

    config = load_config()

    ip = IPrinter(config['endpoint'], config.get('token'), config.get('printers', []))

    while True:
        try:
            ip.run()
        except urllib2.URLError:
            pass
        time.sleep(5)

if __name__ == '__main__':
    main()
