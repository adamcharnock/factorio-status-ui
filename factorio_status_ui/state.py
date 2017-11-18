from typing import Tuple


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


class Server(State):
    name: str
    description: str
    players: Tuple[Player] = tuple()
    admins: Tuple[Player] = tuple()


server = Server()
