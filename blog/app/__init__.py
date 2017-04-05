# -*- coding: utf-8 -*-
import os
import logging
import json
import jinja2
import aiohttp_jinja2
from os import environ as env

from datetime import datetime
from tinydb.storages import MemoryStorage
from tinydb import TinyDB
from aiohttp import web
from .app import json_response
from .views import (
    handle_index, handle_page, handle_contact, handle_contact_form,
    handle_about, handle_blog_post, handle_blog_post_comment
)


async def connect_tinydb_db(app):
    if app['config'].memory_db:
        app.db = TinyDB(storage=MemoryStorage)
    else:
        db_name = app['config'].db_name
        app.db = TinyDB(db_name)

    return app.db


async def disconnect_tinydb_db(app):
    pass


async def on_startup(app):
    await connect_tinydb_db(app)


async def on_shutdown(app):
    await disconnect_tinydb_db(app)


def setup_routers(app):
    app.router.add_get('/', handle_index)
    app.router.add_get('/page/{page:\d+}', handle_page)
    app.router.add_get('/contact', handle_contact)
    app.router.add_post('/contact', handle_contact_form)
    app.router.add_get('/about', handle_about)
    app.router.add_get('/post/{slug}', handle_blog_post)
    app.router.add_post('/comment', handle_blog_post_comment)


class BaseConfig(object):
    @classmethod
    def setup(cls, app):
        app['config'] = cls

    db_name = env.get('TINYDB_DB_NAME', 'tinydb.json')
    memory_db = False


class MainConfig(BaseConfig):
    test = False
    debug = False


class TestConfig(BaseConfig):
    test = True
    debug = True
    memory_db = True


logger = logging.getLogger(__name__)


# temporary fix, waiting for asyncio_jinja2 patch
def render_template(template_name, request, context, *,
                    app_key=aiohttp_jinja2.APP_KEY, encoding='utf-8',
                    status=200):
    response = web.Response(status=status)
    if context is None:
        context = {}
    text = aiohttp_jinja2.render_string(
        template_name, request, context, app_key=app_key)
    response.content_type = 'text/html'
    response.charset = encoding
    response.text = text
    return response


async def error_middleware_factory(app, handler):
    async def error_middleware(request):
        try:
            return await handler(request)
        except web.HTTPException as ex:
            context = {'error': ex.reason, 'status': ex.status}
            response = render_template(
                'error.jinja2', request, context, status=ex.status)
            return response
        except Exception as ex:
            logger.exception('Internal server error')

            context = {'error': str(ex), 'status': 500}
            response = render_template(
                'error.jinja2', request, context, status=500)
            return response

    return error_middleware


def format_date(x, format_):
    obj = datetime.strptime(x, '%Y-%m-%dT%H:%M:%S')
    return datetime.strftime(obj, format_)


def create(loop, conf=None):
    if conf is None:
        conf = MainConfig

    app = web.Application(
        loop=loop, middlewares=[error_middleware_factory], debug=conf.debug)
    app.config = conf
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    static_path = os.path.join(
        os.path.dirname(__file__), '..', 'static')
    app.router.add_static('/static', static_path)

    templates_path = os.path.join(
        os.path.dirname(__file__), '..', 'templates')
    aiohttp_jinja2.setup(
        app, loader=jinja2.FileSystemLoader(templates_path), filters={
            'format_date': format_date
        })

    conf.setup(app)
    setup_routers(app)

    return app
