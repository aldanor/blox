# -*- coding: utf-8 -*-

import pytest

from blox.file import File


@pytest.yield_fixture
def tmpfile(request, tmpdir):
    filename = tmpdir.join('file.tmp').ensure().strpath
    File(filename, 'w').close()
    yield filename
