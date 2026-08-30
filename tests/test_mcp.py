import sys
import os
import json
from unittest.mock import MagicMock

# Ensure we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import src.mcp_server as mcp_server

def test_handle_request_balance():
    # Mock trading client
    mock_client = MagicMock()
    mock_account = MagicMock()
    mock_account.cash = "10000.00"
    mock_account.equity = "10000.00"
    mock_client.get_account.return_value = mock_account
    
    mcp_server.trading_client = mock_client
    
    req = {"jsonrpc": "2.0", "method": "get_account_balance", "id": 1}
    res = mcp_server.handle_request(json.dumps(req))
    
    assert res["id"] == 1
    assert "result" in res
    assert res["result"]["balance"] == "10000.00"
    print("test_handle_request_balance passed")

def test_handle_request_positions():
    mock_client = MagicMock()
    mock_position = MagicMock()
    mock_position.symbol = "AAPL"
    mock_position.qty = "10"
    mock_position.market_value = "1500.00"
    mock_client.get_all_positions.return_value = [mock_position]
    
    mcp_server.trading_client = mock_client
    
    req = {"jsonrpc": "2.0", "method": "get_active_positions", "id": 2}
    res = mcp_server.handle_request(json.dumps(req))
    
    assert res["id"] == 2
    assert "result" in res
    assert len(res["result"]["positions"]) == 1
    assert res["result"]["positions"][0]["symbol"] == "AAPL"
    print("test_handle_request_positions passed")

if __name__ == "__main__":
    test_handle_request_balance()
    test_handle_request_positions()
    print("All tests passed.")
