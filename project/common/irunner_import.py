import MySQLdb


def connect_irunner_db():
    db = MySQLdb.connect(user='irunner_user', passwd='irunner_localhost',
                         host='127.0.0.1',
                         port=3307,
                         db='irunner',
                         charset='utf8')
    return db
