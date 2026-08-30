import pandas as pd
import numpy as np
from scipy.signal import find_peaks

class VolumeProfile:
    def __init__(self, df: pd.DataFrame, bins: int = 50):
        """
        Calculates High Volume Nodes (HVNs) and Low Volume Nodes (LVNs) from OHLCV data.
        df must contain 'Close' (or 'High', 'Low') and 'Volume' columns.
        """
        self.df = df
        self.bins = bins
        self.profile = pd.DataFrame()
        self.hvn = []
        self.lvn = []
        
    def calculate(self):
        # Use Typical Price if High and Low are present, else just Close
        if 'high' in self.df.columns and 'low' in self.df.columns and 'close' in self.df.columns:
            prices = (self.df['high'] + self.df['low'] + self.df['close']) / 3
        else:
            prices = self.df['close']
            
        volumes = self.df['volume']
        
        # Calculate volume profile histogram
        hist, bin_edges = np.histogram(prices, bins=self.bins, weights=volumes)
        
        # Calculate bin centers for the prices
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        self.profile = pd.DataFrame({
            'price': bin_centers,
            'volume': hist
        })
        
        # Find peaks (High Volume Nodes)
        hvn_indices, _ = find_peaks(hist, prominence=np.mean(hist)*0.1)
        self.hvn = self.profile.iloc[hvn_indices]['price'].tolist()
        
        # Find troughs (Low Volume Nodes) by inverting the histogram
        lvn_indices, _ = find_peaks(-hist, prominence=np.mean(hist)*0.1)
        self.lvn = self.profile.iloc[lvn_indices]['price'].tolist()
        
        return {
            'profile': self.profile,
            'hvn': self.hvn,
            'lvn': self.lvn
        }
