# -*- coding: utf-8 -*-

from __future__ import absolute_import

import ast
import sys
import struct

try:
    import ujson as json
except ImportError:
    import json

PY3 = sys.version_info[0] == 3

if PY3:
    string_types = str,
else:
    string_types = basestring,


def flatten_dtype(dtype):
    dtype = str(dtype)
    if dtype.startswith(('{', '[')):
        return ast.literal_eval(dtype)
    return dtype


def write_i64(stream, *values):
    for value in values:
        stream.write(struct.pack('<Q', value))


def read_i64(stream, count=None):
    if count is None:
        return struct.unpack('<Q', stream.read(8))[0]
    return tuple(struct.unpack('<Q', stream.read(8))[0] for _ in range(count))


def write_json(stream, data):
    payload = json.dumps(data).encode('utf-8')
    write_i64(stream, len(payload))
    stream.write(payload)
    return len(payload) + 8


def read_json(stream):
    length = read_i64(stream)
    return json.loads(stream.read(length).decode('utf-8'))
