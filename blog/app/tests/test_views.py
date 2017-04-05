# -*- coding: utf-8 -*-
import pytest
import mock
from datetime import datetime
from tinydb import Query
from functools import wraps
from app.views import get_blog_posts, Post, to_tinydb


@mock.patch('app.views.os')
@mock.patch('app.views.open')
def test_get_blog_posts(mock_open, mock_os):
    mock_os.listdir.return_value = ['a.md', 'b.md', 'c.md', 'd.md', 'efee']
    mock_open.return_value.__enter__.return_value.readlines.side_effect = [
        [
            'Title', 'Sub', '2016-03-03T11:22:00', 'test-slug', 'image',
            'Author', '', 'Content 1'
        ],
        [
            'Title 1', 'Sub 1', '2016-03-03T11:28:00', 'test-slug-1',
            'image', 'Author 2', '', 'Content 2',
        ],
        [
            'Title 2', 'Sub 2', '2016-03-03T11:25:00', 'test-slug-2',
            '', 'Author 3', '', 'Content 3'
        ],
        [
            'Title 3', 'Sub 3', '2016-03-03T12:25:00', 'test-slug-3',
            '', 'Author 4', 'disable_comments', 'Content 4',
        ],
    ]

    posts = get_blog_posts()
    assert len(posts) == 4
    assert posts == [
        Post(
            title='Title 3', subtitle='Sub 3', date='2016-03-03T12:25:00',
            slug='test-slug-3', author='Author 4', image='',
            options={'disable_comments': True}, content='<p>Content 4</p>'),
        Post(
            title='Title 1', subtitle='Sub 1', date='2016-03-03T11:28:00',
            slug='test-slug-1', author='Author 2', options={},
            image='image', content='<p>Content 2</p>'),
        Post(
            title='Title 2', subtitle='Sub 2', date='2016-03-03T11:25:00',
            slug='test-slug-2', author='Author 3', options={},
            image='', content='<p>Content 3</p>'),
        Post(
            title='Title', subtitle='Sub', date='2016-03-03T11:22:00',
            slug='test-slug', author='Author', options={},
            image='image', content='<p>Content 1</p>'),
    ]

    assert mock_os.listdir.call_count == 1
    assert mock_open.call_count == 4


async def test_index(test_client_auth):
    mock_get_blog_posts = mock.patch(
        'app.views.get_blog_posts', return_value=[])
    with mock_get_blog_posts as m:
        resp = await test_client_auth.get('/')

    assert resp.status == 200

    data = await resp.content.read()
    data = data.decode('utf-8')
    assert '- Index' in data
    assert 'No posts.' in data
    assert 'Newer Posts' not in data
    assert 'Older Posts' not in data


async def test_index_has_posts(test_client_auth, fixt_blog_posts):
    mock_get_blog_posts = mock.patch(
        'app.views.get_blog_posts', return_value=fixt_blog_posts)

    with mock_get_blog_posts as m:
        resp = await test_client_auth.get('/')

    assert resp.status == 200

    data = await resp.content.read()
    data = data.decode('utf-8')
    assert 'No posts.' not in data
    assert 'Newer Posts' not in data
    assert 'Older Posts' not in data

    assert 'Title 1' in data
    assert 'Sub 1' in data
    assert '01.01.2010 11:11' in data
    assert '/post/slug-1' in data

    assert 'Title 2' in data
    assert 'Sub 2' in data
    assert '02.01.2010 11:11' in data
    assert '/post/slug-2' in data


async def test_page_has_posts_from_first(
        test_client_auth, fixt_blog_posts_two_pages):
    mock_get_total_pages = mock.patch(
        'app.views.get_total_pages', return_value=2)
    mock_get_blog_posts = mock.patch(
        'app.views.get_blog_posts', return_value=fixt_blog_posts_two_pages)

    with mock_get_blog_posts as m:
        with mock_get_total_pages as m:
            resp = await test_client_auth.get('/page/1')

    assert resp.status == 200

    data = await resp.content.read()
    data = data.decode('utf-8')
    assert 'No posts.' not in data
    assert 'Newer Posts' not in data
    assert 'Older Posts' in data

    assert 'Title 1' in data
    assert 'Sub 1' in data
    assert '01.01.2010 11:11' in data
    assert '/post/slug-1' in data

    assert 'Title 5' in data
    assert 'Sub 5' in data
    assert '05.01.2010 11:11' in data
    assert '/post/slug-5' in data

    assert 'Title 6' not in data
    assert 'Sub 6' not in data
    assert '06.01.2010 11:11' not in data
    assert '/post/slug-6' not in data


