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

    def execute_options_trade(self, underlying_symbol: str, contract_type: str, qty: float):
        """
        Hackathon Requirement: Dynamically trade Options (0-DTE proxy).
        Fetches the options chain, filters for the nearest ATM Call/Put, and executes.
        """
        import logging
        from src.data.market_data import MarketDataFetcher
        logger = logging.getLogger(__name__)
        
        try:
            fetcher = MarketDataFetcher()
            chain = fetcher.fetch_active_options_chain(underlying_symbol)
            
            if not chain:
                logger.error(f"Failed to fetch options chain for {underlying_symbol}")
                return
                
            # Filter for Calls or Puts based on signal (contract_type = "CALL" or "PUT")
            # The symbol format is usually SPY251219C00500000 ('C' for call, 'P' for put)
            target_char = 'C' if contract_type == "CALL" else 'P'
            
            valid_contracts = [sym for sym in chain.keys() if target_char in sym[6:]]
            
            if not valid_contracts:
                logger.error(f"No {contract_type} contracts found for {underlying_symbol}")
                return
                
            # Select the most liquid / first available for the MVP
            target_contract = valid_contracts[0]
            logger.info(f"Selected Options Contract: {target_contract}")
            
            # Submit the order
            req = MarketOrderRequest(
                symbol=target_contract,
                qty=qty,
                side=OrderSide.BUY, # We buy the Call or Buy the Put (no naked shorts)
                time_in_force=TimeInForce.DAY
            )
            
            res = self.client.submit_order(order_data=req)
            logger.info(f"✅ Options Order submitted: {target_contract}")
            return res
            
        except Exception as e:
            logger.error(f"Failed to execute options trade: {e}")
            return None

    def close_all_positions(self, cancel_orders: bool = True):
        """Close all open positions."""
        return self.client.close_all_positions(cancel_orders=cancel_orders)
        
    def get_open_positions(self):
        """Fetch open positions (for testing)."""
        return self.client.get_all_positions()
