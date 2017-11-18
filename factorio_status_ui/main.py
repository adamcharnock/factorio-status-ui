#!/usr/bin/python

# This is an RCON client for games using the Source RCON protocol.
# Pass a RCON command via argument (or don't to use interactive mode)

# Copyright 2015 Dunto, see below for license information.
# This script was written as a quick solution to a personal requirement,
# it may or may not be improved on as time passes.  I make no promises
# as to whether it will work properly for you or not.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>


import socket
import struct
import sys

# START USER EDITABLE SECTION
RCON_SERVER_HOSTNAME = '127.0.0.1'
RCON_SERVER_PORT = 27015
RCON_PASSWORD = '2a025f3147010960'
RCON_SERVER_TIMEOUT = 1  # server response timeout in seconds, don't go too high
# END USER EDITABLE SECTION


MESSAGE_TYPE_AUTH = 3
MESSAGE_TYPE_AUTH_RESP = 2
MESSAGE_TYPE_COMMAND = 2
MESSAGE_TYPE_RESP = 0
MESSAGE_ID = 0


def send_message(sock, command_string, message_type):
    """Packages up a command string into a message and sends it"""
    try:
        # size of message in bytes:
        # id=4 + type=4 + body=variable + null terminator=2 (1 for python string and 1 for message terminator)
        message_size = (4 + 4 + len(command_string) + 2)
        message_format = ''.join(['=lll', str(len(command_string)), 's2s'])
        packed_message = struct.pack(
            message_format, message_size, MESSAGE_ID, message_type, command_string.encode('utf8'), b'\x00\x00'
        )
        sock.sendall(packed_message)
    except socket.timeout:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()
 
 
def get_response(sock):
    """Gets the message response to a sent command and unpackages it"""
    response_id = -1
    response_type = -1
    try:
        response_size, = struct.unpack('=l', sock.recv(4))
        message_format = ''.join(['=ll', str(response_size-9), 's1s'])

        response_id, response_type, response_string, response_dummy \
            = struct.unpack(message_format, sock.recv(response_size))

        if (response_string is None or response_string is str(b'\x00')) and response_id is not 2:
            response_string = "(Empty Response)"

        return response_string, response_id, response_type

    except socket.timeout:
        response_string = "(Connection Timeout)"
        return response_string, response_id, response_type
 
 
# begin main loop
def main():
    if len(sys.argv) > 1:
        command_string = " ".join(sys.argv[1:])
        interactive_mode = False
    else:
        command_string = input("Command: ")

    sock = socket.create_connection((RCON_SERVER_HOSTNAME,RCON_SERVER_PORT))
    sock.settimeout(RCON_SERVER_TIMEOUT)

    # send SERVERDATA_AUTH
    print("Authenticating")
    send_message(sock, RCON_PASSWORD, MESSAGE_TYPE_AUTH)

    # get SERVERDATA_AUTH_RESPONSE (auth response 2 of 2)
    response_string,response_id,response_type = get_response(sock)
    print("Auth response: {}".format(response_string,response_id,response_type))

    print("Running command...")

    # send SERVERDATA_EXECCOMMAND
    send_message(sock, command_string, MESSAGE_TYPE_COMMAND)

    # get SERVERDATA_RESPONSE_VALUE (command response)
    response_string,response_id,response_type = get_response(sock)

    print(response_string, response_id, response_type)
    sock.shutdown(socket.SHUT_RDWR)
    sock.close()
 
if __name__ == '__main__':
    main()


