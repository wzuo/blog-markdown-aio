# -*- coding: utf-8 -*-
import pytest
import asyncio
import os
from datetime import datetime, timedelta
from aiohttp.test_utils import loop_context
from os import environ as env
from app import create, TestConfig
from app.views import Post, Comment, parse_post_options


@pytest.fixture
def app(loop):
    return create(loop, conf=TestConfig)


@pytest.yield_fixture
def loop():
    with loop_context() as loop:
        yield loop


@pytest.yield_fixture
def event_loop(loop):
    """
    This is needed for correct functioning of the test_client
    of aiohttp together with pytest.mark.asyncio pytest-asyncio decorator.
    For more info check the following link:
    https://github.com/KeepSafe/aiohttp/issues/939
    """
    loop._close = loop.close
    loop.close = lambda: None
    yield loop
    loop.close = loop._close


@pytest.fixture
def test_client_auth(
        loop, test_client, app, fixt_auth_header,
):
    client_task = loop.run_until_complete(test_client(app))

    def auth_method(obj, method_name):
        """ Monkey-patch original method """
        new_method_name = 'original_%s' % method_name
        original_fun = getattr(obj, method_name)
        setattr(obj, new_method_name, original_fun)

        async def fun(url, **kwargs):
            kwargs.update(fixt_auth_header)

            new_fun = getattr(obj, new_method_name)
            return await new_fun(url, **kwargs)

        return fun

    client_task.get = auth_method(client_task, 'get')
    client_task.post = auth_method(client_task, 'post')
    client_task.delete = auth_method(client_task, 'delete')
    client_task.put = auth_method(client_task, 'put')
    yield client_task


@pytest.fixture
def test_client_no_auth(loop, test_client, app):
    client_task = loop.run_until_complete(test_client(app))
    yield client_task


@pytest.fixture
def fixt_auth_header():
    return {'headers': {'Authorization': 'Token TestToken'}}


@pytest.fixture
def fixt_blog_comment(fixt_blog_post):
    return Comment(
        author='Comment Author', date='2016-04-05T12:52:00',
        content='Hello Comment',
        post_slug=fixt_blog_post.slug, email='john@doe.pl')


@pytest.fixture
def fixt_blog_post():
    return Post(
        title='Title 1', subtitle='Sub 1', date='2010-01-01T11:11:00',
        slug='slug-1', author='P', options=parse_post_options(''),
        content='Test content 1')


@pytest.fixture
def fixt_blog_post_comments_disabled():
    return Post(
        title='Title 1', subtitle='Sub 1', date='2010-01-01T11:11:00',
        slug='slug-1', author='P',
        options=parse_post_options('disable_comments'),
        content='Test content 1')


@pytest.fixture
def fixt_blog_posts():
    return [
        Post(
            title='Title 1', subtitle='Sub 1', date='2010-01-01T11:11:00',
            slug='slug-1', author='P', options=parse_post_options(''),
            content='Test content 1'),
        Post(
            title='Title 2', subtitle='Sub 2', date='2010-01-02T11:11:00',
            slug='slug-2', author='D', options=parse_post_options(''),
            content='Test content 2'),
    ]


@pytest.fixture
def fixt_blog_posts_two_pages():
    return [
        Post(
            title='Title 1', subtitle='Sub 1', date='2010-01-01T11:11:00',
            slug='slug-1', author='P', options=parse_post_options(''),
            content='Test content 1'),
        Post(
            title='Title 2', subtitle='Sub 2', date='2010-01-02T11:11:00',
            slug='slug-2', author='D', options=parse_post_options(''),
            content='Test content 2'),
        Post(
            title='Title 3', subtitle='Sub 3', date='2010-01-03T11:11:00',
            slug='slug-3', author='E', options=parse_post_options(''),
            content='Test content 3'),
        Post(
            title='Title 4', subtitle='Sub 4', date='2010-01-04T11:11:00',
            slug='slug-4', author='Q', options=parse_post_options(''),
            content='Test content 4'),
        Post(
            title='Title 5', subtitle='Sub 5', date='2010-01-05T11:11:00',
            slug='slug-5', author='T', options=parse_post_options(''),
            content='Test content 5'),
        Post(
            title='Title 6', subtitle='Sub 6', date='2010-01-06T11:11:00',
            slug='slug-6', author='Y', options=parse_post_options(''),
            content='Test content 6'),
    ]


class Any(object):
    def __eq__(self, x):
        return True

    def __repr__(self):
        return 'Any'

    def __ne__(self, x):
        return not self.__eq__(x)


class AlmostSimilarDateTime(object):
    def __init__(self, expected, threshold=1):
        self.expected = expected
        self.threshold = threshold

    def __eq__(self, x):
        y = self.expected
        if isinstance(x, str):
            x = datetime.strptime(x, '%Y-%m-%dT%H:%M:%S.%f')

        if y < x:
            x, y = y, x
        return y - x < timedelta(seconds=self.threshold)

    def __repr__(self):
        return 'AlmostSimilarDateTime {}s {}'.format(
            self.threshold, self.expected)

    def __ne__(self, x):
        return not self.__eq__(x)
