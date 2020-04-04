#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

from w3af.plugins.attack.db.sqlmap.lib.core.common import Backend
from w3af.plugins.attack.db.sqlmap.lib.core.data import conf
from w3af.plugins.attack.db.sqlmap.lib.core.data import kb
from w3af.plugins.attack.db.sqlmap.lib.core.dicts import DBMS_DICT
from w3af.plugins.attack.db.sqlmap.lib.core.enums import DBMS
from w3af.plugins.attack.db.sqlmap.lib.core.settings import MSSQL_ALIASES
from w3af.plugins.attack.db.sqlmap.lib.core.settings import MYSQL_ALIASES
from w3af.plugins.attack.db.sqlmap.lib.core.settings import ORACLE_ALIASES
from w3af.plugins.attack.db.sqlmap.lib.core.settings import PGSQL_ALIASES
from w3af.plugins.attack.db.sqlmap.lib.core.settings import SQLITE_ALIASES
from w3af.plugins.attack.db.sqlmap.lib.core.settings import ACCESS_ALIASES
from w3af.plugins.attack.db.sqlmap.lib.core.settings import FIREBIRD_ALIASES
from w3af.plugins.attack.db.sqlmap.lib.core.settings import MAXDB_ALIASES
from w3af.plugins.attack.db.sqlmap.lib.core.settings import SYBASE_ALIASES
from w3af.plugins.attack.db.sqlmap.lib.core.settings import DB2_ALIASES
from w3af.plugins.attack.db.sqlmap.lib.core.settings import HSQLDB_ALIASES
from w3af.plugins.attack.db.sqlmap.lib.core.settings import INFORMIX_ALIASES
from w3af.plugins.attack.db.sqlmap.lib.utils.sqlalchemy import SQLAlchemy

from w3af.plugins.attack.db.sqlmap.plugins.dbms.mssqlserver import MSSQLServerMap
from w3af.plugins.attack.db.sqlmap.plugins.dbms.mssqlserver.connector import Connector as MSSQLServerConn
from w3af.plugins.attack.db.sqlmap.plugins.dbms.mysql import MySQLMap
from w3af.plugins.attack.db.sqlmap.plugins.dbms.mysql.connector import Connector as MySQLConn
from w3af.plugins.attack.db.sqlmap.plugins.dbms.oracle import OracleMap
from w3af.plugins.attack.db.sqlmap.plugins.dbms.oracle.connector import Connector as OracleConn
from w3af.plugins.attack.db.sqlmap.plugins.dbms.postgresql import PostgreSQLMap
from w3af.plugins.attack.db.sqlmap.plugins.dbms.postgresql.connector import Connector as PostgreSQLConn
from w3af.plugins.attack.db.sqlmap.plugins.dbms.sqlite import SQLiteMap
from w3af.plugins.attack.db.sqlmap.plugins.dbms.sqlite.connector import Connector as SQLiteConn
from w3af.plugins.attack.db.sqlmap.plugins.dbms.access import AccessMap
from w3af.plugins.attack.db.sqlmap.plugins.dbms.access.connector import Connector as AccessConn
from w3af.plugins.attack.db.sqlmap.plugins.dbms.firebird import FirebirdMap
from w3af.plugins.attack.db.sqlmap.plugins.dbms.firebird.connector import Connector as FirebirdConn
from w3af.plugins.attack.db.sqlmap.plugins.dbms.maxdb import MaxDBMap
from w3af.plugins.attack.db.sqlmap.plugins.dbms.maxdb.connector import Connector as MaxDBConn
from w3af.plugins.attack.db.sqlmap.plugins.dbms.sybase import SybaseMap
from w3af.plugins.attack.db.sqlmap.plugins.dbms.sybase.connector import Connector as SybaseConn
from w3af.plugins.attack.db.sqlmap.plugins.dbms.db2 import DB2Map
from w3af.plugins.attack.db.sqlmap.plugins.dbms.db2.connector import Connector as DB2Conn
from w3af.plugins.attack.db.sqlmap.plugins.dbms.hsqldb import HSQLDBMap
from w3af.plugins.attack.db.sqlmap.plugins.dbms.hsqldb.connector import Connector as HSQLDBConn
from w3af.plugins.attack.db.sqlmap.plugins.dbms.informix import InformixMap
from w3af.plugins.attack.db.sqlmap.plugins.dbms.informix.connector import Connector as InformixConn

def setHandler():
    """
    Detect which is the target web application back-end database
    management system.
    """

    items = [
                  (DBMS.MYSQL, MYSQL_ALIASES, MySQLMap, MySQLConn),
                  (DBMS.ORACLE, ORACLE_ALIASES, OracleMap, OracleConn),
                  (DBMS.PGSQL, PGSQL_ALIASES, PostgreSQLMap, PostgreSQLConn),
                  (DBMS.MSSQL, MSSQL_ALIASES, MSSQLServerMap, MSSQLServerConn),
                  (DBMS.SQLITE, SQLITE_ALIASES, SQLiteMap, SQLiteConn),
                  (DBMS.ACCESS, ACCESS_ALIASES, AccessMap, AccessConn),
                  (DBMS.FIREBIRD, FIREBIRD_ALIASES, FirebirdMap, FirebirdConn),
                  (DBMS.MAXDB, MAXDB_ALIASES, MaxDBMap, MaxDBConn),
                  (DBMS.SYBASE, SYBASE_ALIASES, SybaseMap, SybaseConn),
                  (DBMS.DB2, DB2_ALIASES, DB2Map, DB2Conn),
                  (DBMS.HSQLDB, HSQLDB_ALIASES, HSQLDBMap, HSQLDBConn),
                  (DBMS.INFORMIX, INFORMIX_ALIASES, InformixMap, InformixConn),
            ]

    _ = max(_ if (conf.get("dbms") or Backend.getIdentifiedDbms() or kb.heuristicExtendedDbms or "").lower() in _[1] else None for _ in items)
    if _:
        items.remove(_)
        items.insert(0, _)

    for dbms, aliases, Handler, Connector in items:
        if conf.forceDbms:
            if conf.forceDbms.lower() not in aliases:
                continue
            else:
                kb.dbms = conf.dbms = conf.forceDbms = dbms

        if kb.dbmsFilter:
            if dbms not in kb.dbmsFilter:
                continue

        handler = Handler()
        conf.dbmsConnector = Connector()

        if conf.direct:
            dialect = DBMS_DICT[dbms][3]

            if dialect:
                sqlalchemy = SQLAlchemy(dialect=dialect)
                sqlalchemy.connect()

                if sqlalchemy.connector:
                    conf.dbmsConnector = sqlalchemy
                else:
                    try:
                        conf.dbmsConnector.connect()
                    except NameError:
                        pass
            else:
                conf.dbmsConnector.connect()

        if conf.forceDbms == dbms or handler.checkDbms():
            if kb.resolutionDbms:
                conf.dbmsHandler = max(_ for _ in items if _[0] == kb.resolutionDbms)[2]()
            else:
                conf.dbmsHandler = handler

            conf.dbmsHandler._dbms = dbms
            break
        else:
            conf.dbmsConnector = None

    # At this point back-end DBMS is correctly fingerprinted, no need
    # to enforce it anymore
    Backend.flushForcedDbms()
