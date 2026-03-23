import pytest
from src.strategy.grid import AdaptiveGrid, GridState, GridLevel

def test_generate_basic_grid():
    grid = AdaptiveGrid(num_levels=3, spacing_atr_mult=0.5)

    mid_price = 100.0
    atr_value = 2.0

    state = grid.generate(mid_price=mid_price, atr_value=atr_value, base_size=1.0)

    assert isinstance(state, GridState)
    assert len(state.levels) == 6  # 3 buy, 3 sell
    assert state.mid_price == 100.0
    assert state.spacing == 1.0  # 2.0 * 0.5

    buy_levels = state.buy_levels
    sell_levels = state.sell_levels

    assert len(buy_levels) == 3
    assert len(sell_levels) == 3

    # Check prices (spacing is 1.0, so buys are 99, 98, 97, sells are 101, 102, 103)
    buy_prices = [l.price for l in buy_levels]
    assert 99.0 in buy_prices
    assert 98.0 in buy_prices
    assert 97.0 in buy_prices

    sell_prices = [l.price for l in sell_levels]
    assert 101.0 in sell_prices
    assert 102.0 in sell_prices
    assert 103.0 in sell_prices

def test_generate_zero_spacing_fallback():
    grid = AdaptiveGrid(num_levels=2)

    mid_price = 100.0
    atr_value = 0.0  # Should trigger fallback

    state = grid.generate(mid_price=mid_price, atr_value=atr_value)

    # Fallback spacing is mid_price * 0.001 = 0.1
    assert state.spacing == 0.1

    buy_prices = [l.price for l in state.buy_levels]
    assert 99.9 in buy_prices
    assert 99.8 in buy_prices

def test_generate_positive_bias():
    grid = AdaptiveGrid(num_levels=1)

    # Positive bias -> increase BUY sizes, decrease SELL sizes
    state = grid.generate(mid_price=100.0, atr_value=2.0, bias_score=1.0, base_size=1.0)

    buy_size = state.buy_levels[0].size
    sell_size = state.sell_levels[0].size

    assert buy_size > 1.0
    assert sell_size < 1.0

def test_generate_negative_bias():
    grid = AdaptiveGrid(num_levels=1)

    # Negative bias -> decrease BUY sizes, increase SELL sizes
    state = grid.generate(mid_price=100.0, atr_value=2.0, bias_score=-1.0, base_size=1.0)

    buy_size = state.buy_levels[0].size
    sell_size = state.sell_levels[0].size

    assert buy_size < 1.0
    assert sell_size > 1.0

def test_generate_trend_regime_amplifies_bias():
    grid = AdaptiveGrid(num_levels=1)

    # Range regime
    range_state = grid.generate(
        mid_price=100.0, atr_value=2.0, bias_score=1.0,
        base_size=1.0, regime="range"
    )

    # Trend regime
    trend_state = grid.generate(
        mid_price=100.0, atr_value=2.0, bias_score=1.0,
        base_size=1.0, regime="trend"
    )

    # Trend should amplify bias -> even larger buy, even smaller sell
    assert trend_state.buy_levels[0].size > range_state.buy_levels[0].size
    assert trend_state.sell_levels[0].size < range_state.sell_levels[0].size

def test_distance_decay():
    grid = AdaptiveGrid(num_levels=3)

    state = grid.generate(mid_price=100.0, atr_value=2.0, base_size=1.0)

    # Buy prices are 97, 98, 99. Index 0 is 97 (farthest), 1 is 98, 2 is 99 (closest)
    # The actual order in buy_levels depends on sorting.
    # Grid state sorts all levels by price.
    # So buy_levels will have prices [97.0, 98.0, 99.0].
    # Level 1 (closest) is 99.0, Level 2 is 98.0, Level 3 (farthest) is 97.0
    # Decay means farthest (Level 3) has smallest size.

    buy_99 = next(l for l in state.buy_levels if l.price == 99.0)
    buy_98 = next(l for l in state.buy_levels if l.price == 98.0)
    buy_97 = next(l for l in state.buy_levels if l.price == 97.0)

    assert buy_99.size > buy_98.size
    assert buy_98.size > buy_97.size

def test_needs_rebalance():
    grid = AdaptiveGrid(num_levels=1, spacing_atr_mult=1.0, rebalance_threshold=0.5)

    # No grid yet -> needs rebalance
    assert grid.needs_rebalance(current_price=100.0) is True

    grid.generate(mid_price=100.0, atr_value=2.0)
    # Spacing is 2.0. Threshold is 0.5 * 2.0 = 1.0

    # Price moved slightly -> no rebalance
    assert grid.needs_rebalance(current_price=100.5) is False

    # Price moved past threshold -> needs rebalance
    assert grid.needs_rebalance(current_price=101.1) is True
    assert grid.needs_rebalance(current_price=98.9) is True

def test_grid_state_properties():
    state = GridState(
        levels=[
            GridLevel(price=99.0, side="BUY", size=1.0, order_id=1, is_filled=True),
            GridLevel(price=98.0, side="BUY", size=1.0, order_id=2, is_filled=False),
            GridLevel(price=101.0, side="SELL", size=1.0, order_id=None, is_filled=False),
        ]
    )

    assert len(state.buy_levels) == 2
    assert len(state.sell_levels) == 1
    assert len(state.open_orders) == 1
    assert state.open_orders[0].order_id == 2
    assert len(state.filled_orders) == 1
    assert state.filled_orders[0].order_id == 1
