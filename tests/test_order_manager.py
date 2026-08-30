import os
import sys

# Ensure src can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.execution.order_manager import OrderManager

def test_initialization_and_positions():
    print("Testing OrderManager initialization...")
    manager = OrderManager()
    
    print("Testing get_open_positions()...")
    positions = manager.get_open_positions()
    
    print("Successfully initialized OrderManager.")
    print(f"Fetched {len(positions)} open positions.")
    for p in positions:
        print(f"Position: {p.symbol} - {p.qty} shares")

if __name__ == "__main__":
    test_initialization_and_positions()
