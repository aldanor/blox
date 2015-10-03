# -*- coding: utf-8 -*-

from __future__ import absolute_import

import blosc
import numpy as np

from blox.utils import read_json, write_json, flatten_dtype, string_types


def write_blosc(data, stream, compression='lz4', level=5, shuffle=True):
    if isinstance(compression, string_types) and compression.startswith('blosc:'):
        compression = compression[6:]
    data = np.asanyarray(data)
    if not data.flags.contiguous:
        raise ValueError('expected contiguous array')
    payload = blosc.compress_ptr(
        data.__array_interface__['data'][0],
        data.size,
        data.dtype.itemsize,
        cname=compression,
        clevel=level,
        shuffle=shuffle
    )
    meta = {
        'size': data.size * data.dtype.itemsize,
        'length': len(payload),
        'comp': (compression, level, int(shuffle)),
        'shape': data.shape,
        'dtype': flatten_dtype(data.dtype)
    }
    meta_length = write_json(stream, meta)
    stream.write(payload)
    return len(payload) + meta_length


def read_blosc(stream, out=None):
    meta = read_json(stream)
    shape = meta['shape']
    dtype = np.dtype(meta['dtype'])
    if out is None:
        out = np.empty(shape, dtype)
    else:
        if not isinstance(out, np.ndarray):
            raise TypeError('expected ndarray, got {}'.format(type(out).__name__))
        if out.shape != shape:
            raise ValueError('incompatible shape: expected {}, got {}'.format(shape, out.shape))
        if out.dtype != dtype:
            raise ValueError('incompatible dtype: expected {}, got {}'.format(dtype, out.dtype))
        if not out.flags.contiguous:
            raise ValueError('expected contiguous array')
    blosc.decompress_ptr(
        stream.read(meta['length']),
        out.__array_interface__['data'][0]
    )
    return out
