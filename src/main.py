import time
import logging
import sys
import os

# Add project root to path so 'src' can be resolved
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
    
    # 1. Build Morning Profile
    logger.info("Fetching historical data for Volume Profile...")
    df = data_fetcher.fetch_historical_bars("SPY", days_back=5)
    
    profile = VolumeProfile(df)
    result = profile.calculate()
    
    poc = profile.profile.loc[profile.profile['volume'].idxmax(), 'price']
    logger.info(f"Volume Profile POC: {poc}")
    logger.info(f"LVNs (Support/Resistance): {profile.lvn}")

    # 2. Main Trading Loop
    logger.info("Starting real-time monitoring loop...")
    
    try:
        while True:
            # In a real streaming scenario, this would be websocket driven.
            # For hackathon daemon, we simulate streaming by polling latest bar.
            latest_bar = data_fetcher.get_latest_bar("SPY")
            current_price = latest_bar['close']
            current_volume = latest_bar['volume']

            # Update risk metrics from broker
            positions = order_manager.get_open_positions()
            account = order_manager.client.get_account() if hasattr(order_manager, 'client') else None
            buying_power = float(account.buying_power) if account else 100000.0
            
            # daily_pnl logic here (simplified for demo)
            signal_gen.update_risk_metrics(len(positions), 0.0)

            # Analyze for 'Turns'
            signal = signal_gen.analyze_price_action(current_price, current_volume, profile)
            
            if signal:
                direction = signal["direction"]
                size = signal["size"]
                
                # Check Buying Power before routing order
                estimated_cost = current_price * size
                if estimated_cost > buying_power * 0.9:
                    logger.warning(f"Insufficient Buying Power. Required: ${estimated_cost:.2f}, Available: ${buying_power:.2f}. Halting trade.")
                    continue
                if direction == "BUY":
                    logger.info(f"Executing Bullish Equity Trade (Shares) - Size: {size}")
                    try:
                        from alpaca.trading.enums import OrderSide
                        order_manager.submit_market_order_equity("SPY", qty=size, side=OrderSide.BUY)
                        logger.info("✅ BUY Order successfully submitted to Alpaca.")
                    except Exception as e:
                        logger.error(f"Failed to route BUY order: {e}")
                    
                elif direction == "SELL":
                    logger.info(f"Executing Bearish Equity Trade (Shares) - Size: {size}")
                    try:
                        from alpaca.trading.enums import OrderSide
                        order_manager.submit_market_order_equity("SPY", qty=size, side=OrderSide.SELL)
                        logger.info("✅ SELL Order successfully submitted to Alpaca.")
                    except Exception as e:
                        logger.error(f"Failed to route SELL order: {e}")
            
            # Sleep to prevent rate limit hitting on polling
            time.sleep(60)

    except KeyboardInterrupt:
        logger.info("Agent shutting down. Closing all positions to avoid overnight risk.")
        order_manager.close_all_positions()

if __name__ == "__main__":
    main()
