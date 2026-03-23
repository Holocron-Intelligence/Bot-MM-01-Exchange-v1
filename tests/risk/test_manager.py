import pytest
from src.risk.manager import compute_stop_loss

@pytest.mark.parametrize("entry_price, side, atr_value, regime, expected", [
    (100.0, "BUY", 2.0, "range", 100.0 - (2.0 * 1.5)), # mult_range=1.5 -> 97.0
    (100.0, "SELL", 2.0, "range", 100.0 + (2.0 * 1.5)), # mult_range=1.5 -> 103.0
    (100.0, "BUY", 2.0, "trend", 100.0 - (2.0 * 2.5)), # mult_trend=2.5 -> 95.0
    (100.0, "SELL", 2.0, "trend", 100.0 + (2.0 * 2.5)), # mult_trend=2.5 -> 105.0
    (100.0, "BUY", 0.0, "range", 100.0), # zero ATR -> 100.0
    (0.0, "BUY", 2.0, "range", 0.0 - (2.0 * 1.5)), # zero entry -> -3.0
])
def test_compute_stop_loss_basic(entry_price, side, atr_value, regime, expected):
    """Test standard parameters and basic combinations."""
    sl = compute_stop_loss(
        entry_price=entry_price,
        side=side,
        atr_value=atr_value,
        regime=regime
    )
    assert sl == expected

def test_compute_stop_loss_custom_multipliers():
    """Test that custom multipliers are respected."""
    # BUY, custom range multiplier
    sl1 = compute_stop_loss(
        entry_price=100.0,
        side="BUY",
        atr_value=2.0,
        stop_mult_range=1.0, # custom
        regime="range"
    )
    assert sl1 == 98.0 # 100 - (2.0 * 1.0)

    # SELL, custom trend multiplier
    sl2 = compute_stop_loss(
        entry_price=100.0,
        side="SELL",
        atr_value=2.0,
        stop_mult_trend=3.0, # custom
        regime="trend"
    )
    assert sl2 == 106.0 # 100 + (2.0 * 3.0)

def test_compute_stop_loss_default_regime():
    """Test that default regime is range."""
    # Not passing regime parameter
    sl = compute_stop_loss(
        entry_price=100.0,
        side="BUY",
        atr_value=2.0
    )
    # Default is "range", mult=1.5
    assert sl == 100.0 - (2.0 * 1.5)
