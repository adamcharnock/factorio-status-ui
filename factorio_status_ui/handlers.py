import json
import re
import tempfile
from pathlib import Path
from typing import Tuple, List

import logging
from zipfile import ZipFile

from datetime import datetime

from factorio_status_ui.state import Player, server, mod_database, Mod, ServerConfig, application_config

logger = logging.getLogger(__name__)


def handle_players(player_data: str):
    player_data = player_data.decode('utf8')

    players = []
    for player_line in player_data.split('\n')[1:]:
        username, *extra = player_line.strip().split(' ', 1)

        players.append(Player(
            username=username,
            is_online='(online)' in extra
        ))

    server.players = tuple(players)
    logger.info('Players changed: {}'.format(players))


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

    server.admins = tuple(admins)
    logger.info('Admins changed: {}'.format(admins))


def handle_mods(mods_json, mod_settings_json, files):
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

    server.mods = tuple(mods)
    logger.info('Mods changed: {}'.format(', '.join(m.name for m in mods if m.enabled)))
    logger.info('Mods changed (disabled): {}'.format(', '.join(m.name for m in mods if not m.enabled)))

    refresh_all_mods_file()


def refresh_all_mods_file():
    # TODO: This is blocking, perhaps put it in a different executor
    logger.info('Refreshing all mods zip file')
    all_mods_dir = Path(tempfile.gettempdir()) / 'factorio-status-ui'
    all_mods_dir.mkdir(exist_ok=True)
    tmp_zip_path = all_mods_dir / 'tmp.zip'
    with ZipFile(tmp_zip_path, mode='w') as tmp_zip:
        for mod in server.mods:
            if mod.file and mod.enabled:
                tmp_zip.write(mod.file, arcname=Path('mods') / mod.file.name)

        extras = [
            application_config.mods_directory / 'mod-list.json',
            application_config.mods_directory / 'mod-settings.json',
        ]
        for extra in extras:
            if extra.exists():
                tmp_zip.write(extra, arcname=Path('mods') / extra.name)

    all_mods_file = all_mods_dir / 'all-mods-{}.zip'.format(datetime.now().strftime('%Y-%m-%d_%H-%m-%S'))
    tmp_zip_path.rename(all_mods_file)
    server.all_mods_file = all_mods_file
    logger.info('Written all mods zip file to {}'.format(all_mods_file))


def handle_mod_database(data):
    tmp_database = {}
    for mod in data['results']:
        if 'name' in mod:
            tmp_database[mod['name']] = mod
    if tmp_database:
        mod_database.update(tmp_database)
    logger.info('Mod database changed. {} mods found.'.format(len(mod_database)))


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
    server.config = ServerConfig(**kwargs)
    logger.info('Server config changed: {}'.format(server.config))


def handle_ip(ip):
    if not application_config.server_host:
        application_config.server_host = ip
        logger.info('Server IP set: {}'.format(application_config.server_host))
