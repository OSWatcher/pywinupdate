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
import logging
import subprocess
import json
import time
from pprint import pformat
from tempfile import NamedTemporaryFile
from pathlib import Path
from contextlib import AbstractContextManager
from typing import Dict

from docopt import docopt


class AnsiblePlaybook(AbstractContextManager):

    def __init__(self, host: str, playbook: Path, port=5985, verbose_lvl=0, user='vagrant', password='vagrant',
                 extra_vars: Dict[str, str] = None):
        self._cmd = ['ansible-playbook']
        # host
        self._cmd.extend(['--inventory', f'{host},'])
        # connection
        self._cmd.extend(['--connection', 'winrm'])
        # extra vars
        evars = {
            'ansible_user': user,
            'ansible_password': password,
            'ansible_port': port,
            'ansible_winrm_scheme': 'http'
        }
        if extra_vars:
            evars.update(extra_vars)
        for var, value in evars.items():
            self._cmd.extend(['--extra-vars', f'{var}={value}'])
        # verbosity (-vvv..)
        if verbose_lvl:
            self._cmd.append(f"-{''.join(['v' for i in range(verbose_lvl)])}")
        # playbook
        self._cmd.append(str(playbook))
        self.result = None

    def __enter__(self):
        self.tempfile = NamedTemporaryFile()
        # pass additional tempfile as extravar
        self._cmd.insert(-1, '--extra-vars')
        self._cmd.insert(-1, f'output_file={self.tempfile.name}')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.tempfile.close()

    def run(self):
        logging.debug(self._cmd)
        subprocess.check_call(self._cmd)
        # load output file
        with open(self.tempfile.name) as f:
            self.result = json.load(f)


def main(args):
    host = args['<host>']
    port = int(args['--port'])
    debug_lvl = int(args['--debug'])
    user = args['--user']
    password = args['--password']

    # setup logging
    log_lvl = logging.INFO
    if debug_lvl > 0:
        log_lvl = logging.DEBUG
    logging.basicConfig(level=log_lvl)

    search_playbook = Path('search_wupdates.yml')
    with AnsiblePlaybook(host, search_playbook, port, debug_lvl, user, password) as ansible:
        ansible.run()
        wupdates = ansible.result
    # display updates
    logging.debug('Updates: %s', pformat(wupdates))
    # for each update
    apply_playbook = Path('apply_wupdate.yml')
    for up_id, up_info in wupdates['updates'].items():
        logging.info('Applying update %s', up_info['title'])
        evars = {
            'kb_id': up_info['kb'][0],
            # also increase the read timeout, as Windows Updates might break WinRM connection for quite some time
            'ansible_winrm_read_timeout_sec': 60 * 3
        }
        installed = True
        with AnsiblePlaybook(host, apply_playbook, port, debug_lvl, user, password, evars) as ansible:
            ansible.run()
            res = ansible.result
            logging.debug(pformat(res))
            need_reboot = res['reboot_required']
            installed = res['updates'][up_id]['installed']
        if need_reboot:
            # wait for guest to be IDLE
            logging.info('Wait for guest to be IDLE after reboot')
            time.sleep(60)
        if not installed:
            raise NotImplemented()



if __name__ == '__main__':
    args = docopt(__doc__)
    ret = main(args)
    if ret is None:
        ret = 0
    sys.exit(ret)
