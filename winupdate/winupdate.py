import logging
import time
from pathlib import Path
from pprint import pformat

from winupdate.ansible import AnsiblePlaybook

DEFAULT_WINRM_PORT = 5985
DEFAULT_USER = 'vagrant'
DEFAULT_PASSWORD = 'vagrant'


def apply_winupdates(host: str, port: int = DEFAULT_WINRM_PORT, user: str = DEFAULT_USER,
                     password: str = DEFAULT_PASSWORD, debug_lvl: int = 0):
    """
    Main entrypoint for libraries
    """
    # setup logging
    log_lvl = logging.INFO
    if debug_lvl > 0:
        log_lvl = logging.DEBUG
    logging.basicConfig(level=log_lvl)

    search_playbook = Path(__file__).parent / 'search_wupdates.yml'
    with AnsiblePlaybook(host, search_playbook, port, debug_lvl, user, password) as ansible:
        ansible.run()
        wupdates = ansible.result
    # display updates
    logging.debug('Updates: %s', pformat(wupdates))
    # for each update
    apply_playbook = Path(__file__).parent / 'apply_wupdate.yml'
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
            raise NotImplementedError
