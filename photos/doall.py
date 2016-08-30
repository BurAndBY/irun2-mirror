# -*- coding: utf-8 -*-

import json
import os
import sys
import urllib
import urllib2
import zipfile

from parse_func import parse_intranet_bsu_html

BASE_URL = 'http://intranet.bsu/resurses/Students/Find/'
FAMCS = '3'


def fetch_page(first_name, last_name, patronymic):
    params = {
        'IdF': FAMCS,
        'IncludeAchrive': '1',
    }

    def add(key, value):
        if value is not None:
            value = value.replace('(EPS)', '').replace('(eps)', '').strip()
            if value:
                params[key] = value.encode('cp1251')

    add('NameF', last_name)
    add('NameI', first_name)
    add('NameO', patronymic)

    data = urllib.urlencode(params)
    req = urllib2.Request(BASE_URL, data)
    response = urllib2.urlopen(req)
    return response.read().decode('cp1251')


def filter_by_group(intranet, group):
    for x in intranet:
        if x.get('group') == group:
            yield x


def download_photos(data, archive_name, group=None):
    with zipfile.ZipFile(archive_name, 'w') as zf:
        for student in data['users']:
            user_id = student['id']
            intranet = student.get('intranet')
            if intranet is not None:
                if group is not None:
                    intranet = list(filter_by_group(intranet, group))

                if len(intranet) == 0 or len(intranet) > 1:
                    print >>sys.stderr, 'WARNING:', len(intranet), 'photos for', user_id
                if len(intranet) > 0:
                    photo = intranet[0]['photo']
                    blob = urllib.urlopen(BASE_URL + photo).read()
                    zf.writestr(student['username'] + '.jpg', blob)


def main():
    filename = sys.argv[1]
    group = None
    if len(sys.argv) > 2:
        group = int(sys.argv[2])

    name, ext = os.path.splitext(filename)

    with open('{0}.json'.format(name), 'rb') as fd:
        data = json.load(fd)

    for student in data['users']:
        page = fetch_page(student.get('firstName'), student.get('lastName'), student.get('patronymic'))
        student['intranet'] = parse_intranet_bsu_html(page)

    with open('{0}_intranet.json'.format(name), 'wb') as fd:
        blob = json.dumps(data, ensure_ascii=False, indent=4)
        fd.write(unicode(blob).encode('utf-8'))

    download_photos(data, '{0}.zip'.format(name), group)

if __name__ == '__main__':
    main()
