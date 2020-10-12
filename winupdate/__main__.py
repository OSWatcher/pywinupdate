#!/usr/bin/env python3

"""
Search and Install Windows Updates

Usage:
    winupdates.py [options] search <host>
    winupdates.py [options] update <host>

Options:
    -h --help                           Display this message
    -d DEBUG_LVL --debug DEBUG_LVL      Enable debug output [Default: 0]
    -p PORT --port PORT                 WinRM port [Default: 5985]
    -u USER --user USER                 Ansible user [Default: vagrant]
    -p PASS --password PASS             Ansible password [Default: vagrant]
    -o --one                            Install only one update
"""

import logging
import sys
from typing import List

from docopt import docopt

from winupdate.winupdate import WinUpdate, WinUpdateInfo


def main_cmdline(args):
    """
    Main entrypoint for docopt
    """
    search = args["search"]
    update = args["update"]
    host = args["<host>"]
    port = int(args["--port"])
    debug_lvl = int(args["--debug"])
    user = args["--user"]
    password = args["--password"]
    one = args["--one"]

    winupdate = WinUpdate(host, port=port, user=user, password=password, debug_lvl=debug_lvl)
    if search:
        # search for updates:
        logging.info("Searching for available Windows Updates...")
        wupdates: List[WinUpdateInfo] = list(winupdate.search())
        logging.info("Found %s updates", len(wupdates))
        for up_info in wupdates:
            logging.info("\t%s: %s", up_info.kb[0], up_info.title)
        return 0
    if update:
        logging.info("Applying updates")
        for index, (up_info, applied) in enumerate(winupdate.update_windows(only_next=one, search_again=True)):
            if applied:
                kb_id = up_info.kb[0]
                logging.info("[%s] Applied: [%s] %s", index + 1, kb_id, up_info.title)
        return 0
    return 0


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
