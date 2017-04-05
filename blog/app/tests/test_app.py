# -*- coding: utf-8 -*-
import pytest
import json
from datetime import datetime, timedelta
from app.app import safe_unpack
from app.tests.conftest import Any, AlmostSimilarDateTime


@pytest.mark.parametrize('data,count,expected', (
    (('a', 'b'), 2, ('a', 'b')),  # exact
    (('a', 'b', 'c'), 2, ('a', 'b')),  # too long input
    (('a',), 2, ('a', None)),  # too short input
    (('a',), 0, tuple()),  # zero wanted
    (tuple(), 0, tuple()),  # zero
    (tuple(), 2, (None, None)),  # two wanted but zero
))
def test_safe_unpack(data, count, expected):
    assert safe_unpack(data, count) == expected
