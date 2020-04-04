#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

from w3af.plugins.attack.db.sqlmap.lib.core.common import Backend
from w3af.plugins.attack.db.sqlmap.lib.core.common import Format
from w3af.plugins.attack.db.sqlmap.lib.core.common import getUnicode
from w3af.plugins.attack.db.sqlmap.lib.core.data import conf
from w3af.plugins.attack.db.sqlmap.lib.core.data import kb
from w3af.plugins.attack.db.sqlmap.lib.core.data import logger
from w3af.plugins.attack.db.sqlmap.lib.core.enums import DBMS
from w3af.plugins.attack.db.sqlmap.lib.core.enums import OS
from w3af.plugins.attack.db.sqlmap.lib.core.session import setDbms
from w3af.plugins.attack.db.sqlmap.lib.core.settings import MSSQL_ALIASES
from w3af.plugins.attack.db.sqlmap.lib.request import inject
from w3af.plugins.attack.db.sqlmap.plugins.generic.fingerprint import Fingerprint as GenericFingerprint

class Fingerprint(GenericFingerprint):
    def __init__(self):
        GenericFingerprint.__init__(self, DBMS.MSSQL)

    def getFingerprint(self):
        value = ""
        wsOsFp = Format.getOs("web server", kb.headersFp)

        if wsOsFp:
            value += "%s\n" % wsOsFp

        if kb.data.banner:
            dbmsOsFp = Format.getOs("back-end DBMS", kb.bannerFp)

            if dbmsOsFp:
                value += "%s\n" % dbmsOsFp

        value += "back-end DBMS: "
        actVer = Format.getDbms()

        if not conf.extensiveFp:
            value += actVer
            return value

        blank = " " * 15
        value += "active fingerprint: %s" % actVer

        if kb.bannerFp:
            release = kb.bannerFp["dbmsRelease"] if 'dbmsRelease' in kb.bannerFp else None
            version = kb.bannerFp["dbmsVersion"] if 'dbmsVersion' in kb.bannerFp else None
            servicepack = kb.bannerFp["dbmsServicePack"] if 'dbmsServicePack' in kb.bannerFp else None

            if release and version and servicepack:
                banVer = "%s %s " % (DBMS.MSSQL, release)
                banVer += "Service Pack %s " % servicepack
                banVer += "version %s" % version

                value += "\n%sbanner parsing fingerprint: %s" % (blank, banVer)

        htmlErrorFp = Format.getErrorParsedDBMSes()

        if htmlErrorFp:
            value += "\n%shtml error message fingerprint: %s" % (blank, htmlErrorFp)

        return value

    def checkDbms(self):
        if not conf.extensiveFp and Backend.isDbmsWithin(MSSQL_ALIASES):
            setDbms("%s %s" % (DBMS.MSSQL, Backend.getVersion()))

            self.getBanner()

            Backend.setOs(OS.WINDOWS)

            return True

        infoMsg = "testing %s" % DBMS.MSSQL
        logger.info(infoMsg)

        # NOTE: SELECT LEN(@@VERSION)=LEN(@@VERSION) FROM DUAL does not
        # work connecting directly to the Microsoft SQL Server database
        if conf.direct:
            result = True
        else:
            result = inject.checkBooleanExpression("UNICODE(SQUARE(NULL)) IS NULL")

        if result:
            infoMsg = "confirming %s" % DBMS.MSSQL
            logger.info(infoMsg)

            for version, check in (("2000", "HOST_NAME()=HOST_NAME()"), \
                                    ("2005", "XACT_STATE()=XACT_STATE()"), \
                                    ("2008", "SYSDATETIME()=SYSDATETIME()"), \
                                    ("2012", "CONCAT(NULL,NULL)=CONCAT(NULL,NULL)"), \
                                    ("2014", "CHARINDEX('12.0.2000',@@version)>0"), \
                                    ("2016", "ISJSON(NULL) IS NULL")):
                result = inject.checkBooleanExpression(check)

                if result:
                    Backend.setVersion(version)

            if Backend.getVersion():
                setDbms("%s %s" % (DBMS.MSSQL, Backend.getVersion()))
            else:
                setDbms(DBMS.MSSQL)

            self.getBanner()

            Backend.setOs(OS.WINDOWS)

            return True
        else:
            warnMsg = "the back-end DBMS is not %s" % DBMS.MSSQL
            logger.warn(warnMsg)

            return False

    def checkDbmsOs(self, detailed=False):
        if Backend.getOs() and Backend.getOsVersion() and Backend.getOsServicePack():
            return

        if not Backend.getOs():
            Backend.setOs(OS.WINDOWS)

        if not detailed:
            return

        infoMsg = "fingerprinting the back-end DBMS operating system "
        infoMsg += "version and service pack"
        logger.info(infoMsg)

        infoMsg = "the back-end DBMS operating system is %s" % Backend.getOs()

        self.createSupportTbl(self.fileTblName, self.tblField, "varchar(1000)")
        inject.goStacked("INSERT INTO %s(%s) VALUES (%s)" % (self.fileTblName, self.tblField, "@@VERSION"))

        # Reference: http://en.wikipedia.org/wiki/Comparison_of_Microsoft_Windows_versions
        # http://en.wikipedia.org/wiki/Windows_NT#Releases
        versions = { "NT": ("4.0", (6, 5, 4, 3, 2, 1)),
                     "2000": ("5.0", (4, 3, 2, 1)),
                     "XP": ("5.1", (3, 2, 1)),
                     "2003": ("5.2", (2, 1)),
                     "Vista or 2008": ("6.0", (2, 1)),
                     "7 or 2008 R2": ("6.1", (1, 0)),
                     "8 or 2012": ("6.2", (0,)),
                     "8.1 or 2012 R2": ("6.3", (0,)) }

        # Get back-end DBMS underlying operating system version
        for version, data in list(versions.items()):
            query = "EXISTS(SELECT %s FROM %s WHERE %s " % (self.tblField, self.fileTblName, self.tblField)
            query += "LIKE '%Windows NT " + data[0] + "%')"
            result = inject.checkBooleanExpression(query)

            if result:
                Backend.setOsVersion(version)
                infoMsg += " %s" % Backend.getOsVersion()
                break

        if not Backend.getOsVersion():
            Backend.setOsVersion("2003")
            Backend.setOsServicePack(2)

            warnMsg = "unable to fingerprint the underlying operating "
            warnMsg += "system version, assuming it is Windows "
            warnMsg += "%s Service Pack %d" % (Backend.getOsVersion(), Backend.getOsServicePack())
            logger.warn(warnMsg)

            self.cleanup(onlyFileTbl=True)

            return

        # Get back-end DBMS underlying operating system service pack
        sps = versions[Backend.getOsVersion()][1]
        for sp in sps:
            query = "EXISTS(SELECT %s FROM %s WHERE %s " % (self.tblField, self.fileTblName, self.tblField)
            query += "LIKE '%Service Pack " + getUnicode(sp) + "%')"
            result = inject.checkBooleanExpression(query)

            if result:
                Backend.setOsServicePack(sp)
                break

        if not Backend.getOsServicePack():
            debugMsg = "assuming the operating system has no service pack"
            logger.debug(debugMsg)

            Backend.setOsServicePack(0)

        if Backend.getOsVersion():
            infoMsg += " Service Pack %d" % Backend.getOsServicePack()

        logger.info(infoMsg)

        self.cleanup(onlyFileTbl=True)
