import json
import re
from pathlib import Path
from typing import Tuple, List

from factorio_status_ui.state import Player, server, mod_database, Mod, Config


def handle_players(player_data: str):
    player_data = player_data.decode('utf8')

    players = []
    for player_line in player_data.split('\n')[1:]:
        username, *extra = player_line.strip().split(' ', 1)

        players.append(Player(
            username=username,
            is_online='(online)' in extra
        ))

    print('Players:', repr(players))
    server.players = tuple(players)


def handle_admins(admin_data: str):
    admin_data = admin_data.decode('utf8')

    admins = []
    for admin_line in admin_data.split('\n'):
        username, *extra = admin_line.strip().split(' ', 1)

        admin = None
        for player in server.players:
            if player.username == username:
                admin = player

        if not admin:
            admin = Player(username=username)

        admins.append(admin)

    print('Admins:', repr(admins))
    server.admins = tuple(admins)


def handle_mods(mods_and_files: Tuple[str, List[Path]]):
    mods_json, files = mods_and_files
    mod_data = json.loads(mods_json)['mods']

    parsed_files = []
    files_by_name = {}
    for file in files:
        matches = re.match(r'(.*)_([0-9\.]*[0-9])\.zip', file.name)
        if matches:
            mod_name, version = matches.groups()
            mod_name = mod_name.replace('_', ' ')
            parsed_files.append((mod_name, version, file))
            files_by_name[mod_name] = (version, file)

    mods = []
    for mod in mod_data:
        name = mod['name'].replace('_', ' ')
        if name in files_by_name:
            version, file = files_by_name[name]
        else:
            version, file = None, None

        mods.append(Mod(
            name=name,
            enabled=mod['enabled'],
            version=version,
            file=file,
        ))

    print('Mods:', repr(mods))
    server.mods = tuple(mods)


def handle_mod_database(data):
    tmp_database = {}
    for mod in data['results']:
        if 'name' in mod:
            tmp_database[mod['name']] = mod
    if tmp_database:
        mod_database.update(tmp_database)
    print('Mods loaded:', len(mod_database))


def handle_config(config: dict):
    def munge_value(v: str):
        v = v.strip('.')
        if ':' in v:
            v = v.split(':', 1)[-1].strip()

        if v.lower() == 'false':
            return False
        if v.lower() == 'true':
            return True
        if 'disabled' in v:
            return False
        if 'enabled' in v:
            return True
        if 'every' in v:  # Autosave every 10 minutes
            return v.split('every', 1)[-1].strip()
        if v.strip() == "The server currently doesn't have a password":
            return None
        return v

    kwargs = {k.replace('-', '_'): munge_value(v.decode('utf8')) for k, v in config.items()}
    server.config = Config(**kwargs)
    print(server.config)


def handle_ip(ip):
    if not server.ip:
        server.ip = ip
        print(server.ip)
