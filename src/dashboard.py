import streamlit as st
import pandas as pd
import json
import os
import sys

# Add project root to path so 'src' can be resolved
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from alpaca.trading.client import TradingClient
from src.config import ALPACA_API_KEY, ALPACA_SECRET_KEY, PAPER_TRADING

# Initialize Alpaca Client
trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=PAPER_TRADING)

def load_ai_sentiment():
    # Assuming dashboard.py is in src/ and ai_sentiment_state.json is in the root directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, "ai_sentiment_state.json")
    
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return {"regime": "UNKNOWN", "last_updated": "N/A"}

def main():
    st.set_page_config(page_title="IVN Autonomous AI Agent", layout="wide", page_icon="🤖")
    
    st.title("🤖 IVN Autonomous AI Agent")
    st.markdown("---")

    # Sidebar for AI Risk State
    st.sidebar.header("🧠 AI Risk State")
    sentiment = load_ai_sentiment()
    
    regime = sentiment.get("regime", "UNKNOWN")
    last_updated = sentiment.get("last_updated", "N/A")
    
    st.sidebar.metric(label="Current Regime", value=regime)
    st.sidebar.caption(f"Last Updated: {last_updated}")
    
    if regime == "BULLISH":
        st.sidebar.success("🟢 Risk-On Mode Active")
    elif regime == "BEARISH":
        st.sidebar.error("🔴 Risk-Off / Hedging Active")
    else:
        st.sidebar.warning("🟡 Neutral Stance")

    st.subheader("💼 Account Overview")
    
    try:
        account = trading_client.get_account()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Portfolio Value", f"${float(account.portfolio_value):,.2f}")
        with col2:
            st.metric("Cash", f"${float(account.cash):,.2f}")
        with col3:
            st.metric("Buying Power", f"${float(account.buying_power):,.2f}")
        with col4:
            st.metric("Daytrade Count", account.daytrade_count)
            
    except Exception as e:
        st.error(f"Failed to fetch account info: {e}")
        
    st.markdown("---")
    st.subheader("📊 Open Positions")
    
    try:
        positions = trading_client.get_all_positions()
        if not positions:
            st.info("No open positions at the moment.")
        else:
            pos_data = []
            for pos in positions:
                pos_data.append({
                    "Symbol": pos.symbol,
                    "Side": pos.side,
                    "Qty": float(pos.qty),
                    "Market Value": f"${float(pos.market_value):,.2f}",
                    "Unrealized P/L": f"${float(pos.unrealized_pl):,.2f}",
                    "Unrealized P/L %": f"{float(pos.unrealized_plpc)*100:.2f}%",
                    "Current Price": f"${float(pos.current_price):,.2f}",
                    "Avg Entry": f"${float(pos.avg_entry_price):,.2f}"
                })
            st.dataframe(pos_data, use_container_width=True)
    except Exception as e:
        st.error(f"Failed to fetch positions: {e}")

if __name__ == "__main__":
    main()
