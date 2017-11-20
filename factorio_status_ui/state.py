from pathlib import Path
from typing import Tuple, Any


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


class ServerConfig(State):
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
        return '<ServerConfig: {}>'.format(self.__dict__)

    def as_dict(self):
        return self.__dict__


class Server(State):
    description: str
    players: Tuple[Player] = tuple()
    admins: Tuple[Player] = tuple()
    mods: Tuple[Mod] = tuple()
    mod_settings: dict = {}
    all_mods_file: Path
    config: ServerConfig = ServerConfig()


class ApplicationConfig(State):
    host: str = None
    port: int = None

    rcon_host: str = None
    rcon_port: int = None
    rcon_password: str = None
    rcon_timeout: int = None

    mods_directory: Path = None
    saves_directory: Path = None

    server_name: str = None
    server_host: str = None
    server_port: int = None

    def __repr__(self):
        return '<ApplicationConfig: {}>'.format(self.__dict__)


server = Server()
mod_database = {}
application_config = ApplicationConfig()
