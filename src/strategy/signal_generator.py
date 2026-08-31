import os
import logging
import os
from src.strategy.volume_profile import VolumeProfile
from src.config import MAX_LOSS_PER_TRADE_USD, MAX_POSITIONS

logger = logging.getLogger(__name__)

class SignalGenerator:
    def __init__(self):
        self.active_positions = 0
        self.daily_pnl = 0.0
        # Hard stop limit modeled after Topstep risk controls
        self.daily_loss_limit = MAX_LOSS_PER_TRADE_USD * 3 

    def analyze_price_action(self, current_price, current_volume, volume_profile: VolumeProfile):
        """
        Analyzes the current price against the Volume Profile Supply/Demand zones (LVNs).
        If the price hits an LVN and volume spikes, we have a 'turn'.
        It also reads the latest AI Market Regime state to adjust or veto the trade.
        """
        if self.daily_pnl <= -self.daily_loss_limit:
            logger.warning("Daily Loss Limit hit. Trading halted.")
            return None

        if self.active_positions >= MAX_POSITIONS:
            return None
            
        # Read AI Risk State (0 ms latency)
        ai_state = "NEUTRAL"
        state_file = os.path.join(os.path.dirname(__file__), '..', '..', 'ai_sentiment_state.json')
        if os.path.exists(state_file):
            try:
                import json
                with open(state_file, "r") as f:
                    ai_state = json.load(f).get("regime", "NEUTRAL")
            except Exception:
                pass

        # Look for the nearest Low Volume Node (Support/Resistance)
        lvns = volume_profile.lvn
        if not lvns:
            return None

        # Logic: If price is near an LVN and volume is exceptionally high, trigger a reversal
        # We define 'near' as within 0.1% of the price level
        threshold = current_price * 0.001

        for lvn in lvns:
            if abs(current_price - lvn) <= threshold:
                # We are at a key level. Check volume.
                # Optimized Backtest Params: 1.2x Volume Spike
                if current_volume > volume_profile.df['volume'].mean() * 1.2:
                    # Reversal signal
                    # POC is the max volume node
                    poc = volume_profile.profile.loc[volume_profile.profile['volume'].idxmax(), 'price']
                    if current_price > poc:
                        # Resistance rejection -> Bearish
                        if ai_state == "BULLISH_AGGRESSIVE":
                            logger.info(f"AI VETO: Ignoring Bearish turn at {lvn:.2f} due to BULLISH macro news.")
                            return None
                        size = 4 if ai_state == "BEARISH_CAUTIOUS" else 1
                        logger.info(f"Rejection at LVN {lvn:.2f}. Bearish turn detected. AI Size: {size}")
                        return {"direction": "SELL", "size": size}
                    else:
                        # Support bounce -> Bullish
                        if ai_state == "BEARISH_CAUTIOUS":
                            logger.info(f"AI VETO: Ignoring Bullish turn at {lvn:.2f} due to BEARISH macro news.")
                            return None
                        size = 4 if ai_state == "BULLISH_AGGRESSIVE" else 1
                        logger.info(f"Bounce at LVN {lvn:.2f}. Bullish turn detected. AI Size: {size}")
                        return {"direction": "BUY", "size": size}

        return None

    def update_risk_metrics(self, active_count, daily_pnl):
        self.active_positions = active_count
        self.daily_pnl = daily_pnl
