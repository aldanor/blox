# -*- coding: utf-8 -*-

from blox.file import File
from pytest import raises_regexp


class TestFile(object):
    def test_mode(self, tmpfile):
        raises_regexp(ValueError, 'invalid mode', File, tmpfile, 'foo')
        assert File(tmpfile).mode == 'r'
        assert File(tmpfile, 'w').mode == 'w'

    def test_filename(self, tmpfile):
        raises_regexp(IOError, 'No such file', File, '/foo/bar/baz')
        assert File(tmpfile).filename == tmpfile

    def test_create_dataset(self, tmpfile):
        raises_regexp(IOError, 'file is not writable',
                      File(tmpfile).create_dataset, 'a', [])
