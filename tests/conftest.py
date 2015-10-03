# -*- coding: utf-8 -*-

import pytest


@pytest.yield_fixture
def tmpfile(request, tmpdir):
    yield tmpdir.join('file.tmp').ensure().strpath
