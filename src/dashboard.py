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
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, "ai_sentiment_state.json")
    
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return {"regime": "UNKNOWN", "last_updated": "N/A"}

def set_custom_css():
    st.markdown("""
        <style>
            /* Institutional Dark Theme / Glassmorphism */
            .stApp {
                background-color: #0d1117;
                color: #c9d1d9;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            }
            .css-1d391kg {
                background-color: #161b22;
                border-right: 1px solid #30363d;
            }
            /* Cards */
            div[data-testid="stMetricValue"] {
                font-size: 2rem !important;
                font-weight: 600;
                color: #58a6ff;
            }
            div[data-testid="stMetricLabel"] {
                color: #8b949e;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            /* Dataframes */
            .stDataFrame {
                border: 1px solid #30363d;
                border-radius: 8px;
                overflow: hidden;
            }
            /* Headers */
            h1, h2, h3 {
                color: #c9d1d9 !important;
                font-weight: 600 !important;
            }
            hr {
                border-color: #30363d !important;
            }
        </style>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="IVN Quantum Swarm", layout="wide", page_icon="⚡")
    set_custom_css()
    
    st.title("⚡ IVN Quantum Swarm Terminal")
    st.markdown("---")

    # Sidebar for AI Risk State
    st.sidebar.title("🧠 Neural Core")
    sentiment = load_ai_sentiment()
    
    regime = sentiment.get("regime", "UNKNOWN")
    last_updated = sentiment.get("last_updated", "N/A")
    
    st.sidebar.metric(label="Market Regime", value=regime)
    st.sidebar.caption(f"Last Synced: {last_updated}")
    
    if regime == "BULLISH_AGGRESSIVE":
        st.sidebar.success("🟢 RISK ON (Max Leverage)")
    elif regime == "BEARISH_CAUTIOUS":
        st.sidebar.error("🔴 RISK OFF (Hedging)")
    else:
        st.sidebar.warning("🟡 NEUTRAL (Scalping)")

    st.subheader("💼 Portfolio Matrix")
    
    try:
        account = trading_client.get_account()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Net Liq", f"${float(account.portfolio_value):,.2f}")
        with col2:
            st.metric("Cash Reserve", f"${float(account.cash):,.2f}")
        with col3:
            st.metric("Buying Power", f"${float(account.buying_power):,.2f}")
        with col4:
            st.metric("Daytrade Count", account.daytrade_count)
            
    except Exception as e:
        st.error(f"Failed to fetch account info: {e}")
        
    st.markdown("---")
    st.subheader("📊 Active Vectors")
    
    try:
        positions = trading_client.get_all_positions()
        if not positions:
            st.info("No active vectors. Swarm is standing by.")
        else:
            pos_data = []
            for pos in positions:
                pos_data.append({
                    "Symbol": pos.symbol,
                    "Side": pos.side.upper(),
                    "Qty": float(pos.qty),
                    "Notional": f"${float(pos.market_value):,.2f}",
                    "Unrealized P/L": f"${float(pos.unrealized_pl):,.2f}",
                    "P/L %": f"{float(pos.unrealized_plpc)*100:.2f}%",
                    "Spot Price": f"${float(pos.current_price):,.2f}",
                    "Avg Entry": f"${float(pos.avg_entry_price):,.2f}"
                })
            st.dataframe(pos_data, use_container_width=True)
    except Exception as e:
        st.error(f"Failed to fetch positions: {e}")

if __name__ == "__main__":
    main()
