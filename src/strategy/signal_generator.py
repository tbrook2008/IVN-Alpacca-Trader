import logging
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
        """
        if self.daily_pnl <= -self.daily_loss_limit:
            logger.warning("Daily Loss Limit hit. Trading halted.")
            return None

        if self.active_positions >= MAX_POSITIONS:
            return None

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
                # Assuming 'current_volume' is the 1-minute volume. If it's over a certain spike threshold:
                if current_volume > volume_profile.profile['volume'].mean() * 2:
                    # Reversal signal
                    # POC is the max volume node
                    poc = volume_profile.profile.loc[volume_profile.profile['volume'].idxmax(), 'price']
                    if current_price > poc:
                        # Resistance rejection -> Bearish
                        logger.info(f"Rejection at LVN {lvn:.2f}. Bearish turn detected.")
                        return "SELL"
                    else:
                        # Support bounce -> Bullish
                        logger.info(f"Bounce at LVN {lvn:.2f}. Bullish turn detected.")
                        return "BUY"

        return None

    def update_risk_metrics(self, active_count, daily_pnl):
        self.active_positions = active_count
        self.daily_pnl = daily_pnl
