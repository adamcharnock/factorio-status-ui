import json
import re
from pathlib import Path
from typing import Tuple, List

from factorio_status_ui.state import Player, server, Mod


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
        username = admin_line.strip()

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

