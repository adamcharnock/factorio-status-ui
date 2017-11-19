import logging

from aiohttp import web

from factorio_status_ui.web import setup_routes, setup_templates, start_background_tasks, cleanup_background_tasks


def main():
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


if __name__ == '__main__':
    main()
