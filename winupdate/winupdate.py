import logging
import subprocess
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from queue import Queue
from typing import Dict, List

from winupdate.ansible import AnsiblePlaybook

DEFAULT_WINRM_PORT = 5985
DEFAULT_USER = "vagrant"
DEFAULT_PASSWORD = "vagrant"
DEFAULT_MAX_INSTALL_ATTEMPTS = 3


class UpdateNotInstalledError(Exception):
    pass


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
    failed_update_count: int
    filtered_updates: Dict
    found_update_count: int
    installed_update_count: int
    reboot_required: bool
    updates: Dict[str, WinUpdateInfo]


class WinUpdate:
    """
    Main class to interact with PyWinUpdate
    """

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_WINRM_PORT,
        user: str = DEFAULT_USER,
        password: str = DEFAULT_PASSWORD,
        debug_lvl: int = 0,
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.debug_lvl = debug_lvl
        self.debug_enabled = True if self.debug_lvl > 0 else False
        self.search_playbook = Path(__file__).parent / "search_wupdates.yml"
        self.apply_playbook = Path(__file__).parent / "apply_wupdate.yml"
        # represents remaining Windows Updates to apply
        # we use a Queue because some updates might fail, and we put them back in the Queue
        # while applying the rest
        self._rem_updates = Queue()

        # setup logging
        log_lvl = logging.INFO
        if debug_lvl > 0:
            log_lvl = logging.DEBUG
        logging.basicConfig(level=log_lvl)

    def _ansible_res_to_python(self, result: Dict) -> WinUpdateModData:
        """Concert Ansible win_updates Dict result to a Python Dataclass object"""
        # update the dict to have failed_update_count
        # it's not always present
        if "failed_update_count" not in result:
            result["failed_update_count"] = 0
        search_res = WinUpdateModData(**result)
        search_res.updates = {up_id: WinUpdateInfo(**up_info) for up_id, up_info in result["updates"].items()}
        return search_res

    def search(self) -> WinUpdateModData:
        """Search for Windows Updates"""
        with AnsiblePlaybook(
            self.host,
            self.search_playbook,
            self.port,
            self.debug_lvl,
            self.user,
            self.password,
            debug=self.debug_enabled,
        ) as ansible:
            ansible.run()
            res = ansible.result
            return self._ansible_res_to_python(res)

    def apply_update(self, up_uuid: str, kb_id: str):
        evars = {
            "kb_id": kb_id,
            # also increase the read timeout, as Windows Updates might break WinRM connection for quite some time
            "ansible_winrm_read_timeout_sec": 60 * 3,
        }
        installed = False
        with AnsiblePlaybook(
            self.host,
            self.apply_playbook,
            self.port,
            self.debug_lvl,
            self.user,
            self.password,
            evars,
            debug=self.debug_enabled,
        ) as ansible:
            try:
                ansible.run()
            except subprocess.CalledProcessError:
                # Ansible failed
                raise UpdateNotInstalledError
            res = ansible.result
            apply_res = self._ansible_res_to_python(res)
            need_reboot = apply_res.reboot_required
            if apply_res.installed_update_count and apply_res.updates:
                installed = apply_res.updates[up_uuid].installed
            else:
                raise UpdateNotInstalledError
            if len(apply_res.updates) > 1:
                logging.warning(
                    "Multiple updates were installed: %s", [up_info.kb[0] for up_info in apply_res.updates.values()]
                )
        if need_reboot:
            # wait for guest to be IDLE
            logging.info("Wait for guest to be IDLE after reboot")
            time.sleep(60)
        if not installed:
            raise NotImplementedError

    def apply_updates(self, wupdates: WinUpdateModData):
        """All all Windows Updates available"""
        # build a queue
        for up_uuid, up_info in wupdates.updates.items():
            self._rem_updates.put((up_uuid, up_info))

        # this counter keeps track of how many times we attempted to install a given update
        install_counter = Counter()
        update_count = 0
        while not self._rem_updates.empty():
            # pop next update
            up_uuid, up_info = self._rem_updates.get()
            # check attempt counter
            kb_id = up_info.kb[0]
            if install_counter[up_uuid] > DEFAULT_MAX_INSTALL_ATTEMPTS:
                logging.warning("Skipping %s", kb_id)
                continue
            try:
                logging.info("[%s] Applying: [%s]: %s", update_count + 1, kb_id, up_info.title)
                self.apply_update(up_uuid, kb_id)
            except UpdateNotInstalledError:
                logging.warning("Failed to apply update %s", kb_id)
                # put it back in the queue, increase attempt counter
                self._rem_updates.put((up_uuid, up_info))
                # if this fails again, just leave it
                continue
            else:
                update_count += 1
            finally:
                # increase attempt counter
                install_counter[up_uuid] += 1
