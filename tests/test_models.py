import datetime
import pytest
from app.models import Periodik


def test_temukan_hujan():
    tg = datetime.datetime(2018, 11, 1, 7, 0)
    Periodik.temukan_hujan(tg)
