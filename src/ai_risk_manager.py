import os
import sys
import time
import json
import logging
from datetime import datetime
from openai import OpenAI
from alpaca.data.historical.news import NewsClient
from alpaca.data.requests import NewsRequest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.config import ALPACA_API_KEY, ALPACA_SECRET_KEY, FEATHERLESS_API_KEY

logging.basicConfig(level=logging.INFO, format='%(asctime)s - AI_RISK - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

STATE_FILE = os.path.join(os.path.dirname(__file__), '..', 'ai_sentiment_state.json')

class AIRiskManager:
    def __init__(self):
        self.news_client = NewsClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)
        
        if not FEATHERLESS_API_KEY:
            logger.warning("FEATHERLESS_API_KEY not found. AI Risk Manager will default to NEUTRAL.")
            self.client = None
        else:
            # Featherless AI uses the standard OpenAI python SDK format
            self.client = OpenAI(
                base_url="https://api.featherless.ai/v1",
                api_key=FEATHERLESS_API_KEY
            )

    def fetch_latest_news(self, symbol="SPY", limit=5):
        try:
            req = NewsRequest(symbols=symbol, limit=limit)
            news_response = self.news_client.get_news(req)
            
            # In alpaca-py, the response has a data property or is a pydantic model containing dicts
            articles = getattr(news_response, 'news', [])
            if not articles and hasattr(news_response, 'data'):
                articles = news_response.data.get('news', [])
            
            headlines = []
            for n in articles:
                if isinstance(n, dict):
                    headline = n.get('headline', 'No Headline')
                    summary = n.get('summary', '')
                else:
                    headline = getattr(n, 'headline', 'No Headline')
                    summary = getattr(n, 'summary', '')
                headlines.append(f"- {headline} (Summary: {summary})")
                
            return "\n".join(headlines)
        except Exception as e:
            logger.error(f"Failed to fetch news: {e}")
            return ""

    def evaluate_sentiment(self, headlines: str) -> str:
        if not self.client:
            return "NEUTRAL"
        if not headlines:
            return "NEUTRAL"

        prompt = f"""
You are an expert quantitative risk manager for an algorithmic trading fund.
Your job is to analyze the following breaking market news for the SPY index and determine the immediate, short-term market regime.

Recent News:
{headlines}

Based on this news, output exactly ONE of the following three words describing the current market regime. Do not output anything else:
BULLISH_AGGRESSIVE (Market is clearly positive, allow max position sizing)
BEARISH_CAUTIOUS (Market is negative or highly uncertain, veto long trades or reduce size)
NEUTRAL (Market is normal, allow standard technical trading)
"""
        try:
            # Using an ungated open-source model available on Featherless
            response = self.client.chat.completions.create(
                model="mistralai/Mistral-7B-Instruct-v0.2",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=20
            )
            
            # Log the raw response so we can debug if needed
            logger.info(f"Raw LLM Response: {response}")
            
            content = ""
            if hasattr(response, 'choices') and response.choices:
                content = getattr(response.choices[0].message, 'content', '')
            elif isinstance(response, dict) and response.get('choices'):
                content = response['choices'][0].get('message', {}).get('content', '')
            else:
                content = str(response)
                
            decision = str(content).strip().upper()
                
            # Ensure it strictly matches our Enums
            if "BULLISH" in decision: return "BULLISH_AGGRESSIVE"
            if "BEARISH" in decision: return "BEARISH_CAUTIOUS"
            return "NEUTRAL"
            
        except Exception as e:
            logger.error(f"LLM evaluation failed: {e}")
            return "NEUTRAL"

    def write_state(self, sentiment: str):
        state = {
            "regime": sentiment,
            "last_updated": datetime.now().isoformat()
        }
        tmp_file = STATE_FILE + ".tmp"
        with open(tmp_file, "w") as f:
            json.dump(state, f)
        os.replace(tmp_file, STATE_FILE) # Atomic swap on POSIX
        logger.info(f"Updated AI Global Risk State to: {sentiment}")

    def run_daemon(self, interval_seconds=300):
        """Runs continuously in the background, updating the sentiment state."""
        logger.info("Starting Asynchronous AI Risk Manager Daemon...")
        while True:
            logger.info("Waking up to read latest macroeconomic data...")
            news_text = self.fetch_latest_news("SPY", limit=5)
            sentiment = self.evaluate_sentiment(news_text)
            self.write_state(sentiment)
            logger.info(f"Going back to sleep for {interval_seconds} seconds.")
            time.sleep(interval_seconds)

if __name__ == "__main__":
    manager = AIRiskManager()
    # Run once for testing
    news = manager.fetch_latest_news("SPY", limit=3)
    logger.info("Fetched News:\n" + news)
    sentiment = manager.evaluate_sentiment(news)
    manager.write_state(sentiment)
