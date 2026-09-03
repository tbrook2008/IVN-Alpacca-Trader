from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, TakeProfitRequest, StopLossRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
from src.config import ALPACA_API_KEY, ALPACA_SECRET_KEY, PAPER_TRADING
import logging

logger = logging.getLogger(__name__)

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

    def submit_market_order_equity(self, symbol: str, qty: float, side: OrderSide = OrderSide.BUY, current_price: float = None):
        """Submit a market order for an equity with Bracket (Take Profit / Stop Loss)."""
        if current_price is None:
            # Fallback to standard market order without brackets if price is unknown
            req = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=side,
                time_in_force=TimeInForce.DAY
            )
        else:
            # High win-rate scalp parameters: 0.1% TP, 0.2% SL
            tp_price = current_price * 1.001 if side == OrderSide.BUY else current_price * 0.999
            sl_price = current_price * 0.998 if side == OrderSide.BUY else current_price * 1.002
            
            req = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=side,
                time_in_force=TimeInForce.DAY,
                order_class=OrderClass.BRACKET,
                take_profit=TakeProfitRequest(limit_price=round(tp_price, 2)),
                stop_loss=StopLossRequest(stop_price=round(sl_price, 2))
            )
        return self.client.submit_order(order_data=req)

    def execute_options_trade(self, underlying_symbol: str, contract_type: str, qty: float, current_underlying_price: float):
        """
        Hackathon Requirement: Dynamically trade Options (0-DTE proxy).
        Fetches the options chain, filters for the nearest ATM Call/Put, and executes.
        """
        from src.data.market_data import MarketDataFetcher
        
        try:
            fetcher = MarketDataFetcher()
            chain = fetcher.fetch_active_options_chain(underlying_symbol)
            
            if not chain:
                logger.error(f"Failed to fetch options chain for {underlying_symbol}")
                return
                
            # Filter for Calls or Puts based on signal (contract_type = "CALL" or "PUT")
            target_char = 'C' if contract_type == "CALL" else 'P'
            valid_contracts = [sym for sym in chain.keys() if target_char in sym[6:]]
            
            if not valid_contracts:
                logger.error(f"No {contract_type} contracts found for {underlying_symbol}")
                return
                
            # Target ATM Options: Extract strike price from the symbol
            # Symbol format: SPY251219C00500000 -> Strike is the last 8 digits divided by 1000
            atm_contract = None
            min_diff = float('inf')
            
            for sym in valid_contracts:
                try:
                    strike_str = sym[-8:]
                    strike_price = float(strike_str) / 1000.0
                    diff = abs(strike_price - current_underlying_price)
                    if diff < min_diff:
                        min_diff = diff
                        atm_contract = sym
                except Exception:
                    continue
            
            if not atm_contract:
                atm_contract = valid_contracts[0]
                
            logger.info(f"Selected ATM Options Contract: {atm_contract} (Underlying: {current_underlying_price})")
            
            # We buy the Call or Buy the Put (no naked shorts)
            # High win-rate scalp parameters: we need an estimated premium to set TP/SL
            # Since we use MarketOrders, we will set a wider TP/SL on options or just use the underlying price proxy if we don't have the quote.
            # Actually, without the option's current quote, brackets on the option price are hard to calculate accurately.
            # Let's fetch the latest quote for the option to set the brackets!
            try:
                # Alpaca-py options snapshot
                from alpaca.data.requests import OptionSnapshotRequest
                from alpaca.data.historical.option import OptionHistoricalDataClient
                opt_client = OptionHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)
                snap_req = OptionSnapshotRequest(symbol_or_symbols=atm_contract)
                snap = opt_client.get_option_snapshot(snap_req)
                
                # Get the latest bid/ask midpoint
                if atm_contract in snap and snap[atm_contract].latest_quote:
                    opt_quote = snap[atm_contract].latest_quote
                    opt_price = (opt_quote.ask_price + opt_quote.bid_price) / 2
                else:
                    opt_price = 1.0 # fallback
                    
            except Exception as e:
                logger.warning(f"Could not get option quote, using fallback price: {e}")
                opt_price = 1.0
                
            # Options are more volatile, so we use 10% TP, 20% SL as a proxy for the 0.1% underlying move
            tp_price = opt_price * 1.10
            sl_price = opt_price * 0.80
            
            req = MarketOrderRequest(
                symbol=atm_contract,
                qty=qty,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY,
                order_class=OrderClass.BRACKET,
                take_profit=TakeProfitRequest(limit_price=round(tp_price, 2)),
                stop_loss=StopLossRequest(stop_price=round(sl_price, 2))
            )
            
            res = self.client.submit_order(order_data=req)
            logger.info(f"✅ Options Bracket Order submitted: {atm_contract}")
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
