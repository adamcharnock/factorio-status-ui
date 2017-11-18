import asyncio

import aiohttp_jinja2
import jinja2
from aiohttp import web
from pathlib import Path

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


async def test_co(app):
    while True:
        try:
            await asyncio.sleep(1)
        except asyncio.CancelledError:
            return
        print("test_co")


async def start_background_tasks(app):
    app['test_co'] = app.loop.create_task(test_co(app))


async def cleanup_background_tasks(app):
    app['test_co'].cancel()
    await app['test_co']


if __name__ == '__main__':
    app = web.Application()
    setup_routes(app)
    setup_templates(app)
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    web.run_app(app, host='127.0.0.1', port=8080)
