"""
get_net_iface.py

Copyright 2009 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""

import os
import socket
from w3af.core.controllers.misc.get_local_ip import get_local_ip


def get_net_iface():
    """
    This function is very OS dependant.

    :return: The interface name that is being used to connect to the net.
    """
    #   Get the IP address thats used to go to the Internet
    internet_ip = get_local_ip()

    #
    #   I need to have a default in case everything else fails!
    #
    ifname = 'eth0'

    if os.name == "nt":
        #
        #   TODO: Find out how to do this in Windows!
        #
        pass
    else:
        #
        #   Linux
        #
        import fcntl
        import struct

        interfaces = [b"eth0", b"eth1", b"eth2", b"wlan0", b"wlan1",
                      b"wifi0", b"ath0", b"ath1", b"ppp0"]
        for ifname in interfaces:
            s = None
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                interface_ip = socket.inet_ntoa(fcntl.ioctl(s.fileno(),
                    0x8915,  # SIOCGIFADDR
                    struct.pack('256s', ifname[:15])
                )[20:24])
            except IOError:
                pass
            else:
                # closing opened socket
                s.close()
                if internet_ip == interface_ip:
                    break
            finally:
                if s:
                    s.close()

    return ifname
