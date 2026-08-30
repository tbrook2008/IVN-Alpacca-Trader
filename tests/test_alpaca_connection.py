import os
import sys
from dotenv import load_dotenv

# Add src to path so we can import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src import config

from alpaca.trading.client import TradingClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.requests import OptionSnapshotRequest

def test_connection():
    print("Testing Alpaca Connection...")
    config.validate_config()
    
    # Initialize clients
    trading_client = TradingClient(config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY, paper=config.PAPER_TRADING)
    data_client = OptionHistoricalDataClient(config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY)
    
    # 1. Get Account
    try:
        account = trading_client.get_account()
        print(f"✅ Successfully connected to Alpaca!")
        print(f"   Account Status: {account.status}")
        print(f"   Buying Power: ${account.buying_power}")
        print(f"   Portfolio Value: ${account.portfolio_value}")
    except Exception as e:
        print(f"❌ Failed to get account: {e}")
        return

    print("\n✅ API Keys verified. Ready to proceed to next steps.")

if __name__ == "__main__":
    test_connection()
