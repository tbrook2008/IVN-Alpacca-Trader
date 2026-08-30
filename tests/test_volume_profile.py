import pandas as pd
import numpy as np
import sys
import os

# Add src to path to import strategy modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from strategy.volume_profile import VolumeProfile

def generate_dummy_data(n=1000):
    np.random.seed(42)
    base_price = 100
    price_changes = np.random.normal(0, 0.5, n)
    close = base_price + np.cumsum(price_changes)
    high = close + np.random.uniform(0, 0.5, n)
    low = close - np.random.uniform(0, 0.5, n)
    volume = np.random.randint(100, 1000, n)
    
    return pd.DataFrame({
        'High': high,
        'Low': low,
        'Close': close,
        'Volume': volume
    })

if __name__ == "__main__":
    print("Generating dummy data...")
    df = generate_dummy_data(1000)
    
    print("Calculating Volume Profile...")
    vp = VolumeProfile(df, bins=50)
    result = vp.calculate()
    
    print(f"High Volume Nodes (HVNs): {result['hvn']}")
    print(f"Low Volume Nodes (LVNs): {result['lvn']}")
    
    print("\nTest completed successfully.")
