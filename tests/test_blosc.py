# -*- coding: utf-8 -*-

import io
import blosc
import pytest
import numpy as np
from pytest import raises_regexp

from blox.utils import read_json
from blox.blosc import read_blosc, write_blosc


@pytest.fixture(params=[
    np.arange(10).astype(int),
    np.arange(10).astype(float),
    np.arange(12).reshape((2, 2, 3)),
    np.array([]),
    np.array([['foo', 'bar']]),
    [[1.1, 2.2], [3.3, 4.4]],
    'foo',
    42
])
def array(request):
    return request.param


@pytest.fixture(params=blosc.compressor_list())
def compression(request):
    return request.param


@pytest.fixture(params=[0, 1, 2], ids=['none', 'byte', 'bit'])
def shuffle(request):
    return request.param


@pytest.fixture
def write_result(array, compression, shuffle):
    stream = io.BytesIO()
    length = write_blosc(stream, array, compression, 5, shuffle)
    return (stream, length)


@pytest.fixture
def stream(write_result):
    return write_result[0]


@pytest.fixture
def length(write_result):
    return write_result[1]


class TestBlosc(object):
    def test_length(self, stream, length):
        assert stream.tell() == length

    def test_metadata(self, array, compression, shuffle, stream, length):
        array = np.asanyarray(array)
        stream.seek(0)
        meta = read_json(stream)
        assert meta['comp'] == [compression, 5, shuffle]
        assert meta['size'] == array.size * array.dtype.itemsize
        assert np.dtype(meta['dtype']) == array.dtype
        assert meta['shape'] == list(array.shape)
        assert stream.tell() == length - meta['length']

    def test_comp_name(self, array, compression, shuffle, stream, length):
        stream2 = io.BytesIO()
        length2 = write_blosc(stream2, array, 'blosc:' + compression, 5, shuffle)
        assert length2 == length
        assert stream2.getvalue() == stream.getvalue()

    def test_read_blosc(self, array, stream):
        array = np.asanyarray(array)
        stream.seek(0)
        out = read_blosc(stream)
        assert out.shape == array.shape
        assert out.dtype == array.dtype
        np.testing.assert_array_equal(out, array)

    def test_recarray(self):
        arr = np.rec.fromarrays(np.arange(6).reshape(2, 3), names='x, y').view(np.recarray)
        assert arr.dtype.type is np.record
        stream = io.BytesIO()
        write_blosc(stream, arr)
        stream.seek(0)
        out = read_blosc(stream)
        assert isinstance(out, np.recarray)
        assert out.dtype == arr.dtype
        assert out.dtype.type is np.record

    def test_noncontiguous(self):
        stream = io.BytesIO()
        raises_regexp(ValueError, 'expected contiguous array',
                      write_blosc, stream, np.ndarray((3, 4, 5), order='F').transpose(0, 2, 1))

    def test_read_into(self, array, stream):
        array = np.asanyarray(array)

        stream.seek(0)
        pytest.raises_regexp(TypeError, 'expected ndarray', read_blosc, stream,
                             out='foo')
        stream.seek(0)
        pytest.raises_regexp(ValueError, 'incompatible shape', read_blosc, stream,
                             out=np.empty((42, 42)))
        stream.seek(0)
        pytest.raises_regexp(ValueError, 'incompatible dtype', read_blosc, stream,
                             out=np.empty(array.shape, np.uint8))

        if array.ndim == 3:
            out = np.empty_like(array.transpose(0, 2, 1), order='F').transpose(0, 2, 1)
            stream.seek(0)
            pytest.raises_regexp(ValueError, 'expected contiguous array', read_blosc, stream,
                                 out=out)

        out = np.empty_like(array)
        stream.seek(0)
        assert read_blosc(stream, out=out) is out
        stream.seek(0)
        np.testing.assert_array_equal(out, read_blosc(stream))
