from pathlib import Path
from typing import Tuple, Any

import factorio_status_ui.config


class State(object):

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class Player(State):
    username: str
    is_online: bool = False

    def __repr__(self):
        return '<Player: {}, is_online={}>'.format(
            self.username,
            self.is_online,
        )


class Mod(State):
    file: Path
    enabled: bool
    name: str
    version: str

    def __repr__(self):
        return '<Mod: {}, enabled={}, file={}, version={}>'.format(
            self.name,
            self.enabled,
            self.file.name if self.file else None,
            self.version,
        )


class Config(State):
    afk_auto_kick: bool
    allow_commands: str
    autosave_interval: str
    autosave_only_on_server: Any
    ignore_player_limit_for_returning_players: Any
    max_players: Any
    max_upload_speed: Any
    only_admins_can_pause: Any
    password: Any
    require_user_verification: Any
    visibility_lan: Any
    visibility_public: Any

    def __repr__(self):
        return '<Config: {}>'.format(self.__dict__)

    def as_dict(self):
        return self.__dict__


class Server(State):
    name: str = factorio_status_ui.config.SERVER_NAME
    description: str
    players: Tuple[Player] = tuple()
    admins: Tuple[Player] = tuple()
    mods: Tuple[Mod] = tuple()
    all_mods_file: Path
    config: Config = {}
    ip: factorio_status_ui.config.SERVER_IP = None
    port: factorio_status_ui.config.SERVER_PORT = 34197


server = Server()
mod_database = {}
