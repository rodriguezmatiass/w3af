#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

try:
    import sqlite3
except:
    pass

import logging

from w3af.plugins.attack.db.sqlmap.lib.core.convert import utf8encode
from w3af.plugins.attack.db.sqlmap.lib.core.data import conf
from w3af.plugins.attack.db.sqlmap.lib.core.data import logger
from w3af.plugins.attack.db.sqlmap.lib.core.exception import SqlmapConnectionException
from w3af.plugins.attack.db.sqlmap.lib.core.exception import SqlmapMissingDependence
from w3af.plugins.attack.db.sqlmap.plugins.generic.connector import Connector as GenericConnector


class Connector(GenericConnector):
    """
    Homepage: http://pysqlite.googlecode.com/ and http://packages.ubuntu.com/quantal/python-sqlite
    User guide: http://docs.python.org/release/2.5/lib/module-sqlite3.html
    API: http://docs.python.org/library/sqlite3.html
    Debian package: python-sqlite (SQLite 2), python-pysqlite3 (SQLite 3)
    License: MIT

    Possible connectors: http://wiki.python.org/moin/SQLite
    """

    def __init__(self):
        GenericConnector.__init__(self)
        self.__sqlite = sqlite3

    def connect(self):
        self.initConnection()
        self.checkFileDb()

        try:
            self.connector = self.__sqlite.connect(database=self.db, check_same_thread=False, timeout=conf.timeout)

            cursor = self.connector.cursor()
            cursor.execute("SELECT * FROM sqlite_master")
            cursor.close()

        except (self.__sqlite.DatabaseError, self.__sqlite.OperationalError) as msg:
            warnMsg = "unable to connect using SQLite 3 library, trying with SQLite 2"
            logger.warn(warnMsg)

            try:
                try:
                    import sqlite
                except ImportError:
                    errMsg = "sqlmap requires 'python-sqlite' third-party library "
                    errMsg += "in order to directly connect to the database '%s'" % self.db
                    raise SqlmapMissingDependence(errMsg)

                self.__sqlite = sqlite
                self.connector = self.__sqlite.connect(database=self.db, check_same_thread=False, timeout=conf.timeout)
            except (self.__sqlite.DatabaseError, self.__sqlite.OperationalError) as msg:
                raise SqlmapConnectionException(msg[0])

        self.initCursor()
        self.printConnected()

    def fetchall(self):
        try:
            return self.cursor.fetchall()
        except self.__sqlite.OperationalError as msg:
            logger.log(logging.WARN if conf.dbmsHandler else logging.DEBUG, "(remote) %s" % msg[0])
            return None

    def execute(self, query):
        try:
            self.cursor.execute(utf8encode(query))
        except self.__sqlite.OperationalError as msg:
            logger.log(logging.WARN if conf.dbmsHandler else logging.DEBUG, "(remote) %s" % msg[0])
        except self.__sqlite.DatabaseError as msg:
            raise SqlmapConnectionException(msg[0])

        self.connector.commit()

    def select(self, query):
        self.execute(query)
        return self.fetchall()
