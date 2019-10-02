import os

import pytest

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    client = app.test_client()
    yield client


def test_cli_raw2periodik():
    from app.command import raw2periodic
    from app import db
    from app.models import Raw, Device

    r1 = Raw.query.order_by(Raw.id.desc()).first()
    assert 'device' in r1.content
    raw2periodic(r1.content)
