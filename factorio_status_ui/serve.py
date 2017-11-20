import argparse
import logging
import signal
import sys
from pathlib import Path

from aiohttp import web

from factorio_status_ui.state import application_config
from factorio_status_ui.web import setup_routes, setup_templates, start_background_tasks, cleanup_background_tasks, \
    get_version


def main():
    print(sys.argv)

    # Logging
    logger = logging.getLogger('factorio_status_ui')
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(msg)s'))
    logger.addHandler(handler)

    # Arguments
    parser = argparse.ArgumentParser(
        description='Factorio status UI',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    required = parser.add_argument_group('required arguments')

    parser.add_argument('--port', help='The port on which to serve the status page.', type=int, default=8080)
    parser.add_argument('--host', help='The IP on which to serve the status page.', default='0.0.0.0')

    parser.add_argument('--server-name', help='Server name. For display purposes only.', default='Factorio Server')
    parser.add_argument('--server-host', help='Factorio server IP address. For display purposes only. '
                                              'Will attempt to autodetect.')
    parser.add_argument('--server-port', help='Factorio server port. For display purposes only.', default=34197)

    required.add_argument('--rcon-host', help='RCON host address.', required=True)
    required.add_argument('--rcon-port', help='RCON port.', type=int, required=True, default=27015)
    required.add_argument('--rcon-password', help='RCON password.', required=True)
    parser.add_argument('--rcon-timeout', help='RCON timeout in seconds.', default=1, type=int)

    required.add_argument('--mods-directory', help='Path to factorio mods directory.', type=Path, required=True)
    required.add_argument('--saves-directory', help='Path to factorio saves directory.', type=Path, required=True)

    args = parser.parse_args()
    for option in dir(application_config):
        if option.startswith('_'):
            continue
        setattr(application_config, option, getattr(args, option))

    logger.info('Starting up')
    logger.info('Arguments: {}'.format(args.__dict__))

    # App
    app = web.Application()
    setup_routes(app)
    setup_templates(app)
    app.on_startup.append(start_background_tasks)
    app.on_startup.append(get_version)
    app.on_cleanup.append(cleanup_background_tasks)
    web.run_app(app, host=application_config.host, port=application_config.port)


if __name__ == '__main__':
    main()
