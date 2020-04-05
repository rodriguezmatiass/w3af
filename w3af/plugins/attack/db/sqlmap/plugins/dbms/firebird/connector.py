#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

try:
    import kinterbasdb
except:
    pass

import logging

from w3af.plugins.attack.db.sqlmap.lib.core.data import conf
from w3af.plugins.attack.db.sqlmap.lib.core.data import logger
from w3af.plugins.attack.db.sqlmap.lib.core.exception import SqlmapConnectionException
from w3af.plugins.attack.db.sqlmap.lib.core.settings import UNICODE_ENCODING
from w3af.plugins.attack.db.sqlmap.plugins.generic.connector import Connector as GenericConnector

class Connector(GenericConnector):
    """
    Homepage: http://kinterbasdb.sourceforge.net/
    User guide: http://kinterbasdb.sourceforge.net/dist_docs/usage.html
    Debian package: python-kinterbasdb
    License: BSD
    """

    def __init__(self):
        GenericConnector.__init__(self)

    # sample usage:
    # ./sqlmap.py -d "firebird://sysdba:testpass@/opt/firebird/testdb.fdb"
    # ./sqlmap.py -d "firebird://sysdba:testpass@127.0.0.1:3050//opt/firebird/testdb.fdb"
    def connect(self):
        self.initConnection()

        if not self.hostname:
            self.checkFileDb()

        try:
            self.connector = kinterbasdb.connect(host=self.hostname.encode(UNICODE_ENCODING), database=self.db.encode(UNICODE_ENCODING),
                user=self.user.encode(UNICODE_ENCODING), password=self.password.encode(UNICODE_ENCODING), charset="UTF8")  # Reference: http://www.daniweb.com/forums/thread248499.html
        except kinterbasdb.OperationalError as msg:
            raise SqlmapConnectionException(msg[1])

        self.initCursor()
        self.printConnected()

    def fetchall(self):
        try:
            return self.cursor.fetchall()
        except kinterbasdb.OperationalError as msg:
            logger.log(logging.WARN if conf.dbmsHandler else logging.DEBUG, "(remote) %s" % msg[1])
            return None

    def execute(self, query):
        try:
            self.cursor.execute(query)
        except kinterbasdb.OperationalError as msg:
            logger.log(logging.WARN if conf.dbmsHandler else logging.DEBUG, "(remote) %s" % msg[1])
        except kinterbasdb.Error as msg:
            raise SqlmapConnectionException(msg[1])

        self.connector.commit()

    def select(self, query):
        self.execute(query)
        return self.fetchall()
