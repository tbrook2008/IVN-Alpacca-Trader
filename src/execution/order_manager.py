from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from src.config import ALPACA_API_KEY, ALPACA_SECRET_KEY, PAPER_TRADING

class OrderManager:
    def __init__(self):
        self.client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=PAPER_TRADING)

    def submit_limit_order_options(self, symbol: str, qty: float, limit_price: float, side: OrderSide = OrderSide.BUY):
        """Submit a limit order for an options contract."""
        req = LimitOrderRequest(
            symbol=symbol,
            qty=qty,
            side=side,
            time_in_force=TimeInForce.DAY,
            limit_price=limit_price
        )
        return self.client.submit_order(order_data=req)

    def submit_market_order_equity(self, symbol: str, qty: float, side: OrderSide = OrderSide.BUY):
        """Submit a market order for an equity."""
        req = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=side,
            time_in_force=TimeInForce.DAY
        )
        return self.client.submit_order(order_data=req)

    def close_all_positions(self, cancel_orders: bool = True):
        """Close all open positions."""
        return self.client.close_all_positions(cancel_orders=cancel_orders)
        
    def get_open_positions(self):
        """Fetch open positions (for testing)."""
        return self.client.get_all_positions()
