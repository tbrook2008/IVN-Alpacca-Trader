import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
FEATHERLESS_API_KEY = os.getenv("FEATHERLESS_API_KEY")

# Paper Trading Mode
PAPER_TRADING = os.getenv("PAPER_TRADING", "True").lower() in ("true", "1", "yes")
BASE_URL = "https://paper-api.alpaca.markets" if PAPER_TRADING else "https://api.alpaca.markets"

# Trading Constants
SYMBOLS = [sym.strip() for sym in os.getenv("SYMBOLS", "SPY,QQQ").split(",")]
MAX_LOSS_PER_TRADE_USD = float(os.getenv("MAX_LOSS_PER_TRADE_USD", "500"))
MAX_POSITIONS = int(os.getenv("MAX_POSITIONS", "2"))

def validate_config():
    if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
        raise ValueError("Missing Alpaca API Keys in environment variables.")
