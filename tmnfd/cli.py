import os
import sys
import argparse
from helpers.settings import DedicatedCfg, MatchSettings
from glob import glob
from datetime import datetime
import json
import subprocess
os.chdir(os.path.dirname(os.path.realpath(__file__)))

parser = argparse.ArgumentParser(description='TMNFD CLI')
parser.add_argument('--test', dest='test', action='store_true', default=False, help='Used for testing if tmnfd-cli is available')
parser.add_argument('--init', dest='init', action='store_true', default=False, help='Initialize Configuration')
parser.add_argument('--prepare-start', dest='prepare_start', action='store_true', help='Prepares everything for tmnfd to be started')
parser.add_argument('--upload_replay', dest='upload_replay', default=None, help='Uploads specified replay file to S3 storage')
parser.add_argument('--generate_thumbnails', dest='generate_thumbnails', action='store_true', help='Generates thumbnails and uploads them to S3 storage')
parser.add_argument('--upload_challenges', dest='upload_challenges', action='store_true', help='Uploads challenges files of active machsetting to S3 storage')
parser.add_argument('--create_backup', dest='create_backup', action='store_true', help='Creates backup of tmnfd config and stores it to S3')
parser.add_argument('--restore_backup', dest='restore_backup', action='store_true', help='Restores backup of tmnfd config from S3')
args = parser.parse_args()


def init_config(force=True):
    from helpers.config import get_config, save_config
    config = get_config()
    if force or not config.get('init', False):
        cfg = DedicatedCfg()
        cfg.set_name('TMNF-TAS')
        cfg.set_xmlrpc()
        cfg.set_laddermode()
        cfg.save()
        ms = MatchSettings(config['active_matchsetting'])
        ms.save(activate=True)
        config['init'] = True
        save_config(config)


def write_active():
    from helpers.config import get_config
    ms = MatchSettings(get_config()['active_matchsetting'])
    ms.save(activate=True)


def list_challenges():
    from pygbx import Gbx, GbxType
    from helpers.config import get_config
    path = os.path.normpath(get_config()['challenges_path']) + '/'
    for f in \
            glob(os.path.join(path, 'Campaigns', 'Nations', '**', '*.Challenge.Gbx'), recursive=True) + \
            glob(os.path.join(path, 'Challenges', '**', '*.Challenge.Gbx'), recursive=True):
        g = Gbx(f)
        challenge = g.get_class_by_id(GbxType.CHALLENGE)
        if not challenge:
            continue
        print(f"{challenge.map_name} {f.replace(path, '')} {challenge.map_uid}")


def generate_thumbnails(interactive=True):
    from helpers.config import get_config
    from helpers.thumbnails import extract_thumbnail
    from helpers.s3 import exists_thumbnail, upload_thumbnail
    config = get_config()
    ms = MatchSettings(config['active_matchsetting'])
    cpath = get_config()['challenges_path']
    for ident, path in ms.get_challenges():
        if not exists_thumbnail(ident):
            challenge_file = os.path.join(cpath, path.replace('\\', '/'))
            extract_thumbnail(challenge_file, '/tmp/thumbnail.jpg')
            upload_thumbnail('/tmp/thumbnail.jpg', ident)
            if interactive:
                print(f'Extracted thumbnail from {challenge_file}')
        elif interactive:
            print(f'Thumbnail {ident}.jpg exists')


def upload_challenges(interactive=True):
    from helpers.config import get_config
    from helpers.s3 import exists_challenge, upload_challenge
    config = get_config()
    ms = MatchSettings(config['active_matchsetting'])
    for ident, cpath in ms.get_challenges():
        cpath = os.path.join(config['challenges_path'], cpath.replace('\\', '/'))
        if not exists_challenge(ident):
            upload_challenge(cpath, ident)
            if interactive:
                print(f'Uploaded: {cpath}')
        elif interactive:
            print(f'Allready exists: {cpath}')


def exit():
    sys.exit(0)


def upload_replay(replay):
    from helpers.s3 import upload_replay as s3_upload_replay
    from helpers.config import get_config
    replay_path = os.path.join(get_config()['replays_path'], replay)
    if not replay_path.endswith('.Replay.Gbx'):
        replay_path = replay_path + '.Replay.Gbx'
    s3_upload_replay(replay_path, replay)


