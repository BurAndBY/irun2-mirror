import MySQLdb

from django.core.files.base import ContentFile


def connect_irunner_db():
    db = MySQLdb.connect(user='irunner_user', passwd='irunner_localhost',
                         host='127.0.0.1',
                         port=3307,
                         db='irunner',
                         charset='utf8')
    return db


def fetch_irunner_file(db, file_id, storage):
    '''
    Returns a tuple (filename, resource_id) or None
    '''
    cur = db.cursor()
    cur.execute('''SELECT name, data FROM katrin_file WHERE fileID = %s''', (file_id,))

    for row in cur:
        filename = row[0]
        size = len(row[1])
        resource_id = storage.save(ContentFile(row[1]))
        return (filename, size, resource_id)

    return None
