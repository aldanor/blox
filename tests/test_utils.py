# -*- coding: utf-8 -*-

import json
import pytest
import numpy as np
from io import BytesIO

from blox.utils import flatten_dtype, restore_dtype, read_i64, write_i64, read_json, write_json


@pytest.mark.parametrize('dtype, flattened', [
    ('f8', 'float64'),
    ('i8', 'int64'),
    ([('a', '<f4'), ('b', [('c', '<i4'), ('d', '<i2')])],
     [('a', '<f4'), ('b', [('c', '<i4'), ('d', '<i2')])],),
    ((np.record, [('a', '<f4'), ('b', [('c', '<i4'), ('d', '<i2')])]),
     ('record', [('a', '<f4'), ('b', [('c', '<i4'), ('d', '<i2')])]))
])
def test_flatten_restore_dtype(dtype, flattened):
    dtype = np.dtype(dtype)
    assert flatten_dtype(dtype) == flattened
    assert restore_dtype(flatten_dtype(dtype)) == dtype
    assert restore_dtype(json.loads(json.dumps(flatten_dtype(dtype)))) == dtype


def test_read_write_i64():
    stream = BytesIO()
    write_i64(stream, 10)
    assert stream.tell() == 8
    stream.seek(0)
    assert read_i64(stream) == 10
    write_i64(stream, 11, 12, 13)
    assert stream.tell() == 32
    stream.seek(8)
    assert read_i64(stream, 2) == (11, 12)
    assert read_i64(stream, 1) == (13,)
    assert read_i64(stream, 0) == ()


@pytest.mark.parametrize('data', [
    42, 'foo', [1, 2, 3],
    {'a': {'b': [1, 2, 3]}, 'c': 'foo', 'd': 42}
])
def test_read_write_json(data):
    stream = BytesIO()
    total = write_json(stream, data)
    assert stream.tell() == total
    stream.seek(0)
    length = read_i64(stream)
    assert stream.tell() == total - length
    assert json.loads(stream.read(length).decode('utf-8')) == data
    stream.seek(0)
    assert read_json(stream) == data
