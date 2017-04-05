# -*- coding: utf-8 -*-
import jsonschema
from .db import OremusType


login_schema = {
    'type': 'object',
    'properties': {
        'username': {'type': 'string'},
        'password': {'type': 'string'},
    },
    'required': ['username', 'password'],
}


register_schema = {
    'type': 'object',
    'properties': {
        'username': {'type': 'string', 'minLength': 3, 'maxLength': 25},
        'password': {'type': 'string', 'minLength': 5, 'maxLength': 50},
        'first_name': {'type': 'string', 'minLength': 3, 'maxLength': 30},
        'last_name': {'type': 'string', 'minLength': 3, 'maxLength': 50},
        'email': {'type': 'string', 'format': 'email'},
    },
    'required': ['username', 'password', 'first_name', 'last_name', 'email'],
}


refresh_token_schema = {
    'type': 'object',
    'properties': {
        'token': {'type': 'string'},
    },
    'required': ['token'],
}


oremus_create_schema = {
    'type': 'object',
    'properties': {
        'title': {'type': 'string', 'minLength': 3, 'maxLength': 128},
        'description': {'type': 'string', 'maxLength': 1000},
        'type': {'type': 'integer', 'enum': OremusType.as_list()},
        'category_id': {'type': 'integer'},
        'prayer_id': {'type': 'integer'},
    },
    'required': ['title', 'description', 'type', 'category_id', 'prayer_id'],
}
