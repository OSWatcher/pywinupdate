import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from winupdate.ansible import AnsiblePlaybook

DEFAULT_WINRM_PORT = 5985
DEFAULT_USER = 'vagrant'
DEFAULT_PASSWORD = 'vagrant'


@dataclass
class WinUpdateInfo:
    categories: List[str]
    id: str
    installed: bool
    kb: List[str]
    title: str


@dataclass
class WinUpdateModData:
    """Represents the data returned by win_updates Ansible module"""
    changed: bool
    failed: bool
    filtered_updates: Dict
    found_update_count: int
    installed_update_count: int
    reboot_required: bool
    updates: Dict[str, WinUpdateInfo]


class WinUpdate:
    """
    Main class to interact with PyWinUpdate
    """

    def __init__(self, host: str, port: int = DEFAULT_WINRM_PORT, user: str = DEFAULT_USER,
                 password: str = DEFAULT_PASSWORD, debug_lvl: int = 0):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.debug_lvl = debug_lvl
        self.search_playbook = Path(__file__).parent / 'search_wupdates.yml'
        self.apply_playbook = Path(__file__).parent / 'apply_wupdate.yml'

        # setup logging
        log_lvl = logging.INFO
        if debug_lvl > 0:
            log_lvl = logging.DEBUG
        logging.basicConfig(level=log_lvl)

    def _ansible_res_to_python(self, result: Dict) -> WinUpdateModData:
        # convert to dataclasses
        search_res = WinUpdateModData(**result)
        search_res.updates = {up_id: WinUpdateInfo(**up_info) for up_id, up_info in result['updates'].items()}
        return search_res

    def search(self) -> WinUpdateModData:
        """Search for Windows Updates"""
        with AnsiblePlaybook(self.host, self.search_playbook, self.port, self.debug_lvl, self.user,
                             self.password) as ansible:
            ansible.run()
            res = ansible.result
            return self._ansible_res_to_python(res)

    def apply_update(self, up_uuid: str, kb_id: str):
        evars = {
            'kb_id': kb_id,
            # also increase the read timeout, as Windows Updates might break WinRM connection for quite some time
            'ansible_winrm_read_timeout_sec': 60 * 3
        }
        installed = True
        with AnsiblePlaybook(self.host, self.apply_playbook, self.port, self.debug_lvl, self.user, self.password,
                             evars) as ansible:
            ansible.run()
            res = ansible.result
            apply_res = self._ansible_res_to_python(res)
            need_reboot = apply_res.reboot_required
            installed = apply_res.updates[up_uuid].installed
        if need_reboot:
            # wait for guest to be IDLE
            logging.info('Wait for guest to be IDLE after reboot')
            time.sleep(60)
        if not installed:
            raise NotImplementedError

    def run(self):
        wupdates = self.search()
        for up_uuid, up_info in wupdates.updates.items():
            logging.info('Applying update %s', up_info.title)
            kb_id = up_info.kb[0]
            self.apply_update(up_uuid, kb_id)