def create_backup(s3=False):
    import zipfile
    from helpers.config import get_config
    from helpers.s3 import botoClient, upload_generic
    if s3:
        path = '/tmp'
    else:
        path = input('Where do you like to store the backup?: ')
        if not os.path.isdir(path):
            print(f'{path} is not a valid directory!')
            return
    dt = datetime.now()
    backup_name = 'tmnfd_backup_' + dt.strftime('%Y%m%d%M%H%S') + '.zip'
    backup_file = os.path.join(path, backup_name)
    config = get_config()
    metadata = dict({
        'ts': int(dt.timestamp()),
        'MatchSettings': 0,
        'Challenges': 0
    })

    with zipfile.ZipFile(backup_file, mode='w') as zf:
        with zf.open('config.json', 'w') as f:
            f.write(json.dumps(config, indent=2).encode('utf-8'))
        with zf.open('dedicated_cfg.txt', 'w') as f:
            with open(config['config_path'], 'rb') as inp:
                f.write(inp.read())
        for ms in glob(os.path.join(config['match_settings'], '*')):
            ms = ms.replace(os.path.normpath(config['match_settings']) + '/', '')
            with zf.open(f'MatchSettings/{ms}', 'w') as f:
                with open(os.path.join(config['match_settings'], ms), 'rb') as inp:
                    f.write(inp.read())
                    metadata['MatchSettings'] += 1
        for chal in \
                glob(os.path.join(config['challenges_path'], 'Campaigns', 'Nations', '**', '*.Challenge.Gbx'), recursive=True) + \
                glob(os.path.join(config['challenges_path'], 'Challenges', '**', '*.Challenge.Gbx'), recursive=True):
            chal = chal.replace(os.path.normpath(config['challenges_path']) + '/', '')
            with zf.open(f'Challenges/{chal}', 'w') as f:
                with open(os.path.join(config['challenges_path'], chal), 'rb') as inp:
                    f.write(inp.read())
                    metadata['Challenges'] += 1
        with zf.open('metadata.json', 'w') as f:
            f.write(json.dumps(metadata, indent=2).encode('utf-8'))

    if s3:
        if 'tmnfd-backups' not in [b['Name'] for b in botoClient.list_buckets()['Buckets']]:
            botoClient.create_bucket(Bucket='tmnfd-backups')
        if upload_generic('tmnfd-backups', backup_file, backup_name, rm_local=True):
            print(f'Backup uploaded to S3 as: {backup_name}')
        else:
            print('Backup upload failed')
    else:
        print(f'Backup written to: {backup_file}')


def restore_backup(s3=False):
    import zipfile
    from helpers.config import get_config, reload_config
    from helpers.s3 import get_generic
    import pathlib
    if s3:
        backup_file = '/tmp/tmnfd_s3_restore_backup.zip'
        with open(backup_file, 'wb') as bf:
            bf.write(get_generic('tmnfd-backups', 'restore.zip').read())
    else:
        backup_file = input('Path to backup-file: ')
        if not os.path.isfile(backup_file):
            print('Invalid file-backup_file!')
            return

    metadata = dict({
        'MatchSettings': 0,
        'Challenges': 0
    })

    with zipfile.ZipFile(backup_file, 'r') as zf:
        with zf.open('metadata.json', 'r') as inp:
            metadata.update(json.load(inp))

        config = get_config()
        subprocess.call(f"rm -rf {config['match_settings']}/*", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        subprocess.call(f"rm -rf {config['challenges_path']}/Campaigns/*", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        subprocess.call(f"rm -rf {config['challenges_path']}/Challenges/*", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        subprocess.call(f"rm -f {config['config_path']}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        with zf.open('config.json', 'r') as inp:
            with open('config.json', 'wb') as out:
                out.write(inp.read())
        reload_config()
        config = get_config()
        subprocess.call(f"rm -rf {config['match_settings']}/*", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        subprocess.call(f"rm -rf {config['challenges_path']}/Campaigns/*", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        subprocess.call(f"rm -rf {config['challenges_path']}/Challenges/*", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        subprocess.call(f"rm -f {config['config_path']}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

        with zf.open('dedicated_cfg.txt', 'r') as inp:
            with open(config['config_path'], 'wb') as out:
                out.write(inp.read())

        if metadata['MatchSettings'] > 0:
            for ms in [ms for ms in zf.namelist() if ms.startswith('MatchSettings/')]:
                file_path = os.path.join(config['match_settings'], ms.lstrip('MatchSettings').lstrip('/'))
                pathlib.Path(os.path.dirname(file_path)).mkdir(parents=True, exist_ok=True)
                with zf.open(ms, 'r') as inp:
                    with open(file_path, 'wb') as out:
                        out.write(inp.read())

        if metadata['Challenges'] > 0:
            for chal in [chal for chal in zf.namelist() if chal.startswith('Challenges/')]:
                file_path = os.path.join(config['challenges_path'], chal.lstrip('Challenges').lstrip('/'))
                pathlib.Path(os.path.dirname(file_path)).mkdir(parents=True, exist_ok=True)
                with zf.open(chal, 'r') as inp:
                    with open(file_path, 'wb') as out:
                        out.write(inp.read())
    if s3:
        subprocess.call(f'rm -f {backup_file}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


commands = [
    ('Force Config Init', init_config),
    ('Write Active MatchSettings', write_active),
    ('List Challenges', list_challenges),
    ('Generate Thumbnails', generate_thumbnails),
    ('Upload Challenges', upload_challenges),
    ('Create Backup', create_backup),
    ('Restore Backup', restore_backup),
    ('Exit', exit)
]

if args.test:
    sys.exit(0)

elif args.init:
    init_config(False)

elif args.prepare_start:
    write_active()

elif args.generate_thumbnails:
    generate_thumbnails(False)

elif args.upload_replay:
    upload_replay(args.upload_replay)

elif args.upload_challenges:
    upload_challenges(False)

elif args.create_backup:
    create_backup(s3=True)

elif args.restore_backup:
    restore_backup(s3=True)

else:
    while True:
        index = 0
        for display, func in commands:
            print(f'{index} {display}')
            index += 1

        selection = int(input('\nSelect: '))
        if selection not in range(0, len(commands)):
            print('Invalid input!')
            sys.exit(1)

        commands[selection][1]()
        print()
