import sys
import json
import logging
from alpaca.trading.client import TradingClient
from src.config import ALPACA_API_KEY, ALPACA_SECRET_KEY, PAPER_TRADING

# Setup logging to stderr so stdout is strictly for JSON-RPC
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("mcp_server")

# Initialize Alpaca client
try:
    trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=PAPER_TRADING)
except Exception as e:
    logger.error(f"Failed to initialize Alpaca client: {e}")
    trading_client = None

def handle_request(request_str):
    try:
        request = json.loads(request_str)
    except json.JSONDecodeError:
        return {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None}

    req_id = request.get("id")
    method = request.get("method")
    
    if method == "get_account_balance":
        if not trading_client:
            return {"jsonrpc": "2.0", "error": {"code": -32603, "message": "Alpaca client not initialized"}, "id": req_id}
        try:
            account = trading_client.get_account()
            return {"jsonrpc": "2.0", "result": {"balance": str(account.cash), "equity": str(account.equity)}, "id": req_id}
        except Exception as e:
            return {"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}, "id": req_id}
            
    elif method == "get_active_positions":
        if not trading_client:
            return {"jsonrpc": "2.0", "error": {"code": -32603, "message": "Alpaca client not initialized"}, "id": req_id}
        try:
            positions = trading_client.get_all_positions()
            pos_list = [{"symbol": p.symbol, "qty": str(p.qty), "market_value": str(p.market_value)} for p in positions]
            return {"jsonrpc": "2.0", "result": {"positions": pos_list}, "id": req_id}
        except Exception as e:
            return {"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}, "id": req_id}
            
    else:
        return {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": req_id}

def main():
    logger.info("Starting MCP JSON-RPC Server...")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        response = handle_request(line)
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
