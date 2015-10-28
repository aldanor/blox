# -*- coding: utf-8 -*-

from pytest import raises_regexp

from blox.file import File


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
