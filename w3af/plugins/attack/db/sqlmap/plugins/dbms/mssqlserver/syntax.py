#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

from w3af.plugins.attack.db.sqlmap.plugins.generic.syntax import Syntax as GenericSyntax

class Syntax(GenericSyntax):
    def __init__(self):
        GenericSyntax.__init__(self)

    @staticmethod
    def escape(expression, quote=True):
        """
        >>> Syntax.escape("SELECT 'abcdefgh' FROM foobar")
        'SELECT CHAR(97)+CHAR(98)+CHAR(99)+CHAR(100)+CHAR(101)+CHAR(102)+CHAR(103)+CHAR(104) FROM foobar'
        """

        def escaper(value):
            return "+".join("%s(%d)" % ("CHAR" if ord(value[i]) < 256 else "NCHAR", ord(value[i])) for i in range(len(value)))

        return Syntax._escape(expression, quote, escaper)
