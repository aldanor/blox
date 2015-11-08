# -*- coding: utf-8 -*-

import io
import py.path
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
