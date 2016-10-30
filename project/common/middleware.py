from __future__ import unicode_literals

PREFIX = '/irunner2'

def fix(s):
    if s and s.startswith(PREFIX):
        return s[len(PREFIX):]
    return s

class CutPrefix(object):
    def process_request(self, request):
        request.path = fix(request.path)
        request.path_info = fix(request.path_info)
