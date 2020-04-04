#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

from w3af.plugins.attack.db.sqlmap.lib.core.data import logger

from w3af.plugins.attack.db.sqlmap.plugins.generic.enumeration import Enumeration as GenericEnumeration

class Enumeration(GenericEnumeration):
    def __init__(self):
        GenericEnumeration.__init__(self)

    def getHostname(self):
        warnMsg = "on PostgreSQL it is not possible to enumerate the hostname"
        logger.warn(warnMsg)
