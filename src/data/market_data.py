from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, OptionChainRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
import src.config as config

class MarketDataFetcher:
    def __init__(self):
        self.stock_client = StockHistoricalDataClient(config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY)
        self.option_client = OptionHistoricalDataClient(config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY)

    def fetch_historical_bars(self, symbol: str, days: int = 5):
        """Fetch 1-minute historical bars for a given symbol for the past N days."""
        # Free tier requires at least 15 min delay
        end_time = datetime.utcnow() - timedelta(minutes=20)
        start_time = end_time - timedelta(days=days)
        
        request_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Minute,
            start=start_time,
            end=end_time
        )
        
        bars = self.stock_client.get_stock_bars(request_params)
        return bars.df

    def fetch_active_options_chain(self, underlying_symbol: str):
        """Fetch the active options chain for a given underlying symbol to find near-the-money 0-DTE contracts."""
        request_params = OptionChainRequest(
            underlying_symbol=underlying_symbol
        )
        
        # Depending on alpaca-py version, getting the active options chain:
        chain = self.option_client.get_option_chain(request_params)
        return chain

    def get_latest_bar(self, symbol: str):
        """Fetch the most recent 1-minute historical bar."""
        # Free tier requires at least 15 min delay
        end_time = datetime.utcnow() - timedelta(minutes=16)
        start_time = end_time - timedelta(minutes=30)
        
        request_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Minute,
            start=start_time,
            end=end_time,
            limit=1
        )
        try:
            bars = self.stock_client.get_stock_bars(request_params)
            df = bars.df
            if not df.empty:
                latest = df.iloc[-1]
                return {
                    'close': float(latest['close']),
                    'volume': int(latest['volume'])
                }
        except Exception:
            pass
        return None
