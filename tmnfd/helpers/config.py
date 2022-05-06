import os
import json


loaded = False
_config = {
    'config_path': 'dedicated/GameData/Config/dedicated_cfg.txt',
    'match_settings': 'dedicated/GameData/Tracks/MatchSettings/TAS',
    'active_path': 'dedicated/GameData/Tracks/MatchSettings/active.txt',
    'challenges_path': 'dedicated/GameData/Tracks',
    'active_matchsetting': 'NationsWhite.txt',
    'thumbnails_path': '/opt/middleware/tmnf-tas/static/thumbnails',
    'thumbnail_generation_enabled': True,
    'replays_path': 'dedicated/GameData/Tracks/Replays',
    's3': {
        'host': 'localhost',
        'port': 9000,
        'access_key': 'tmnftas',
        'access_secret': 'password',
        'bucket_replays': 'tas-replays'
    }
}


def get_config():
    global loaded
    if not loaded:
        loaded = True
        if os.path.isfile('config.json'):
            with open('config.json', 'r') as f:
                _config.update(json.loads(f.read()))
        else:
            save_config(_config)
    return _config


def save_config(config):
    _config = config
    with open('config.json', 'w') as f:
        f.write(json.dumps(_config, indent=4))
