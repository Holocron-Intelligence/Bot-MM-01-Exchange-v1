
import sys
from unittest.mock import MagicMock

# Mock pandas
mock_pd = MagicMock()
sys.modules["pandas"] = mock_pd

# Mock numpy
mock_np = MagicMock()
sys.modules["numpy"] = mock_np

# Mock indicators.core and implement the logic to be tested
def get_tr(df):
    high = df["high"]
    low = df["low"]
    close = df["close"]

    # Simulate high - low
    tr1 = high - low
    # Simulate (high - close.shift(1)).abs()
    tr2 = (high - close_shift_1).abs()
    # Simulate (low - close.shift(1)).abs()
    tr3 = (low - close_shift_1).abs()

    # We can't really run this without real numpy/pandas.
    # The goal is to show the redundant computation in the code.
    pass

def adx(df, period=14):
    high = df["high"]
    low = df["low"]
    close = df["close"]

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = mock_np.fmax(tr1, mock_np.fmax(tr2, tr3))
    # ...
    return tr

def atr(df, period=14):
    high = df["high"]
    low = df["low"]
    close = df["close"]

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = mock_np.fmax(tr1, mock_np.fmax(tr2, tr3))
    return tr

# Since I can't run real pandas, I'll just do a code analysis and manual verification.
# The redundancy is clear in src/indicators/core.py:
# adx() computes tr
# atr() computes tr
# compute_all() calls adx() and then calls atr()
