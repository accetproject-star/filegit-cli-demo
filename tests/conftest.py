import pytest
from pathlib import Path
import tempfile

@pytest.fixture
def temp_repo():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)
