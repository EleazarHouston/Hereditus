import random

import numpy as np
import pytest


@pytest.fixture
def seeded_rng():
    """Seed and restore the global RNGs used by the current model layer."""
    python_state = random.getstate()
    numpy_state = np.random.get_state()
    random.seed(0)
    np.random.seed(0)
    try:
        yield random.Random(0)
    finally:
        random.setstate(python_state)
        np.random.set_state(numpy_state)
