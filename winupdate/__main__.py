#!/usr/bin/env python3

"""
Usage: winupdates.py [options] <host>

Options:
    -h --help                           Display this message
    -d DEBUG_LVL --debug DEBUG_LVL      Enable debug output [Default: 0]
    -p PORT --port PORT                 WinRM port [Default: 5985]
    -u USER --user USER                 Ansible user [Default: vagrant]
    -p PASS --password PASS             Ansible password [Default: vagrant]
"""

import sys

from docopt import docopt

from winupdate.winupdate import WinUpdate


def main_cmdline(args):
    """
    Main entrypoint for docopt
    """
    host = args['<host>']
    port = int(args['--port'])
    debug_lvl = int(args['--debug'])
    user = args['--user']
    password = args['--password']

    winupdate = WinUpdate(host, port=port, user=user, password=password, debug_lvl=debug_lvl)
    return winupdate.run()


def main():
    """
    Main entrypoint for setup.py console script
    """
    args = docopt(__doc__)
    ret = main_cmdline(args)
    if ret is None:
        ret = 0
    sys.exit(ret)


main()
