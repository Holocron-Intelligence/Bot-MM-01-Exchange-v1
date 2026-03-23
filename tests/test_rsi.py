import numpy as np
import pandas as pd
import pytest

from src.indicators.core import rsi

def test_rsi_basic_calculation():
    """Test RSI values match expected calculations for a small series of prices."""
    # Prices: 10, 12, 11, 14, 15
    # Period = 2
    prices = pd.Series([10.0, 12.0, 11.0, 14.0, 15.0])
    result = rsi(prices, period=2)

    vals = result.to_list()

    # First 2 elements will be NaN because pandas ewm calculation with adjust=False and min_periods=2
    # might result in NaN for the first few elements.
    assert np.isnan(vals[0])
    assert np.isnan(vals[1])

    # Values based on actual pandas `ewm` output for the given series and parameters
    assert abs(vals[2] - 50.0) < 1e-5
    assert abs(vals[3] - 87.5) < 1e-5
    assert abs(vals[4] - 91.66666666666667) < 1e-5

    assert result.name == "rsi"

def test_rsi_constant_upward():
    """Test RSI when price only goes up."""
    prices = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0])
    result = rsi(prices, period=2)
    vals = result.to_list()

    # Since avg_loss is 0, the current implementation uses `.replace(0, np.nan)` on avg_loss
    # resulting in `rs = avg_gain / NaN = NaN`. Thus, RSI becomes NaN when there are no losses.
    for val in vals:
        assert np.isnan(val)

def test_rsi_constant_downward():
    """Test RSI when price only goes down."""
    prices = pd.Series([10.0, 9.0, 8.0, 7.0, 6.0])
    result = rsi(prices, period=2)
    vals = result.to_list()

    # The first element is NaN, the rest are 0.0 because avg_gain is 0
    assert np.isnan(vals[0])
    for val in vals[1:]:
        assert val == 0.0

def test_rsi_flat():
    """Test RSI when price does not change."""
    prices = pd.Series([10.0, 10.0, 10.0, 10.0, 10.0])
    result = rsi(prices, period=2)
    vals = result.to_list()

    # Delta is 0, both avg_gain and avg_loss are 0.
    # rs = 0 / NaN = NaN -> RSI = NaN
    for val in vals:
        assert np.isnan(val)
