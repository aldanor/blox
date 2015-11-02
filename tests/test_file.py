# -*- coding: utf-8 -*-

import io
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
    def test_mode(self, tmpfile):
        raises_regexp(ValueError, 'invalid mode', File, tmpfile, 'foo')
        assert File(tmpfile).mode == 'r'
        assert File(tmpfile, 'w').mode == 'w'

    def test_filename(self, tmpfile):
        raises_regexp(IOError, 'No such file', File, '/foo/bar/baz')
        assert File(tmpfile).filename == tmpfile

    def test_write_array(self, tmpfile):
        raises_regexp(IOError, 'file is not writable',
                      File(tmpfile).write_array, 'a', [])
