import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.market_data import MarketDataFetcher

def test_fetchers():
    fetcher = MarketDataFetcher()
    
    print("Fetching SPY historical bars for past 5 days...")
    bars = fetcher.fetch_historical_bars("SPY", days=5)
    print(f"Got {len(bars)} bars.")
    if len(bars) > 0:
        print(bars.head(2))
    
    print("\nFetching active options chain for SPY...")
    try:
        chain = fetcher.fetch_active_options_chain("SPY")
        print(f"Success. Type of response: {type(chain)}")
        # chain is an OptionChain object or dict of snapshots
        print("Example data:")
        if isinstance(chain, dict):
            keys = list(chain.keys())
            print(f"Number of contracts: {len(keys)}")
            if keys:
                print(f"First contract: {keys[0]}, Data: {chain[keys[0]]}")
        else:
            print(chain)
    except Exception as e:
        print(f"Error fetching options chain: {e}")

if __name__ == "__main__":
    test_fetchers()
