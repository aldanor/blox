# -*- coding: utf-8 -*-

import io
import blosc
import pytest
import numpy as np
from pytest import raises_regexp
from numpy.testing import assert_array_equal

from blox.blosc import read_blosc, write_blosc
from blox.utils import read_json


@pytest.mark.parametrize('arr', [
    np.arange(10).astype(int),
    np.arange(10).astype(float),
    np.arange(12).reshape((4, 3)),
    np.arange(12).reshape((2, 2, 3)),
    np.array([]),
    np.array([['foo', 'bar']]),
    'foo',
    42
])
@pytest.mark.parametrize('compression', blosc.compressor_list())
@pytest.mark.parametrize('shuffle', [0, 1, 2], ids=['no', 'byte', 'bit'])
def test_roundtrip(arr, compression, shuffle):
    stream = io.BytesIO()
    length = write_blosc(arr, stream, compression, 5, shuffle)
    arr = np.asanyarray(arr)
    assert stream.tell() == length
    stream.seek(0)
    meta = read_json(stream)
    assert meta['comp'] == [compression, 5, shuffle]
    assert meta['size'] == arr.size * arr.dtype.itemsize
    assert np.dtype(meta['dtype']) == arr.dtype
    assert meta['shape'] == list(arr.shape)
    assert stream.tell() == length - meta['length']
    stream.seek(0)
    out = read_blosc(stream)
    assert out.shape == arr.shape
    assert out.dtype == arr.dtype
    assert_array_equal(out, arr)


def test_invalid_args():
    stream = io.BytesIO()
    raises_regexp(ValueError, 'expected contiguous array',
                  write_blosc, np.ndarray((3, 4, 5), order='F').transpose(0, 2, 1), stream)
