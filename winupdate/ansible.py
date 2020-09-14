import json
import logging
import subprocess
from contextlib import AbstractContextManager
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict


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