async def test_page_has_posts_from_second(
        test_client_auth, fixt_blog_posts_two_pages):
    mock_get_total_pages = mock.patch(
        'app.views.get_total_pages', return_value=2)
    mock_get_blog_posts = mock.patch(
        'app.views.get_blog_posts', return_value=fixt_blog_posts_two_pages)

    with mock_get_blog_posts as m:
        with mock_get_total_pages as m:
            resp = await test_client_auth.get('/page/2')

    assert resp.status == 200

    data = await resp.content.read()
    data = data.decode('utf-8')
    assert '- Page 2 of 2' in data
    assert 'No posts.' not in data
    assert 'Newer Posts' in data
    assert 'Older Posts' not in data

    assert 'Title 1' not in data
    assert 'Sub 1' not in data
    assert '01.01.2010 11:11' not in data
    assert '/post/slug-1' not in data

    assert 'Title 5' not in data
    assert 'Sub 5' not in data
    assert '05.01.2010 11:11' not in data
    assert '/post/slug-5' not in data

    assert 'Title 6' in data
    assert 'Sub 6' in data
    assert '06.01.2010 11:11' in data
    assert '/post/slug-6' in data


async def test_page_not_found(test_client_auth):
    mock_get_total_pages = mock.patch(
        'app.views.get_total_pages', return_value=1)
    with mock_get_total_pages as m:
        resp = await test_client_auth.get('/page/2')

    assert resp.status == 404

    data = await resp.content.read()
    data = data.decode('utf-8')
    assert 'Error 404' in data


async def test_blog_post(test_client_auth, fixt_blog_posts):
    mock_get_blog_posts = mock.patch(
        'app.views.get_blog_posts', return_value=fixt_blog_posts)
    with mock_get_blog_posts as m:
        resp = await test_client_auth.get('/post/slug-1')

    assert resp.status == 200

    data = await resp.content.read()
    data = data.decode('utf-8')
    assert '- Title 1' in data
    assert 'Title 1' in data
    assert 'Sub 1' in data
    assert '01.01.2010 11:11' in data
    assert 'Test content 1' in data
    assert 'No comments.' in data
    assert 'Name' in data
    assert 'Email Address' in data
    assert 'Message' in data
    assert 'Send' in data


async def test_blog_post_image(test_client_auth, fixt_blog_post_image):
    mock_get_blog_posts = mock.patch(
        'app.views.get_blog_posts', return_value=[fixt_blog_post_image])
    with mock_get_blog_posts as m:
        resp = await test_client_auth.get('/post/slug-1')

    assert resp.status == 200

    data = await resp.content.read()
    data = data.decode('utf-8')
    assert '/static/img/test.jpg' in data
    assert '- Title 1' in data
    assert 'Title 1' in data
    assert 'Sub 1' in data
    assert '01.01.2010 11:11' in data
    assert 'Test content 1' in data
    assert 'No comments.' in data
    assert 'Name' in data
    assert 'Email Address' in data
    assert 'Message' in data
    assert 'Send' in data


async def test_blog_post_comments(
        test_client_auth, app, fixt_blog_post, fixt_blog_comment):
    app.db.insert(to_tinydb(fixt_blog_comment))

    mock_get_blog_posts = mock.patch(
        'app.views.get_blog_posts', return_value=[fixt_blog_post])
    with mock_get_blog_posts as m:
        resp = await test_client_auth.get('/post/slug-1')

    assert resp.status == 200

    data = await resp.content.read()
    data = data.decode('utf-8')
    assert 'Title 1' in data
    assert 'Sub 1' in data
    assert '01.01.2010 11:11' in data
    assert 'Test content 1' in data
    assert 'No comments.' not in data
    assert 'Comment Author' in data
    assert 'Hello Comment' in data
    assert '05.04.2016 12:52' in data
    assert 'john@doe.pl' not in data


async def test_blog_post_comments_disabled(
        test_client_auth, fixt_blog_post_comments_disabled):
    mock_get_blog_posts = mock.patch(
        'app.views.get_blog_posts',
        return_value=[fixt_blog_post_comments_disabled])
    with mock_get_blog_posts as m:
        resp = await test_client_auth.get('/post/slug-1')

    assert resp.status == 200

    data = await resp.content.read()
    data = data.decode('utf-8')
    assert 'Title 1' in data
    assert 'Sub 1' in data
    assert '01.01.2010 11:11' in data
    assert 'Test content 1' in data
    assert 'No comments.' not in data
    assert 'Name' not in data
    assert 'Email Address' not in data
    assert 'Message' not in data
    assert 'Send' not in data


async def test_blog_post_not_found(test_client_auth):
    mock_get_blog_posts = mock.patch(
        'app.views.get_blog_posts', return_value=[])
    with mock_get_blog_posts as m:
        resp = await test_client_auth.get('/post/test-slug')

    assert resp.status == 404

    data = await resp.content.read()
    data = data.decode('utf-8')
    assert 'Error 404' in data


