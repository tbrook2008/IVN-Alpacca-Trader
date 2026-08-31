import time
import logging
import sys
import os

# Add project root to path so 'src' can be resolved
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import src.config as config
from src.config import validate_config
from src.data.market_data import MarketDataFetcher
from src.strategy.volume_profile import VolumeProfile
from src.strategy.signal_generator import SignalGenerator
from src.execution.order_manager import OrderManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    validate_config()
    logger.info("Initializing IVN Alpaca Trading Agent...")

    # Initialize Modules
    data_fetcher = MarketDataFetcher()
    order_manager = OrderManager()
    signal_gen = SignalGenerator()
    
    # 1. Build Morning Profiles for all symbols
    logger.info("Fetching historical data for Volume Profiles...")
    profiles = {}
    for symbol in config.SYMBOLS:
        try:
            df = data_fetcher.fetch_historical_bars(symbol, days=5)
            profile = VolumeProfile(df)
            profile.calculate()
            profiles[symbol] = profile
            poc = profile.profile.loc[profile.profile['volume'].idxmax(), 'price']
            logger.info(f"[{symbol}] POC: {poc} | LVNs: {profile.lvn}")
        except Exception as e:
            logger.error(f"Failed to build profile for {symbol}: {e}")

    # 2. Main Trading Loop
    logger.info("Starting real-time monitoring loop for symbols: " + ", ".join(config.SYMBOLS))
    
    try:
        while True:
            for symbol in config.SYMBOLS:
                if symbol not in profiles: continue
                profile = profiles[symbol]
                latest_bar = data_fetcher.get_latest_bar(symbol)
                if latest_bar is None: continue
                
                current_price = latest_bar['close']
                current_volume = latest_bar['volume']

                # Update risk metrics from broker
                positions = order_manager.get_open_positions()
                account = order_manager.client.get_account() if hasattr(order_manager, 'client') else None
                buying_power = float(account.buying_power) if account else 100000.0
                
                signal_gen.update_risk_metrics(len(positions), 0.0)

                # Analyze for 'Turns'
                signal = signal_gen.analyze_price_action(current_price, current_volume, profile)
                
                if signal and isinstance(signal, dict):
                    direction = signal.get("direction")
                    size = signal.get("size", 1)
                    
                    # Check Buying Power
                    estimated_cost = current_price * size
                    if estimated_cost > buying_power * 0.9:
                        logger.warning(f"[{symbol}] Insufficient Buying Power. Required: ${estimated_cost:.2f}, Available: ${buying_power:.2f}. Halting trade.")
                        continue
                        
                    if direction == "BUY":
                        logger.info(f"[{symbol}] Executing Bullish Trades - Size: {size}")
                        # 1. Equity Trade (with Bracket OCO)
                        try:
                            from alpaca.trading.enums import OrderSide
                            order_manager.submit_market_order_equity(symbol, qty=size, side=OrderSide.BUY, current_price=current_price)
                        except Exception as e:
                            logger.error(f"Equity route failed: {e}")
                        # 2. Options Trade (Target ATM)
                        order_manager.execute_options_trade(symbol, "CALL", qty=size, current_underlying_price=current_price)
                        
                    elif direction == "SELL":
                        logger.info(f"[{symbol}] Executing Bearish Trades - Size: {size}")
                        # 1. Equity Short Trade (with Bracket OCO)
                        try:
                            from alpaca.trading.enums import OrderSide
                            order_manager.submit_market_order_equity(symbol, qty=size, side=OrderSide.SELL, current_price=current_price)
                        except Exception as e:
                            logger.error(f"Equity route failed: {e}")
                        # 2. Options Trade (Buy PUT to avoid naked shorts)
                        order_manager.execute_options_trade(symbol, "PUT", qty=size, current_underlying_price=current_price)
                
            # Sleep to prevent rate limit hitting on polling
            time.sleep(60)

    except KeyboardInterrupt:
        logger.info("Agent shutting down. Closing all positions to avoid overnight risk.")
        order_manager.close_all_positions()

if __name__ == "__main__":
    main()
