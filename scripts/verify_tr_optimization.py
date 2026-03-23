
import sys
from unittest.mock import MagicMock, patch

# Mock pandas and numpy before importing the module under test
mock_pd = MagicMock()
mock_np = MagicMock()

sys.modules["pandas"] = mock_pd
sys.modules["numpy"] = mock_np

# Mock the Series and DataFrame classes
mock_pd.Series = MagicMock
mock_pd.DataFrame = MagicMock

# Now we can import the functions from the module
import src.indicators.core as core

def test_true_range_called_by_adx_when_tr_is_none():
    df = MagicMock()
    with patch('src.indicators.core.true_range') as mock_tr_func:
        try:
            core.adx(df, period=14, tr=None)
        except:
            pass
        mock_tr_func.assert_called_once_with(df)

def test_true_range_not_called_by_adx_when_tr_is_provided():
    df = MagicMock()
    tr = MagicMock()
    with patch('src.indicators.core.true_range') as mock_tr_func:
        try:
            core.adx(df, period=14, tr=tr)
        except:
            pass
        mock_tr_func.assert_not_called()

def test_true_range_called_by_atr_when_tr_is_none():
    df = MagicMock()
    with patch('src.indicators.core.true_range') as mock_tr_func:
        try:
            core.atr(df, period=14, tr=None)
        except:
            pass
        mock_tr_func.assert_called_once_with(df)

def test_true_range_not_called_by_atr_when_tr_is_provided():
    df = MagicMock()
    tr = MagicMock()
    with patch('src.indicators.core.true_range') as mock_tr_func:
        try:
            core.atr(df, period=14, tr=tr)
        except:
            pass
        mock_tr_func.assert_not_called()

def test_compute_all_calls_true_range_once():
    df = MagicMock()
    df.copy.return_value = df
    mock_pd.concat.return_value = df

    with patch('src.indicators.core.true_range') as mock_tr_func:
        with patch('src.indicators.core.vwap'), \
             patch('src.indicators.core.vwap_distance'), \
             patch('src.indicators.core.rsi'), \
             patch('src.indicators.core.adx'), \
             patch('src.indicators.core.atr'), \
             patch('src.indicators.core.momentum'), \
             patch('src.indicators.core.realized_volatility'), \
             patch('src.indicators.core.cvd'), \
             patch('src.indicators.core.detect_divergence'), \
             patch('src.indicators.core.oi_change_signal'):

             core.compute_all(df)
             mock_tr_func.assert_called_once_with(df)

if __name__ == "__main__":
    try:
        test_true_range_called_by_adx_when_tr_is_none()
        print("✓ test_true_range_called_by_adx_when_tr_is_none passed")
        test_true_range_not_called_by_adx_when_tr_is_provided()
        print("✓ test_true_range_not_called_by_adx_when_tr_is_provided passed")
        test_true_range_called_by_atr_when_tr_is_none()
        print("✓ test_true_range_called_by_atr_when_tr_is_none passed")
        test_true_range_not_called_by_atr_when_tr_is_provided()
        print("✓ test_true_range_not_called_by_atr_when_tr_is_provided passed")
        test_compute_all_calls_true_range_once()
        print("✓ test_compute_all_calls_true_range_once passed")
        print("\nAll verification tests passed!")
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ An error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
