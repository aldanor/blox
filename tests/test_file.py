# -*- coding: utf-8 -*-

import io
import os
import blosc
import pytest
import py.path
import numpy as np
from pytest import raises_regexp

from blox.file import File, is_blox, FORMAT_STRING, FORMAT_VERSION
from blox.utils import write_i64


def test_is_blox(tmpfile):
    assert is_blox(tmpfile)
    assert not is_blox('/foo/bar/baz')
    with io.open(tmpfile, 'wb') as f:
        f.write(b'foo')
    assert not is_blox(tmpfile)
    with io.open(tmpfile, 'wb') as f:
        f.write(FORMAT_STRING)
    assert not is_blox(tmpfile)
    with io.open(tmpfile, 'wb') as f:
        f.write(FORMAT_STRING)
        write_i64(f, FORMAT_VERSION)
    assert is_blox(tmpfile)


class TestFile(object):
    def test_mode_writable(self, tmpfile):
        raises_regexp(ValueError, 'invalid mode', File, tmpfile, 'foo')
        f1 = File(tmpfile)
        assert f1.mode == 'r' and not f1.writable
        f2 = File(tmpfile, 'w')
        assert f2.mode == 'w' and f2.writable

    def test_py_path_local(self, tmpfile):
        assert File(py.path.local(tmpfile)).filename == tmpfile

    def test_filename(self, tmpfile):
        raises_regexp(IOError, 'No such file', File, '/foo/bar/baz')
        assert File(tmpfile).filename == tmpfile

    def test_format_version(self, tmpfile):
        assert File(tmpfile).format_version == FORMAT_VERSION
        assert File(tmpfile + '.2', mode='w').format_version == FORMAT_VERSION

    def test_write_array(self, tmpfile):
        raises_regexp(IOError, 'file is not writable',
                      File(tmpfile).write_array, 'a', [])

    def test_iter(self, tmpfile):
        f = File(tmpfile, 'w')
        f.write_array('c', 10)
        f.write_array('a', [1, 2, 3])
        f.write_json('b', {'foo': 'bar'})
        f.write_json('d', 42)
        assert list(f) == ['a', 'b', 'c', 'd']
        f.close()
        f = File(tmpfile)
        assert list(f) == ['a', 'b', 'c', 'd']

    def test_filesize(self, tmpfile):
        assert os.stat(tmpfile).st_size == File(tmpfile).filesize

    @pytest.mark.parametrize(
        'num, comp', list(enumerate(blosc.compressor_list())) + [(None, None)]
    )
    def test_read_write(self, tmpfile, num, comp):
        options = {}
        if comp is not None:
            options['compression'] = comp
            options['level'] = 1 + num * 2
            options['shuffle'] = num % 2
        entries = [
            ('a', 'json', {'a': 'b'}),
            ('b', 'array', np.array([1, 2, 3], 'float32')),
            ('c', 'json', 42),
            ('d', 'array', np.rec.fromarrays([[1, 2], [3, 4]], names='x, y')),
            ('e', 'array', ['foo', 'bar'])
        ]
        index = {'a': 0, 'b': 1, 'c': 0, 'd': 1, 'e': 1}
        with File(tmpfile, 'w') as f:
            for key, tp, data in entries:
                getattr(f, 'write_' + tp)(key, data)
            assert ''.join(f) == 'abcde'
            assert {k: v[0] for k, v in f._index.items()} == index
        f = File(tmpfile)
        assert ''.join(f) == 'abcde'
        assert {k: v[0] for k, v in f._index.items()} == index
        for key, tp, data in entries:
            if tp == 'json':
                assert f.read(key) == data
            else:
                np.testing.assert_array_equal(f.read(key), data)

    def test_invalid_key(self, tmpfile):
        f = File(tmpfile, 'w')
        pytest.raises_regexp(ValueError, 'invalid key: expected string',
                             f.write_json, 42, 0)
        pytest.raises_regexp(ValueError, 'invalid key: empty string',
                             f.write_json, '', 0)
        f.write_json('foo', 'bar')
        pytest.raises_regexp(ValueError, "key already exists: 'foo'",
                             f.write_json, 'foo', 'baz')
        f.close()
        f = File(tmpfile)
        pytest.raises_regexp(ValueError, 'invalid key: expected string',
                             f.read, 42)
        pytest.raises_regexp(KeyError, 'bar',
                             f.read, 'bar')

    def test_close_handle(self, tmpfile):
        f = File(tmpfile, 'w')
        f.close()
        pytest.raises_regexp(IOError, 'the file handle has been closed',
                             f.read, 'foo')
        pytest.raises_regexp(IOError, 'the file handle has been closed',
                             f.write_array, 'foo', [1, 2])
        pytest.raises_regexp(IOError, 'the file handle has been closed',
                             f.write_json, 'foo', [1, 2])
        f.close()
        assert f.filename == tmpfile
        assert f.writable
        f = File(tmpfile)
        f.close()
        f.close()

    def test_flush_on_open(self, tmpfile):
        with File(tmpfile + '.2', 'w'):
            assert File(tmpfile + '.2').filename == tmpfile + '.2'

    def test_format_signature(self, tmpfile):
        with io.open(tmpfile, 'wb') as f:
            f.write(b'foo')
        pytest.raises_regexp(IOError, 'unrecognized file format',
                             File, tmpfile)
        with open(tmpfile, 'wb') as f:
            f.write(FORMAT_STRING)
            f.write(b'foo')
        pytest.raises_regexp(IOError, 'unable to read file version',
                             File, tmpfile)
        with open(tmpfile, 'wb') as f:
            f.write(FORMAT_STRING)
            write_i64(f, 0)
        pytest.raises_regexp(IOError, r'incompatible version: 0 \(expected {}\)'
                             .format(FORMAT_VERSION), File, tmpfile)

    def test_corrupt_index(self, tmpfile):
        with io.open(tmpfile, 'wb') as f:
            f.write(FORMAT_STRING)
            write_i64(f, FORMAT_VERSION)
            f.write(b'foo')
        pytest.raises_regexp(IOError, 'unable to read index',
                             File, tmpfile)

    def test_fail_on_write(self, tmpfile):
        with File(tmpfile, 'w') as f:
            f.write_json('a', 42)
            pytest.raises_regexp(ValueError, 'unable to serialize: invalid dtype',
                                 f.write_array, 'b', {})
        with File(tmpfile) as f:
            assert list(f) == ['a']
            assert f.read('a') == 42
