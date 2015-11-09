# -*- coding: utf-8 -*-

from __future__ import absolute_import

import io
import os
import sys
import six
import atexit

from blox.blosc import read_blosc, write_blosc
from blox.utils import read_i64, write_i64, read_json, write_json, restore_dtype


"""The following signature is a direct descendent of PNG and HDF5 file signatures:

- byte 1: non-ASCII value to reduce the probability that a text file may be
  misrecognized as a blox file; also, it catches bad file transfers that clear bit 7;
- bytes 2-4: format name;
- bytes 5-6: CR-LF sequence catches bad file transfers that alter newline sequences;
- byte 7: control-Z character stops file display under MS-DOS;
- byte 8: the final line feed checks for the inverse of the CR-LF translation problem.
"""
FORMAT_STRING = b'\211BLX\r\n\032\n'

"""Format version is stored as a little-endian integer in the 8 bytes following the initial
signature, and should only be increased if backwards-incompatible changes are introduced."""
FORMAT_VERSION = 1


def is_blox(filename):
    try:
        with open(os.path.abspath(os.path.expanduser(str(filename))), 'rb') as fd:
            return File._try_read_and_verify_version(fd) is not None
    except:
        return False


class File(object):
    def __init__(self, filename, mode=None):
        filename = getattr(filename, 'strpath', filename)
        filename = os.path.abspath(os.path.expanduser(filename))
        if mode is None:
            mode = 'r' if os.path.exists(filename) else 'r+'
        elif mode == 'w':
            mode = 'r+'
        elif mode not in ('r', 'r+'):
            raise ValueError('invalid mode: {!r}; expected r/r+/w'.format(mode))
        self._mode = mode
        if self.writable and not os.path.exists(filename):
            io.open(filename, 'wb').close()
        self._filename = filename
        self._handle = io.open(filename, 'r' + (self.writable * '+') + 'b')
        self._index = {}
        self._seek = 0
        self._version = FORMAT_VERSION
        atexit.register(self.close)
        if not self.writable:
            self._version = self._try_read_and_verify_version(self._handle)
            self._read_index()
        else:
            self._write_signature()
            self._write_index()
            self._handle.flush()

    @property
    def format_version(self):
        return self._version

    @property
    def filename(self):
        return self._filename

    @property
    def mode(self):
        return self._mode

    @property
    def writable(self):
        return self._mode == 'r+'

    @property
    def filesize(self):
        return os.stat(self._filename).st_size

    def info(self, key):
        self._check_handle()
        self._check_key(key)
        is_array, offset = self._index[key]
        self._handle.seek(offset)
        if is_array:
            meta = read_json(self._handle)
            return {
                'type': 'array',
                'shape': tuple(meta['shape']),
                'dtype': restore_dtype(meta['dtype']),
                'compression': tuple(meta['comp'])
            }
        else:
            return {'type': 'json'}

    def shape(self, key):
        return self.info(key).get('shape')

    def dtype(self, key):
        return self.info(key).get('dtype')

    def __iter__(self):
        return iter(sorted(self._index))

    def read(self, key, out=None):
        self._check_handle()
        self._check_key(key)
        is_array, offset = self._index[key]
        if not is_array and out is not None:
            raise ValueError('can only specify output for array values')
        self._handle.seek(offset)
        if is_array:
            return read_blosc(self._handle, out=out)
        else:
            return read_json(self._handle)

    def write_json(self, key, data):
        self._write(key, data, 0, write_json)

    def write_array(self, key, data, compression='lz4', level=5, shuffle=True):
        self._write(key, data, 1, write_blosc, compression, level, shuffle)

    def close(self):
        if self._handle is not None:
            if self.writable:
                self._handle.flush()
            self._handle.close()
        self._handle = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @classmethod
    def _try_read_and_verify_version(cls, byte_stream):
        if byte_stream.read(8) != FORMAT_STRING:
            raise IOError('unrecognized file format')
        try:
            version = read_i64(byte_stream)
        except:
            raise IOError('unable to read file version')
        if version != FORMAT_VERSION:  # this could be later relaxed to a range of versions
            raise IOError('incompatible version: {} (expected {})'.format(version, FORMAT_VERSION))
        return version

    def _write_signature(self):
        self._handle.seek(0)
        self._handle.write(FORMAT_STRING)
        write_i64(self._handle, FORMAT_VERSION)
        self._seek = 16

    def _write(self, key, data, is_array, func, *args, **kwargs):
        self._check_handle(write=True)
        self._check_key(key, write=True)
        self._index[key] = [is_array, self._seek]
        self._handle.seek(self._seek)
        try:
            self._seek += func(self._handle, data, *args, **kwargs)
        except:
            self._index.pop(key)
            self._write_index()
            six.reraise(*sys.exc_info())
        else:
            self._write_index()

    def _read_index(self):
        try:
            self._handle.seek(-8, os.SEEK_END)
            self._handle.seek(read_i64(self._handle))
            self._index = read_json(self._handle)
        except:
            raise IOError('unable to read index')

    def _write_index(self):
        self._handle.truncate()
        write_json(self._handle, self._index)
        write_i64(self._handle, self._seek)

    def _check_handle(self, write=False):
        if self._handle is None:
            raise IOError('the file handle has been closed')
        if write and not self.writable:
            raise IOError('the file is not writable')

    def _check_key(self, key, write=False):
        if not isinstance(key, six.string_types):
            raise ValueError('invalid key: expected string, got {}'.format(type(key).__name__))
        if write:
            if not key:
                raise ValueError('invalid key: empty string')
            if key in self._index:
                raise ValueError('key already exists: {!r}'.format(key))
