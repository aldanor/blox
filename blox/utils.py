# -*- coding: utf-8 -*-

from __future__ import absolute_import

import six
import struct
import functools
import numpy as np

try:
    import ujson as json
    json_dumps = json.dumps
except ImportError:
    import json
    json_dumps = functools.partial(json.dumps, separators=',:')


def flatten_dtype(dtype):
    dtype = np.dtype(dtype)
    if dtype.fields is not None:
        if dtype.type is np.record:
            return ('record', list(dtype.descr))
        return list(dtype.descr)
    return str(dtype)


def restore_dtype(dtype):
    def _convert_dtype(dt):
        # workaround for a long-standing bug in numpy:
        # https://github.com/numpy/numpy/issues/2407
        is_string = lambda s: isinstance(s, (six.text_type, six.string_types))
        if isinstance(dt, list):
            if len(dt) == 2 and is_string(dt[0]):
                return _convert_dtype(tuple(dt))
            return [_convert_dtype(subdt) for subdt in dt]
        elif isinstance(dt, tuple):
            return tuple(_convert_dtype(subdt) for subdt in dt)
        elif isinstance(dt, six.text_type) and six.PY2:
            return dt.encode('ascii')
        return dt
    dtype = _convert_dtype(dtype)
    if isinstance(dtype, (list, tuple)) and len(dtype) == 2 and dtype[0] == 'record':
        return np.dtype((np.record, np.dtype(dtype[1])))
    return np.dtype(dtype)


def write_i64(stream, *values):
    for value in values:
        stream.write(struct.pack('<Q', value))


def read_i64(stream, count=None):
    if count is None:
        return struct.unpack('<Q', stream.read(8))[0]
    return tuple(struct.unpack('<Q', stream.read(8))[0] for _ in range(count))


def write_json(stream, data):
    payload = json_dumps(data).encode('utf-8')
    write_i64(stream, len(payload))
    stream.write(payload)
    return len(payload) + 8


def read_json(stream):
    length = read_i64(stream)
    return json.loads(stream.read(length).decode('utf-8'))
