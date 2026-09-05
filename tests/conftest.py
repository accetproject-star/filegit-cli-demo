import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_repo():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)
