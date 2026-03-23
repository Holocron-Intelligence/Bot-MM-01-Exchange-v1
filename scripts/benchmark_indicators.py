
import pandas as pd
import numpy as np
import time
from src.indicators.core import adx, atr, compute_all

def generate_dummy_data(n=10000):
    np.random.seed(42)
    close = np.cumsum(np.random.randn(n)) + 100
    high = close + np.random.rand(n) * 2
    low = close - np.random.rand(n) * 2
    open_p = (high + low) / 2
    volume = np.random.rand(n) * 1000

    df = pd.DataFrame({
        "open": open_p,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume
    })
    return df

def benchmark():
    df = generate_dummy_data(100000)

    # Warm up
    _ = compute_all(df)

    start_time = time.perf_counter()
    for _ in range(10):
        _ = compute_all(df)
    end_time = time.perf_counter()

    avg_time = (end_time - start_time) / 10
    print(f"Average execution time for compute_all: {avg_time:.4f} seconds")

if __name__ == "__main__":
    benchmark()
