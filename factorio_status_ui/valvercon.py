import valve.rcon

server_address = ("127.0.0.1", 27015)
password = "2a025f3147010960"

with valve.rcon.RCON(server_address, password) as rcon:
    print(rcon("help"))
