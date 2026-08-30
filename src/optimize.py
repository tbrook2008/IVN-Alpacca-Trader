import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.config import validate_config
from src.data.market_data import MarketDataFetcher
from src.strategy.volume_profile import VolumeProfile

def run_simulation(df, profile_lookback, vol_mult, price_thresh, is_options=False):
    unique_dates = pd.Series(df.index.date).unique()
    if len(unique_dates) <= profile_lookback:
        return 0.0, 0, 0

    total_pnl = 0.0
    winning_trades = 0
    losing_trades = 0

    # For options proxy: Assume 0-DTE ATM options. Delta ~ 0.50. Leverage ~ 100x.
    # 1 Option Contract controls 100 shares. 
    # If SPY moves $1, Option moves $0.50. Total PnL = $50.
    shares_per_trade = 100
    option_delta = 0.50

    for i in range(profile_lookback, len(unique_dates)):
        current_date = unique_dates[i]
        start_date = unique_dates[i - profile_lookback]
        end_date = unique_dates[i - 1]
        
        historical_slice = df.loc[str(start_date):str(end_date)]
        if historical_slice.empty:
            continue
            
        profile = VolumeProfile(historical_slice)
        profile.calculate()
        lvns = profile.lvn
        if not lvns:
            continue
            
        avg_1min_vol = historical_slice['volume'].mean()
        poc = profile.profile.loc[profile.profile['volume'].idxmax(), 'price'] if not profile.profile.empty else 0
        
        day_data = df.loc[str(current_date)]
        
        # Synthetic AI State for Backtesting (Proxying LLM macro sentiment)
        # If today's open is > POC, we simulate a BULLISH AI macro sentiment. If below, BEARISH.
        day_open = day_data.iloc[0]['open']
        ai_state = "BULLISH_AGGRESSIVE" if day_open > poc else "BEARISH_CAUTIOUS"
        
        position = 0 
        entry_price = 0.0
        trade_size = 1
        
        for index, row in day_data.iterrows():
            current_price = row['close']
            current_volume = row['volume']
            
            if position != 0:
                price_diff = (current_price - entry_price) * position
                # Take profit: 0.1% on underlying (High win rate scalping)
                if price_diff > current_price * 0.001:
                    pnl = price_diff * shares_per_trade * trade_size
                    if is_options: pnl *= option_delta
                    total_pnl += pnl
                    winning_trades += 1
                    position = 0
                # Stop loss: 0.2% on underlying (Breathing room for trades)
                elif price_diff < -current_price * 0.002:
                    pnl = price_diff * shares_per_trade * trade_size
                    if is_options: pnl *= option_delta
                    total_pnl += pnl
                    losing_trades += 1
                    position = 0
                continue
            
            # Signal Logic
            threshold_val = current_price * price_thresh
            for lvn in lvns:
                if abs(current_price - lvn) <= threshold_val:
                    if current_volume > avg_1min_vol * vol_mult:
                        if current_price > poc:
                            # Resistance rejection -> Bearish
                            if ai_state == "BULLISH_AGGRESSIVE": continue # AI Veto
                            position = -1 # SELL (Put)
                            trade_size = 4 if ai_state == "BEARISH_CAUTIOUS" else 1
                            entry_price = current_price
                        else:
                            # Support bounce -> Bullish
                            if ai_state == "BEARISH_CAUTIOUS": continue # AI Veto
                            position = 1 # BUY (Call)
                            trade_size = 4 if ai_state == "BULLISH_AGGRESSIVE" else 1
                            entry_price = current_price
                        break

        # Close at EOD
        if position != 0:
            final_price = day_data.iloc[-1]['close']
            price_diff = (final_price - entry_price) * position
            pnl = price_diff * shares_per_trade
            if is_options: pnl *= option_delta
            total_pnl += pnl
            if price_diff > 0: winning_trades += 1
            else: losing_trades += 1

    return total_pnl, winning_trades, losing_trades

def optimize():
    print("--- Starting Multi-Symbol Backtest Scanner ---")
    fetcher = MarketDataFetcher()
    
    symbols = ['AAPL', 'NVDA', 'IWM', 'SPY']
    vol_mult = 1.2
    price_thresh = 0.001
    
    results = []
    
    for symbol in symbols:
        print(f"\nEvaluating {symbol}...")
        df = fetcher.fetch_historical_bars(symbol, days=730) 
        if df.empty:
            print(f"Failed to fetch data for {symbol}.")
            continue

        df = df.reset_index(level=0, drop=True)
        df.index = pd.to_datetime(df.index)
        
        unique_dates = pd.Series(df.index.date).unique()
        if len(unique_dates) < 10:
            continue
            
        print(f"Loaded {len(unique_dates)} days of data for {symbol}.")
        
        # Run test
        eq_pnl, eq_wins, eq_losses = run_simulation(df, 5, vol_mult, price_thresh, is_options=False)
        total_eq = eq_wins + eq_losses
        win_rate = (eq_wins/total_eq*100) if total_eq > 0 else 0
        
        print(f"{symbol} -> PnL: ${eq_pnl:.2f}, Trades: {total_eq}, WinRate: {win_rate:.1f}%")
        
        if win_rate >= 60.0 and total_eq > 10:
            results.append(symbol)
            
    print("\n=========================================")
    print(f"✅ HIGHLY PROFITABLE SYMBOLS (Win Rate > 60%):")
    print(results)
    print("=========================================")

if __name__ == "__main__":
    validate_config()
    optimize()