async def test_about(test_client_auth):
    resp = await test_client_auth.get('/about')

    assert resp.status == 200

    data = await resp.content.read()
    data = data.decode('utf-8')
    assert '- About' in data
    assert 'About Me' in data


async def test_contact(test_client_auth):
    resp = await test_client_auth.get('/contact')

    assert resp.status == 200

    data = await resp.content.read()
    data = data.decode('utf-8')
    assert '- Contact' in data
    assert 'Contact Me' in data


async def test_contact_can_send(test_client_auth, app):
    send_data = {'name': 'Test', 'email': 'test@test.pl', 'message': 'Hello!'}

    mock_datetime = mock.patch('app.views.datetime')
    with mock_datetime as md:
        md.strftime.return_value = '2017-04-05T12:33:00'
        resp = await test_client_auth.post('/contact', json=send_data)

    assert resp.status == 204

    result = app.db.search(Query().type == 'contact')
    assert len(result) == 1
    assert result == [
        {
            'type': 'contact',
            'email': 'test@test.pl',
            'name': 'Test',
            'message': 'Hello!',
            'date': '2017-04-05T12:33:00',
        }
    ]


async def test_contact_no_json(test_client_auth):
    resp = await test_client_auth.post('/contact', data='ble')

    assert resp.status == 400

    data = await resp.content.read()
    data = data.decode('utf-8')
    assert 'Error 400' in data


async def test_contact_invalid_data(test_client_auth):
    resp = await test_client_auth.post('/contact', json={'data': 'x'})

    assert resp.status == 400

    data = await resp.content.read()
    data = data.decode('utf-8')
    assert 'Error 400' in data


async def test_contact_too_long_data(test_client_auth):
    send_data = {
        'name': 'Test' * 100,
        'email': 'test@test.pl',
        'message': 'Hello!' * 200
    }

    resp = await test_client_auth.post('/contact', json=send_data)
    assert resp.status == 400

    data = await resp.content.read()
    data = data.decode('utf-8')
    assert 'Error 400' in data


async def test_comment_can_send(test_client_auth, app, fixt_blog_post):
    app.db.insert(to_tinydb(fixt_blog_post))

    send_data = {
        'name': 'Test',
        'email': 'test@test.pl',
        'message': 'Hello!',
        'post_slug': 'slug-1',
    }

    mock_get_blog_posts = mock.patch(
        'app.views.get_blog_posts', return_value=[fixt_blog_post])
    mock_datetime = mock.patch('app.views.datetime')
    with mock_get_blog_posts as m:
        with mock_datetime as md:
            md.strftime.return_value = '2017-04-05T12:33:00'
            resp = await test_client_auth.post('/comment', json=send_data)

    assert resp.status == 204

    result = app.db.search(Query().type == 'comment')
    assert result == [
        {
            'type': 'comment',
            'author': 'Test',
            'email': 'test@test.pl',
            'content': 'Hello!',
            'post_slug': 'slug-1',
            'date': '2017-04-05T12:33:00',
        }
    ]


async def test_comment_not_existing_slug(test_client_auth):
    send_data = {
        'name': 'Test',
        'email': 'test@test.pl',
        'message': 'Hello!',
        'post_slug': 'test-slug',
    }

    mock_get_blog_posts = mock.patch(
        'app.views.get_blog_posts', return_value=[])
    with mock_get_blog_posts as m:
        resp = await test_client_auth.post('/comment', json=send_data)

    assert resp.status == 400


async def test_comment_no_json(test_client_auth):
    resp = await test_client_auth.post('/comment', data='ble')

    assert resp.status == 400

    data = await resp.content.read()
    data = data.decode('utf-8')
    assert 'Error 400' in data


async def test_comment_invalid_data(test_client_auth):
    resp = await test_client_auth.post('/comment', json={'data': 'x'})

    assert resp.status == 400

    data = await resp.content.read()
    data = data.decode('utf-8')
    assert 'Error 400' in data


async def test_comment_too_long_data(
        test_client_auth, app, fixt_blog_post):
    app.db.insert(to_tinydb(fixt_blog_post))
    send_data = {
        'name': 'Test' * 100,
        'email': 'test@test.pl' * 100,
        'message': 'Hello!' * 200,
        'post_slug': 'slug-1',
    }

    mock_get_blog_posts = mock.patch(
        'app.views.get_blog_posts', return_value=[fixt_blog_post])
    with mock_get_blog_posts as m:
        resp = await test_client_auth.post('/comment', json=send_data)

    assert resp.status == 400

    data = await resp.content.read()
    data = data.decode('utf-8')
    assert 'Error 400' in data
