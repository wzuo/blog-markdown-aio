# -*- coding: utf-8 -*-
import os
import json
import logging
import markdown

from functools import wraps
from math import ceil
from collections import namedtuple
from aiohttp import web
from aiohttp_jinja2 import template
from datetime import datetime
from tinydb import Query


logger = logging.getLogger(__name__)


Post = namedtuple(
    'Post',
    ['title', 'subtitle', 'date', 'author', 'slug', 'options', 'content'])
Comment = namedtuple(
    'Comment', ['author', 'date', 'content', 'email', 'post_slug'])
Contact = namedtuple(
    'Contact', ['email', 'name', 'message', 'date'])


def require_tinydb_conn(f):
    @wraps(f)
    async def fun(request, *args, **kwargs):
        db = request.app.db
        return await f(request, *args, **kwargs, conn=db)

    return fun


def to_tinydb(obj):
    ret = obj._asdict()
    ret['type'] = type(obj).__name__.lower()
    return ret


def from_tinydb(dict_):
    dict_ = dict(dict_)  # make clone of obj
    type_ = dict_.pop('type').title()
    klass = globals()[type_](**dict_)
    return klass
    pass


def first(collection, *, default=None):
    return next(iter(collection), default)


PAGE_SIZE = 5


def get_total_pages():
    posts_path = os.path.join(os.path.dirname(__file__), '..', 'posts')
    files = os.listdir(posts_path)
    return ceil(len(files) / PAGE_SIZE)


def parse_post_options(options_str):
    class Settings():
        def __init__(self, **kwargs):
            self.__dict__ = kwargs

        def __eq__(self, other):
            if isinstance(other, dict):
                return self.__dict__ == other
            return self.__dict__ == other.__dict__

        def __neq__(self, other):
            return not self.__eq__(other)

    settings = Settings()

    if not options_str:
        return settings

    options_list = options_str.split(',')
    for option in options_list:
        setattr(settings, option, True)

    return settings


def get_blog_posts():
    ret = []

    posts_path = os.path.join(os.path.dirname(__file__), '..', 'posts')
    files = os.listdir(posts_path)
    for file_ in files:
        if not file_.endswith('.md'):
            continue
        file_path = os.path.join(posts_path, file_)
        with open(file_path) as f:
            file_content = f.readlines()
            title, subtitle, date, slug, author, options, *content = (
                file_content)
            html_content = markdown.markdown('\n'.join(content))

            title = title.strip('#').strip()
            subtitle = subtitle.strip('#').strip()
            date = date.strip('#').strip()
            slug = slug.strip('#').strip()
            author = author.strip('#').strip()
            options = options.strip('#').strip()

            ret.append(Post(
                title=title, subtitle=subtitle, date=date, slug=slug,
                author=author, options=parse_post_options(options),
                content=html_content))

    def sort_by_date(post):
        x = datetime.strptime(post.date, '%Y-%m-%dT%H:%M:%S')
        return x

    ret.sort(key=sort_by_date, reverse=True)
    return ret


def get_blog_posts_paginated(*, page=1):
    start = (page - 1) * PAGE_SIZE
    end = page * PAGE_SIZE
    posts = get_blog_posts()
    return posts[start:end]


def get_post_comments(app, post_slug):
    q = Query()
    result = app.db.search((q.type == 'comment') & (q.post_slug == post_slug))
    return [from_tinydb(x) for x in result]


@template('index.jinja2')
@require_tinydb_conn
async def handle_index(request, conn):
    total_pages = get_total_pages()
    posts = get_blog_posts_paginated()
    return {'posts': posts, 'page': 1, 'total_pages': total_pages}


@template('index.jinja2')
@require_tinydb_conn
async def handle_page(request, conn):
    page = int(request.match_info.get('page'))
    total_pages = get_total_pages()
    if page > total_pages or page < 1:
        raise web.HTTPNotFound()

    posts = get_blog_posts_paginated(page=page)
    return {'posts': posts, 'page': page, 'total_pages': total_pages}


@template('contact.jinja2')
@require_tinydb_conn
async def handle_contact(request, conn):
    return {}


@require_tinydb_conn
async def handle_contact_form(request, conn):
    try:
        data = await request.json()
    except json.JSONDecodeError:
        raise web.HTTPBadRequest()

    # most validation is handled by JS
    required_keys = set(['name', 'email', 'message'])
    posted_keys = set(data.keys())
    if required_keys - posted_keys:
        raise web.HTTPBadRequest()

    name, email, message = data['name'], data['email'], data['message']

    date = datetime.strftime(datetime.utcnow(), '%Y-%m-%dT%H:%M:%S')
    contact = Contact(
        email=email, name=name, message=message, date=date)
    request.app.db.insert(to_tinydb(contact))
    return web.Response(status=204)


@template('about.jinja2')
@require_tinydb_conn
async def handle_about(request, conn):
    return {}


@template('blog_post.jinja2')
@require_tinydb_conn
async def handle_blog_post(request, conn):
    slug = request.match_info.get('slug')

    posts = get_blog_posts()
    post = first([x for x in posts if x.slug == slug])
    if not post:
        raise web.HTTPNotFound()

    comments = get_post_comments(request.app, post.slug)
    return {'post': post, 'comments': comments}


@require_tinydb_conn
async def handle_blog_post_comment(request, conn):
    try:
        data = await request.json()
    except json.JSONDecodeError:
        raise web.HTTPBadRequest()

    # most validation is handled by JS
    required_keys = set(['post_slug', 'name', 'email', 'message'])
    posted_keys = set(data.keys())
    if required_keys - posted_keys:
        raise web.HTTPBadRequest()

    slug, name, email, message = (
        data['post_slug'], data['name'], data['email'], data['message'])

    slugs = set([x.slug for x in get_blog_posts()])
    if slug not in slugs:
        raise web.HTTPBadRequest()

    # TODO: maybe some throttle or spam-limit

    date = datetime.strftime(datetime.utcnow(), '%Y-%m-%dT%H:%M:%S')
    comment = Comment(
        author=name, date=date, content=message, email=email, post_slug=slug)
    request.app.db.insert(to_tinydb(comment))

    return web.Response(status=204)
