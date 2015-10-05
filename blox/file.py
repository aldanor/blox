# -*- coding: utf-8 -*-

from __future__ import absolute_import

import io
import os

from blox.blosc import write_blosc


class File(object):
    def __init__(self, filename, mode=None):
        filename = os.path.abspath(os.path.expanduser(filename))
        if mode is None:
            mode = 'r' if os.path.exists(filename) else 'w'
        elif mode not in 'rw':
            raise ValueError('invalid mode: {!r}; expected r/w'.format(mode))
        self._mode = mode
        self._filename = os.path.abspath(os.path.expanduser(filename))
        self._handle = io.open(filename, mode)
        self._offsets = {}

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

    def create_dataset(self, name, data, compression='lz4', level=5, shuffle=True):
        if not self.writable:
            raise ValueError('file is not writable')
        if name in self._offsets:
            raise ValueError('dataset {!r} already exists'.format(name))
        self._offsets[name] = self._handle.tell()
        write_blosc(data, self._handle, compression, level, shuffle)
