#!/usr/bin/python

import asyncio
import socket
import struct
import sys

# START USER EDITABLE SECTION
RCON_SERVER_HOSTNAME = '127.0.0.1'
RCON_SERVER_PORT = 27015
RCON_PASSWORD = 'f23ecf5f7ead5b07'
RCON_SERVER_TIMEOUT = 1  # server response timeout in seconds, don't go too high
# END USER EDITABLE SECTION


MESSAGE_TYPE_AUTH = 3
MESSAGE_TYPE_AUTH_RESP = 2
MESSAGE_TYPE_COMMAND = 2
MESSAGE_TYPE_RESP = 0
MESSAGE_ID = 0


async def send_message(writer, command_string, message_type):
    """Packages up a command string into a message and sends it"""
    try:
        # size of message in bytes:
        # id=4 + type=4 + body=variable + null terminator=2 (1 for python string and 1 for message terminator)
        message_size = (4 + 4 + len(command_string) + 2)
        message_format = ''.join(['=lll', str(len(command_string)), 's2s'])
        packed_message = struct.pack(
            message_format, message_size, MESSAGE_ID, message_type, command_string.encode('utf8'), b'\x00\x00'
        )
        writer.write(packed_message)
        await writer.drain()
    except socket.timeout:
        writer.shutdown(socket.SHUT_RDWR)
        writer.close()


async def get_response(reader):
    """Gets the message response to a sent command and unpackages it"""
    response_id = -1
    response_type = -1
    try:
        response_size, = struct.unpack('=l', await reader.read(4))
        message_format = ''.join(['=ll', str(response_size - 9), 's1s'])

        response_id, response_type, response_string, response_dummy \
            = struct.unpack(message_format, await reader.read(response_size))

        response_string = response_string.rstrip(b'\x00\n')
        return response_string, response_id, response_type

    except socket.timeout:
        response_string = "(Connection Timeout)"
        return response_string, response_id, response_type


class RconConnection():

    async def __aenter__(self):
        self.reader, self.writer = await asyncio.open_connection(RCON_SERVER_HOSTNAME, RCON_SERVER_PORT)
        await send_message(self.writer, RCON_PASSWORD, MESSAGE_TYPE_AUTH)
        response_string, response_id, response_type = await get_response(self.reader)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.writer.close()

    async def run_command(self, command: str):
        await send_message(self.writer, command, MESSAGE_TYPE_COMMAND)
        response_string, response_id, response_type = await get_response(self.reader)
        return response_string


async def main():
    if len(sys.argv) > 1:
        command_string = " ".join(sys.argv[1:])
    else:
        command_string = input("Command: ")

    reader, writer = await asyncio.open_connection(RCON_SERVER_HOSTNAME, RCON_SERVER_PORT)

    # TODO: Come back to timeouts
    #sock.settimeout(RCON_SERVER_TIMEOUT)

    # send SERVERDATA_AUTH
    print("Authenticating")
    await send_message(writer, RCON_PASSWORD, MESSAGE_TYPE_AUTH)

    # get SERVERDATA_AUTH_RESPONSE (auth response 2 of 2)
    response_string, response_id, response_type = await get_response(reader)
    print("Auth response: {}".format(response_string, response_id, response_type))

    print("Running command...")

    # send SERVERDATA_EXECCOMMAND
    await send_message(writer, command_string, MESSAGE_TYPE_COMMAND)

    # get SERVERDATA_RESPONSE_VALUE (command response)
    response_string, response_id, response_type = await get_response(reader)

    print(response_string, response_id, response_type)
    writer.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    server = loop.run_until_complete(main())


