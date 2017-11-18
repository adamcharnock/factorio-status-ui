import asyncio
import os

import aiohttp_jinja2
import jinja2
from aiohttp import web
from pathlib import Path

from factorio_status_ui import handlers, config
from factorio_status_ui.rcon import RconConnection
from factorio_status_ui.state import server

ROOT_DIR = Path(__file__).parent.parent


class IndexView(web.View):
    async def get(self):
        return aiohttp_jinja2.render_template(
            'index.jinja2',
            self.request,
            {
                'server': server
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
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(str(ROOT_DIR / 'templates')))


async def poll_coroutine(coroutine, handler, interval=1):
    previous_value = None
    while True:
        try:
            value = await coroutine()
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


async def get_mods():
    with open(config.MODS_DIR / 'mod-list.json') as f:
        return f.read(), list(config.MODS_DIR.glob('*.zip'))


async def start_background_tasks(app):
    app['monitor_players'] = app.loop.create_task(poll_rcon('/players', handlers.handle_players))
    app['monitor_admins'] = app.loop.create_task(poll_rcon('/admins', handlers.handle_admins))
    app['monitor_mods'] = app.loop.create_task(poll_coroutine(get_mods, handlers.handle_mods))
    app['monitor_config'] = app.loop.create_task(poll_config(handlers.handle_config))


async def cleanup_background_tasks(app):
    app['monitor_players'].cancel()
    app['monitor_admins'].cancel()
    app['monitor_mods'].cancel()
    app['monitor_config'].cancel()
    await app['monitor_players']
    await app['monitor_admins']
    # await app['monitor_mods']
    await app['monitor_config']


if __name__ == '__main__':
    app = web.Application()
    setup_routes(app)
    setup_templates(app)
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    web.run_app(app, host='127.0.0.1', port=8080)
