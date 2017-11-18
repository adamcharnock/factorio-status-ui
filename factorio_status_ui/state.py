
class User(object):
    username: str
    is_admin: bool = False
    is_online: bool = True


class Server(object):
    name: str
    description: str
    users: list[User]


server = Server()
