import os
import sys
import pandas as pd
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.config import validate_config
from src.data.market_data import MarketDataFetcher
from src.strategy.volume_profile import VolumeProfile
from src.strategy.signal_generator import SignalGenerator

def run_backtest(symbol="SPY", days_total=10, profile_lookback=5):
    print(f"--- Starting Backtest for {symbol} ---")
    print(f"Fetching {days_total} days of historical 1-minute data...")
    
    fetcher = MarketDataFetcher()
    # Fetch data (ensure we get enough days to train the profile and test)
    df = fetcher.fetch_historical_bars(symbol, days=days_total)
    
    if df.empty:
        print("Failed to fetch historical data.")
        return

    # Reset MultiIndex to make timestamp accessible
    df = df.reset_index(level=0, drop=True)
    # Convert index to dates
    df.index = pd.to_datetime(df.index)
    
    # We will simulate the strategy day by day
    # Get unique dates in the dataset
    unique_dates = pd.Series(df.index.date).unique()
    
    if len(unique_dates) <= profile_lookback:
        print("Not enough days of data to perform backtest. Try increasing days_total.")
        return

    total_pnl = 0.0
    winning_trades = 0
    losing_trades = 0

    print(f"\n--- Running Daily Simulations ---")
    for i in range(profile_lookback, len(unique_dates)):
        current_date = unique_dates[i]
        
        # 1. Build Morning Profile using previous `profile_lookback` days
        start_date = unique_dates[i - profile_lookback]
        end_date = unique_dates[i - 1]
        
        historical_slice = df.loc[str(start_date):str(end_date)]
        profile = VolumeProfile(historical_slice)
        profile.calculate()
        
        lvns = profile.lvn
        poc = profile.profile.loc[profile.profile['volume'].idxmax(), 'price'] if not profile.profile.empty else 0
        
        print(f"\n[{current_date}] Profile Built. POC: {poc:.2f}, LVNs: {len(lvns)}")
        
        # 2. Simulate the trading day
        day_data = df.loc[str(current_date)]
        signal_gen = SignalGenerator()
        
        position = 0 # 1 for Long, -1 for Short
        entry_price = 0.0
        daily_pnl = 0.0
        
        for index, row in day_data.iterrows():
            current_price = row['close']
            current_volume = row['volume']
            
            # If we have an open position, we manage it
            if position != 0:
                # Simplistic take profit / stop loss (1% move)
                unrealized = (current_price - entry_price) * position
                if unrealized > current_price * 0.001:  # 0.5% take profit
                    daily_pnl += unrealized
                    print(f"   [{index.time()}] Take Profit hit. PnL: +${unrealized:.2f}")
                    if unrealized > 0: winning_trades += 1
                    else: losing_trades += 1
                    position = 0
                elif unrealized < -current_price * 0.002: # 0.2% stop loss
                    daily_pnl += unrealized
                    print(f"   [{index.time()}] Stop Loss hit. PnL: -${abs(unrealized):.2f}")
                    losing_trades += 1
                    position = 0
                continue # Skip looking for new signals while in position
            
            # Look for signals
            signal = signal_gen.analyze_price_action(current_price, current_volume, profile)
            
            if signal and signal.get("direction") == "BUY":
                position = 1
                entry_price = current_price
                print(f"   [{index.time()}] BUY Signal at {entry_price:.2f}")
            elif signal and signal.get("direction") == "SELL":
                position = -1
                entry_price = current_price
                print(f"   [{index.time()}] SELL Signal at {entry_price:.2f}")

        # End of day flat closing
        if position != 0:
            final_price = day_data.iloc[-1]['close']
            unrealized = (final_price - entry_price) * position
            daily_pnl += unrealized
            if unrealized > 0: winning_trades += 1
            else: losing_trades += 1
            print(f"   [15:59:00] End of day close. PnL: ${unrealized:.2f}")
            
        print(f"   Daily PnL: ${daily_pnl:.2f}")
        total_pnl += daily_pnl

    print(f"\n--- Backtest Complete ---")
    print(f"Total PnL (Equity): ${total_pnl:.2f}")
    print(f"Total Trades: {winning_trades + losing_trades}")
    if (winning_trades + losing_trades) > 0:
        print(f"Win Rate: {(winning_trades / (winning_trades + losing_trades)) * 100:.1f}%")

if __name__ == "__main__":
    validate_config()
    # Run backtest for the last 15 days
    run_backtest(symbol="SPY", days_total=15, profile_lookback=5)
