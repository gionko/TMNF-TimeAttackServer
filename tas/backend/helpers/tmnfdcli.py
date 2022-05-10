from helpers.mongodb import set_tmnfd_cli_method, get_tmnfd_cli_method, set_provide_replays, set_provide_thumbnails
from helpers.config import get_config
import subprocess

config = get_config('tmnf-server')


def tmnfd_cli_test():
    global config
    r = subprocess.call('tmnfd --test', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    if int(r) == 0:
        set_tmnfd_cli_method('bash')
        return 'bash'
    r = subprocess.call(f"ssh -o ConnectTimeout=3 root@{config['host']} tmnfd --test", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    if int(r) == 0:
        set_tmnfd_cli_method('ssh')
        return 'ssh'
    else:
        set_tmnfd_cli_method(None)
        print('TMNF - Dedicated CLI is not reachable!')
        set_provide_replays(False)
        print('  Disableing replay-provider')
        set_provide_thumbnails(False)
        print('  Disableing thumbnail-provider')
        return None


def tmnfd_cli_upload_replay(name):
    global config
    cli_method = get_tmnfd_cli_method()
    if cli_method == 'bash':
        return int(subprocess.call(f'tmnfd --upload_replay {name}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)) == 0
    if cli_method == 'ssh':
        return int(subprocess.call(
            f"ssh root@{config['host']} tmnfd --upload_replay {name}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)) == 0
    return False


def tmnfd_cli_generate_thumbnails():
    global config
    cli_method = get_tmnfd_cli_method()
    if cli_method == 'bash':
        return int(subprocess.call('tmnfd --generate_thumbnails', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)) == 0
    if cli_method == 'ssh':
        return int(subprocess.call(
            f"ssh root@{config['host']} tmnfd --generate_thumbnails", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)) == 0
    return False
