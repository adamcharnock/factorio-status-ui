#!/usr/bin/python

import asyncio
import socket
import struct
import sys

import logging

from factorio_status_ui.state import application_config

MESSAGE_TYPE_AUTH = 3
MESSAGE_TYPE_AUTH_RESP = 2
MESSAGE_TYPE_COMMAND = 2
MESSAGE_TYPE_RESP = 0
MESSAGE_ID = 0

logger = logging.getLogger(__name__)


class RconConnectionError(Exception): pass
class RconTimeoutError(Exception): pass
class RconAuthenticatedFailed(Exception): pass


async def send_message(writer, command_string, message_type):
    """Packages up a command string into a message and sends it"""
    logger.debug('Send message to RCON server: {}'.format(command_string))

    try:
        # size of message in bytes:
        # id=4 + type=4 + body=variable + null terminator=2 (1 for python string and 1 for message terminator)
        message_size = (4 + 4 + len(command_string) + 2)
        message_format = ''.join(['=lll', str(len(command_string)), 's2s'])
        packed_message = struct.pack(
            message_format, message_size, MESSAGE_ID, message_type, command_string.encode('utf8'), b'\x00\x00'
        )
        writer.write(packed_message)
        response_data = await asyncio.wait_for(
            writer.drain(),
            timeout=application_config.rcon_timeout
        )

    except asyncio.TimeoutError:
        raise RconTimeoutError('Timeout sending RCON message. type={}, command={}'.format(message_type, command_string))


async def get_response(reader):
    """Gets the message response to a sent command and unpackages it"""
    response_id = -1
    response_type = -1
    try:
        response_size, = struct.unpack('=l', await reader.read(4))
        message_format = ''.join(['=ll', str(response_size - 9), 's1s'])

        response_data = await asyncio.wait_for(
            reader.read(response_size),
            timeout=application_config.rcon_timeout
        )
        response_id, response_type, response_string, response_dummy \
            = struct.unpack(message_format, response_data)
        response_string = response_string.rstrip(b'\x00\n')
        return response_string, response_id, response_type

    except asyncio.TimeoutError:
        raise RconTimeoutError('Timeout receiving RCON response')


class RconConnection():

    async def __aenter__(self):
        logger.debug('Authenticating with RCON server {}:{} using password "{}"'.format(
            application_config.rcon_host,
            application_config.rcon_port,
            application_config.rcon_password,
        ))

        try:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(application_config.rcon_host, application_config.rcon_port),
                timeout=application_config.rcon_timeout
            )
        except asyncio.TimeoutError:
            raise RconTimeoutError('Timeout connecting to RCON server {}:{}'.format(
                application_config.rcon_host,
                application_config.rcon_port
            ))
        except ConnectionRefusedError:
            raise RconConnectionError('Server {} refused attempted RCON connection on port {}'.format(
                application_config.rcon_host,
                application_config.rcon_port
            ))

        await send_message(self.writer, application_config.rcon_password, MESSAGE_TYPE_AUTH)
        response_string, response_id, response_type = await get_response(self.reader)

        if response_id == -1:
            raise RconAuthenticatedFailed('Failed to authenticate with RCON server {}:{} using password "{}"'.format(
                application_config.rcon_host,
                application_config.rcon_port,
                application_config.rcon_password,
            ))
        else:
            logger.debug('Successfully authenticated with RCON server')

        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.writer.close()

    async def run_command(self, command: str):
        logger.debug('Running RCON command: {}'.format(command))

        await send_message(self.writer, command, MESSAGE_TYPE_COMMAND)
        response_string, response_id, response_type = await get_response(self.reader)

        # See: https://developer.valvesoftware.com/wiki/Source_RCON_Protocol#Multiple-packet_Responses
        # Basically we get an empty packet after each response
        if command.startswith('/config'):
            # ServerConfig commands seem to be multi-packet responses
            await get_response(self.reader)

        return response_string


