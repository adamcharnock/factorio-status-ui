import asyncio
import os

import aiohttp_jinja2
import jinja2
import aiohttp
import logging
from aiohttp import web
from pathlib import Path
import async_timeout

from factorio_status_ui import handlers, config
from factorio_status_ui.rcon import RconConnection
from factorio_status_ui.state import server, mod_database

ROOT_DIR = Path(__file__).parent.parent

logger = logging.getLogger(__name__)


class IndexView(web.View):
    async def get(self):
        return aiohttp_jinja2.render_template(
            'index.jinja2',
            self.request,
            {
                'server': server,
                'config': config,
                'get_mod_data': lambda name: (
                    mod_database.get(name, None) or
                    mod_database.get(name.replace(' ', '_'), None) or
                    mod_database.get(name.replace('_', ' '), None) or
                    {})
            }
        )


class ModDownloadView(web.View):
    async def get(self):
        file_name = self.request.match_info['file_name']
        for mod in server.mods:
            if mod.file and mod.file.name == file_name:
                return web.FileResponse(mod.file)
        return web.HTTPNotFound()


def setup_routes(app):
    app.router.add_static('/static', ROOT_DIR / 'static', append_version=True)
    app.router.add_static('/lib', ROOT_DIR / 'node_modules', append_version=True)
    app.router.add_get('/', IndexView)
    app.router.add_get('/mods/download/{file_name}', ModDownloadView)


def setup_templates(app):
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(str(ROOT_DIR / 'templates')), autoescape=True)


async def poll_local_mods(handler, interval=1):
    logger.info('Setting up monitor: Local mods (via filesystem)')
    previous_value = None
    while True:
        try:
            with open(config.MODS_DIR / 'mod-list.json') as f:
                value = f.read(), list(config.MODS_DIR.glob('*.zip'))
            if value != previous_value:
                handler(value)
            previous_value = value
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            return


async def poll_rcon(command, handler, interval=1):
    """More specific version of monitor_coroutine() for rcon commands"""
    async with RconConnection() as rcon:
        previous_value = None
        while True:
            try:
                value = await rcon.run_command(command)
                if value != previous_value:
                    handler(value)
                previous_value = value
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                return


async def poll_config(handler, interval=10):
    """Execute the config command multiple times in order to get all config options"""
    logger.info('Setting up monitor: Server config polling (via RCON)')
    options = ['afk-auto-kick', 'allow-commands', 'autosave-interval', 'autosave-only-on-server',
               'ignore-player-limit-for-returning-players', 'max-players', 'max-upload-speed', 'only-admins-can-pause',
               'password', 'require-user-verification', 'visibility-lan', 'visibility-public']
    async with RconConnection() as rcon:
        previous_config = None
        while True:
            try:
                server_config = {}
                for option in options:
                    server_config[option] = await rcon.run_command('/config get {}'.format(option))

                if server_config != previous_config:
                    handler(server_config)
                previous_config = server_config.copy()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                return


async def poll_mod_database(handler):
    logger.info('Setting up monitor: Mod database polling')
    previous_value = None

    async with aiohttp.ClientSession() as session, async_timeout.timeout(60):
        while True:
            try:
                async with session.get('https://mods.factorio.com/api/mods?page_size=100000') as response:
                    value = await response.json()

                if value != previous_value:
                    handler(value)
                previous_value = value
                await asyncio.sleep(60*60*24)
            except asyncio.CancelledError:
                return


async def determine_ip(handler):
    logger.info('Determining server public IP address')

    with async_timeout.timeout(10):
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.ipify.org?format=json') as response:
                handler((await response.json())['ip'])


async def start_background_tasks(app):
    app['monitor_players'] = app.loop.create_task(poll_rcon('/players', handlers.handle_players))
    app['monitor_admins'] = app.loop.create_task(poll_rcon('/admins', handlers.handle_admins))
    app['monitor_mods'] = app.loop.create_task(poll_local_mods(handlers.handle_mods))
    app['monitor_config'] = app.loop.create_task(poll_config(handlers.handle_config))
    app['determine_ip'] = app.loop.create_task(determine_ip(handlers.handle_ip))
    app['monitor_mod_database'] = app.loop.create_task(poll_mod_database(handlers.handle_mod_database))


async def cleanup_background_tasks(app):
    app['monitor_players'].cancel()
    app['monitor_admins'].cancel()
    app['monitor_mods'].cancel()
    app['monitor_config'].cancel()
    app['determine_ip'].cancel()
    app['monitor_mod_database'].cancel()

    await app['monitor_players']
    await app['monitor_admins']
    # await app['monitor_mods']
    await app['monitor_config']
    await app['determine_ip']
    await app['monitor_mod_database']


if __name__ == '__main__':
    logger = logging.getLogger('factorio_status_ui')
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(msg)s'))
    logger.addHandler(handler)

    app = web.Application()
    setup_routes(app)
    setup_templates(app)
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    web.run_app(app, host='127.0.0.1', port=8080)
