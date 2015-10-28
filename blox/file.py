# -*- coding: utf-8 -*-

from __future__ import absolute_import

import io
import os
import sys
import six
import atexit

from blox.utils import read_i64, write_i64, read_json, write_json
from blox.blosc import read_blosc, write_blosc


class File(object):
    def __init__(self, filename, mode=None):
        filename = os.path.abspath(os.path.expanduser(filename))
        if mode is None:
            mode = 'r' if os.path.exists(filename) else 'w'
        elif mode not in 'rw':
            raise ValueError('invalid mode: {!r}; expected r/w'.format(mode))
        self._mode = mode
        self._filename = filename
        self._handle = io.open(filename, mode + 'b')
        self._index = {}
        self._dirty = True
        atexit.register(self.close)
        if not self.writable:
            self._read_index()
        self._seek = 0

    @property
    def filename(self):
        return self._filename

    @property
    def mode(self):
        return self._mode

    @property
    def writable(self):
        return self._mode == 'w'

    @property
    def filesize(self):
        return os.stat(self._filename).st_size

    def read(self, key):
        self._check_handle()
        self._check_key(key)
        is_array, offset = self._index[key]
        self._handle.seek(offset)
        return (read_blosc if is_array else read_json)(self._handle)

    def write_json(self, key, data):
        self._write(key, data, 0, write_json)

    def write_array(self, key, data, compression='lz4', level=5, shuffle=True):
        self._write(key, data, 1, write_blosc, compression, level, shuffle)

    def close(self):
        if self._handle is not None:
            if self.writable:
                if self._dirty:
                    self._write_index()
                self._handle.flush()
            self._handle.close()
        self._handle = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _write(self, key, data, is_array, func, *args, **kwargs):
        self._check_handle(write=True)
        self._check_key(write=True)
        self._index[key] = [is_array, self._seek]
        self._handle.seek(self._seek)
        try:
            self._seek = func(self._handle, data, *args, **kwargs)
            self._dirty = True
        except:
            self._index.pop(key)
            six.reraise(*sys.exc_info())
        else:
            self._write_index()

    def _read_index(self):
        try:
            self._handle.seek(-8, os.SEEK_END)
            self._handle.seek(read_i64(self._handle))
            self._index = read_json(self._handle)
        except Exception as e:
            raise IOError('cannot read file ({}: {})'.format(type(e).__name__, str(e)))

    def _write_index(self):
        self._handle.truncate()
        write_json(self._handle, self._index)
        write_i64(self._handle, self._seek)
        self._dirty = False

    def _check_handle(self, write=False):
        if self._handle is None:
            raise IOError('the file handle has been closed')
        if write and not self.writable:
            raise IOError('the file is not writable')

    def _check_key(self, key, write=False):
        if not isinstance(key, six.string_types):
            raise ValueError('invalid key: expected string, got {}'.format(type(key).__name__))
        if write and key in self._index:
            raise ValueError('key already exists: {!r}'.format(key))
