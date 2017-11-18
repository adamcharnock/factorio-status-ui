from factorio_status_ui.state import Player, server


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
