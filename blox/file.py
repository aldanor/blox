# -*- coding: utf-8 -*-

from __future__ import absolute_import

import io
import os
import atexit

from blox.utils import read_i64, write_i64, read_json, write_json
from blox.blosc import write_blosc


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

    def write_array(self, name, data, compression='lz4', level=5, shuffle=True):
        self._check_handle(write=True)
        if name in self._index:
            raise ValueError('dataset {!r} already exists'.format(name))
        self._index[name] = self._seek
        self._handle.seek(self._seek)
        self._dirty = True
        self._seek = write_blosc(data, self._handle, compression, level, shuffle)
        self._write_index()

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
