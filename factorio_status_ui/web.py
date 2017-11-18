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


def setup_routes(app):
    app.router.add_static('/static', ROOT_DIR / 'static', append_version=True)
    app.router.add_get('/', IndexView)


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


async def get_mods():
    with open(config.MODS_DIR / 'mod-list.json') as f:
        return f.read(), list(config.MODS_DIR.glob('*.zip'))


async def start_background_tasks(app):
    app['monitor_players'] = app.loop.create_task(poll_rcon('/players', handlers.handle_players))
    app['monitor_admins'] = app.loop.create_task(poll_rcon('/admins', handlers.handle_admins))
    app['monitor_mods'] = app.loop.create_task(poll_coroutine(get_mods, handlers.handle_mods))


async def cleanup_background_tasks(app):
    app['monitor_players'].cancel()
    app['monitor_admins'].cancel()
    app['monitor_mods'].cancel()
    await app['monitor_players']
    await app['monitor_admins']
    # await app['monitor_mods']


if __name__ == '__main__':
    app = web.Application()
    setup_routes(app)
    setup_templates(app)
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    web.run_app(app, host='127.0.0.1', port=8080)
