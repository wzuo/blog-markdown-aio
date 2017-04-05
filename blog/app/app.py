# -*- coding: utf-8 -*-
import logging

from aiohttp import web
from datetime import datetime


logger = logging.getLogger(__name__)


def json_response(data, *args, **kwargs):
    def _serialize_data(data):
        if isinstance(data, list):
            return [_serialize_data(x) for x in data]
        elif not isinstance(data, dict):
            return data

        for k in data:
            v = data[k]
            if isinstance(v, datetime):
                data[k] = v.isoformat()
        return data
    return web.json_response(
        _serialize_data(data), content_type='application/json',
        *args, **kwargs)


def is_int(element):
    try:
        int(element)
        return True
    except (TypeError, ValueError):
        return False


def safe_unpack(data, wanted_count):
    if len(data) < wanted_count:
        return tuple(list(data) + [None] * (wanted_count - len(data)))

    return tuple(data[:wanted_count])


def filter_keys(test, dict_):
    return {k: v for k, v in dict_.items() if not test(k)}
