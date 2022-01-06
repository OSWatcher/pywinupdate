import json
import logging
import subprocess
from contextlib import AbstractContextManager
from enum import Enum
from pathlib import Path
from pprint import pformat
from tempfile import NamedTemporaryFile
from typing import Dict, Union

# increase default winrm timeout
ANSIBLE_WINRM_TIMEOUT = 90


class WinUpdateCmd(Enum):
    SEARCH = 1
    UPDATE = 2


class WinUpdatePlaybook(AbstractContextManager):
    def __init__(
        self,
        host: str,
        command: WinUpdateCmd,
        playbook: Path = Path(__file__).parent / "playbook.yml",
        port=5985,
        verbose_lvl=0,
        user="vagrant",
        password="vagrant",
        extra_vars: Dict[str, Union[str, int]] = None,
        debug: bool = False,
    ):
        self._debug = debug
        self._cmd = ["ansible-playbook"]
        # host
        self._cmd.extend(["--inventory", f"{host},"])
        # connection
        self._cmd.extend(["--connection", "winrm"])
        # tag
        self._cmd.extend(["--tags", command.name.lower()])
        # extra vars
        evars = {
            "ansible_user": user,
            "ansible_password": password,
            "ansible_port": port,
            "ansible_winrm_scheme": "http",
            "ansible_winrm_read_timeout_sec": ANSIBLE_WINRM_TIMEOUT
        }
        if extra_vars:
            evars.update(extra_vars)
        for var, value in evars.items():
            self._cmd.extend(["--extra-vars", f"{var}={value}"])
        # verbosity (-vvv..)
        if verbose_lvl:
            self._cmd.append(f"-{''.join(['v' for i in range(verbose_lvl)])}")
        # playbook
        self._cmd.append(str(playbook))
        self.result = None

    def __enter__(self):
        self.tempfile = NamedTemporaryFile()
        # pass additional tempfile as extravar
        self._cmd.insert(-1, "--extra-vars")
        self._cmd.insert(-1, f"output_file={self.tempfile.name}")
        return self

    def run(self):
        logging.debug(self._cmd)
        output_dev = subprocess.DEVNULL
        if self._debug:
            output_dev = None
        subprocess.check_call(self._cmd, stdout=output_dev, stderr=output_dev)
        # load output file

        with open(self.tempfile.name) as f:
            try:
                self.result = json.load(f)
            except json.JSONDecodeError:
                data = f.read()
                logging.warning("Invalid JSON: %s", data)
                raise RuntimeError("Failed to load JSON")
            else:
                logging.debug(pformat(self.result))

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.tempfile.close()
