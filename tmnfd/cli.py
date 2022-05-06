import os
import sys
import argparse
from helpers.settings import DedicatedCfg, MatchSettings
from helpers.thumbnails import extract_thumbnail
from glob import glob
from pygbx import Gbx, GbxType
os.chdir(os.path.dirname(os.path.realpath(__file__)))

parser = argparse.ArgumentParser(description='TMNFD CLI')
parser.add_argument('--test', dest='test', action='store_true', default=False, help='Used for testing if tmnfd-cli is available')
parser.add_argument('--init', dest='init', action='store_true', default=False, help='Initialize Configuration')
parser.add_argument('--prepare-start', dest='prepare_start', action='store_true', help='Prepares everything for tmnfd to be started')
parser.add_argument('--upload_replay', dest='upload_replay', default=None, help='Uploads specified replay file to S3 storage')
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
    from helpers.config import get_config
    path = get_config()['challenges_path']
    path += '' if path.endswith('/') else '/'
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
    config = get_config()
    if config.get('thumbnail_generation_enabled', False):
        ms = MatchSettings(config['active_matchsetting'])
        cpath = get_config()['challenges_path']
        tpath = get_config()['thumbnails_path']
        if not os.path.isdir(tpath):
            os.makedirs(tpath)
        for ident, path in ms.get_challenges():
            challenge_file = os.path.join(cpath, path.replace('\\', '/'))
            thumbnail_file = os.path.join(tpath, f'{ident}.jpg')
            extract_thumbnail(challenge_file, thumbnail_file)
            if interactive:
                print(f'Extracted thumbnail from {challenge_file} to {thumbnail_file}')
    elif interactive:
        print('Thumbnail generation is disabled!')


def toggle_thumbnail_generation():
    from helpers.config import get_config, save_config
    config = get_config()
    enabled = config.get('thumbnail_generation_enabled', False)
    if input(f"generation currently {'enabled' if enabled else 'disabled'}! {'Disable' if enabled else 'Enable'} now? (y/N):") == 'y':
        config['thumbnail_generation_enabled'] = not enabled
        save_config(config)


def exit():
    sys.exit(0)


def upload_replay(replay):
    from helpers.s3 import upload_replay as s3_upload_replay
    from helpers.config import get_config
    replay_path = os.path.join(get_config()['replays_path'], replay)
    if not replay_path.endswith('.Replay.Gbx'):
        replay_path = replay_path + '.Replay.Gbx'
    s3_upload_replay(replay_path, replay)


if args.test:
    sys.exit(0)
elif args.init:
    init_config(False)
elif args.prepare_start:
    write_active()
    generate_thumbnails(False)
elif args.upload_replay:
    upload_replay(args.upload_replay)
else:
    commands = [
        ('Force Config Init', init_config),
        ('Write Active MatchSettings', write_active),
        ('List Challenges', list_challenges),
        ('Generate Thumbnails', generate_thumbnails),
        ('Toggle Thumbnail Generation', toggle_thumbnail_generation),
        ('Exit', exit)
    ]

    index = 0
    for display, func in commands:
        print(f'{index} {display}')
        index += 1

    selection = int(input('\nSelect: '))
    if selection not in range(0, len(commands)):
        print('Invalid input!')
        sys.exit(1)

    commands[selection][1]()
