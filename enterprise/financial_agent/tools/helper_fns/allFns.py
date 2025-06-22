import os
import json


from enterprise.financial_agent.tools.FinancialApi import FinancialModelingPrepAPI
from enterprise.financial_agent.tools.gpt import GPTAnalysisEngine

from pydantic import BaseModel, Field
from enterprise.financial_agent.tools.scrapers.crawl import CrawlScraper
from enterprise.financial_agent.tools.redis.redis_cache import RedisCache

fmp = FinancialModelingPrepAPI()
gpt_engine = GPTAnalysisEngine()

def get_fmp_detail(ticker: str):
    import datetime
    cache = RedisCache()
    key=ticker+"_API_data"

    # Check if data is cached
    cached_data = cache.get_cache(key)
    use_cache=False
    if cached_data:
        balance_sheet_date = cached_data["balance_sheet"].get("date")
        if balance_sheet_date and (datetime.datetime.now() - datetime.datetime.strptime(balance_sheet_date, "%Y-%m-%d")).days <= 365:
            use_cache=True

    # Fetch data from API
    company_profile = fmp.get_company_profile(ticker)
    price_data = fmp.get_historical_stock_data(ticker)

    if use_cache:
        financial_metrics=cached_data["financial_metrics"]
        income_statement=cached_data["income_statement"]
        balance_sheet=cached_data["balance_sheet"]
        cash_flow=cached_data["cash_flow"]
        print("Used Cache")
    else:
        financial_metrics = fmp.get_key_metrics(ticker)[0]
        income_statement = fmp.get_income_statement(ticker)[0]
        balance_sheet = fmp.get_balance_sheet(ticker)[0]
        cash_flow = fmp.get_cash_flow_statement(ticker)[0]
        print("Fetched from API")

        data_to_cache = {
            "financial_metrics": financial_metrics,
            "income_statement": income_statement,
            "balance_sheet": balance_sheet,
            "cash_flow": cash_flow
        }

        cache.set_cache(key, data_to_cache, expiry_time=60*60*24*90)
        print("Data Cached")


    data = {
        "company_profile": company_profile,
        "price_data": price_data,
        "financial_metrics": financial_metrics,
        "income_statement": income_statement,
        "balance_sheet": balance_sheet,
        "cash_flow": cash_flow
    }

    return data


def get_company_overview(company_profile):
    try:
        return {
            "name": company_profile.get("companyName", None),
            "sector": company_profile.get("sector", None),
            "industry": company_profile.get("industry", None),
            "current_stock_price": company_profile.get("price", None),
            "image": company_profile.get("image", None)
        }
    except Exception as e:
        print(f"Error in get_company_overview: {e}")
        return None


def market_indicies_data():
    try:
        class USMarketIndex(BaseModel):
            name: str = Field(..., description="Name of the US market index (Dow Jones, NASDAQ Composite, or S&P 500).")
            last: float = Field(..., description="Last recorded value of the index.")
            change: float = Field(..., description="Change in the index value.")
            change_percent: str = Field(..., description="Percentage change in the index.")

        class MarketIndicesList(BaseModel):
            indices: list[USMarketIndex]            

        Crawller = CrawlScraper()
        instruction = """From the crawled content, extract only the following US market indices and their respective details:
                        - Dow Jones Industrial Average
                        - NASDAQ Composite Index
                        - S&P 500 Index
                        Extract the Name, Last recorded value, Change, and Percentage Change accurately."""
        result = Crawller.run("https://www.slickcharts.com/sp500", MarketIndicesList, instruction, markdown=True)
        result = json.loads(result) if isinstance(result, str) else result
        indices = []
        if isinstance(result, list):
            for idx in result:
                indices.append({
                    "name": idx.get("name", None),
                    "last": idx.get("last", None),
                    "change": idx.get("change", None),
                    "change_percent": idx.get("change_percent", None)
                })
        elif isinstance(result, dict):
            indices.append({
                "name": result.get("name", None),
                "last": result.get("last", None),
                "change": result.get("change", None),
                "change_percent": result.get("change_percent", None)
            })
        return indices
    except Exception as e:
        print(f"Error in market_indicies_data: {e}")
        return None


def analyst_stock_forecast(ticker: str):
    try:
        """
        Scrapes stock forecast data from StockAnalysis.com for a given ticker.

        Extracts:
        - Price targets (low, average, median, high) with percentage changes.
        - Analyst ratings for the past 6 months, including Strong Buy, Buy, Hold, Sell, and Strong Sell.
        - Current analyst consensus rating.
        - Financial forecast (revenue, EPS, growth rates, forward P/E).
        - Long-term revenue and EPS projections (high, average, low).

        Parameters:
            ticker (str): Stock ticker symbol (e.g., "AAPL").

        Returns:
            dict: Structured JSON with price targets, analyst ratings, financial forecasts, 
                  revenue projections, and EPS estimates.
        """
        class PriceTargets(BaseModel):
            low: float = Field(..., description="Lowest price target.")
            average: float = Field(..., description="Average price target.")
            median: float = Field(..., description="Median price target.")
            high: float = Field(..., description="Highest price target.")
            low_change: str = Field(..., description="Percentage change for the lowest target.")
            average_change: str = Field(..., description="Percentage change for the average target.")
            median_change: str = Field(..., description="Percentage change for the median target.")
            high_change: str = Field(..., description="Percentage change for the highest target.")

        class MonthlyRatings(BaseModel):
            month: str = Field(..., description="Month and year of the rating (e.g., Oct '24).")
            strong_buy: int = Field(..., description="Number of Strong Buy ratings.")
            buy: int = Field(..., description="Number of Buy ratings.")
            hold: int = Field(..., description="Number of Hold ratings.")
            sell: int = Field(..., description="Number of Sell ratings.")
            strong_sell: int = Field(..., description="Number of Strong Sell ratings.")
            total_analysts: int = Field(..., description="Total number of analysts providing ratings.")

        class AnalystRatings(BaseModel):
            current_analyst_consensus: str = Field(..., description="Overall latest analyst consensus (e.g., Buy, Hold, Sell).")
            months: list[MonthlyRatings]

        class FinancialForecast(BaseModel):
            revenue_this_year: float = Field(..., description="Revenue forecast for this year.")
            revenue_next_year: float = Field(..., description="Revenue forecast for next year.")
            revenue_growth_this_year: float = Field(..., description="Percentage change in revenue this year.")
            revenue_growth_next_year: float = Field(..., description="Percentage change in revenue next year.")
            eps_this_year: float = Field(..., description="Earnings per share (EPS) forecast for this year.")
            eps_next_year: float = Field(..., description="Earnings per share (EPS) forecast for next year.")
            eps_growth_this_year: float = Field(..., description="Percentage change in EPS this year.")
            eps_growth_next_year: float = Field(..., description="Percentage change in EPS next year.")
            forward_pe: float = Field(..., description="Forward P/E ratio for the stock.")

        class RevenueForecast(BaseModel):
            revenue_high: dict = Field(..., description="Revenue high estimates for future years.")
            revenue_avg: dict = Field(..., description="Revenue average estimates for future years.")
            revenue_low: dict = Field(..., description="Revenue low estimates for future years.")
            revenue_growth_high: dict = Field(..., description="Revenue growth high estimates for future years.")
            revenue_growth_avg: dict = Field(..., description="Revenue growth average estimates for future years.")
            revenue_growth_low: dict = Field(..., description="Revenue growth low estimates for future years.")

        class EPSForecast(BaseModel):
            eps_high: dict = Field(..., description="EPS high estimates for future years.")
            eps_avg: dict = Field(..., description="EPS average estimates for future years.")
            eps_low: dict = Field(..., description="EPS low estimates for future years.")
            eps_growth_high: dict = Field(..., description="EPS growth high estimates for future years.")
            eps_growth_avg: dict = Field(..., description="EPS growth average estimates for future years.")
            eps_growth_low: dict = Field(..., description="EPS growth low estimates for future years.")
            
        class StockForecast(BaseModel):
            price_targets: PriceTargets
            analyst_ratings: AnalystRatings
            financial_forecast: FinancialForecast
            revenue_forecast: RevenueForecast
            eps_forecast: EPSForecast

        Crawller = CrawlScraper()
        url = f"https://stockanalysis.com/stocks/{ticker}/forecast/"

        instruction = """Extract the following data:
        
        **1. Price Targets**:
        - Low, Average, Median, High price targets.
        - Corresponding percentage changes.

        **2. Analyst Ratings**:
        - Strong Buy, Buy, Hold, Sell, Strong Sell ratings for the past 6 months.
        - Total analysts.

        **3. Financial Forecast**:
        - Revenue this year and next year with percentage growth from last year to this year and percentage growth from this year to next year.
        - EPS this year and next year with percentage growth.
        - Forward P/E ratio.

        **4. Revenue Forecast (Yearly projections)**:
        - Revenue estimates for future years (High, Avg, Low).
        - Revenue growth estimates for future years.

        **5. EPS Forecast (Yearly projections)**:
        - EPS estimates for future years (High, Avg, Low).
        - EPS growth estimates for future years.

        Ensure the data is accurately extracted and structured properly."""

        result = Crawller.run(url, StockForecast, instruction, markdown=True)

        # Ensure proper JSON structure
        structured_result = json.loads(result) if isinstance(result, str) else result
        if isinstance(structured_result, list):
            if len(structured_result) > 0:
                structured_result = structured_result[0]
            else :
                structured_result = {}

        try:
            ff = structured_result.get("financial_forecast", {})
            rf = structured_result.get("revenue_forecast", {})
            pt = structured_result.get("price_targets", {})
            analyst_ratings= structured_result.get("analyst_ratings", {})


            # Map revenue to this year, next year, next to next year
            revenue_this_year = None
            revenue_next_year = None
            revenue_next_to_next_year = None
            if rf and "revenue_avg" in rf and isinstance(rf["revenue_avg"], dict):
                years = sorted(rf["revenue_avg"].keys())
                if len(years) >= 3:
                    revenue_this_year = rf["revenue_avg"].get(years[0])
                    revenue_next_year = rf["revenue_avg"].get(years[1])
                    revenue_next_to_next_year = rf["revenue_avg"].get(years[2])
                elif len(years) == 2:
                    revenue_this_year = rf["revenue_avg"].get(years[0])
                    revenue_next_year = rf["revenue_avg"].get(years[1])
                elif len(years) == 1:
                    revenue_this_year = rf["revenue_avg"].get(years[0])

            # Get % growth from financial_forecast, not calculated
            revenue_growth_this_year = ff.get("revenue_growth_this_year") if ff else None
            revenue_growth_next_year = ff.get("revenue_growth_next_year") if ff else None

            # EPS this year and next year
            eps_this_year = ff.get("eps_this_year") if ff else None
            eps_next_year = ff.get("eps_next_year") if ff else None
            eps_growth_this_year = ff.get("eps_growth_this_year") if ff else None
            eps_growth_next_year = ff.get("eps_growth_next_year") if ff else None

            # Price targets
            price_targets = {
                "low": pt.get("low") if pt else None,
                "average": pt.get("average") if pt else None,
                "median": pt.get("median") if pt else None,
                "high": pt.get("high") if pt else None,
                "low_change": pt.get("low_change") if pt else None,
                "average_change": pt.get("average_change") if pt else None,
                "median_change": pt.get("median_change") if pt else None,
                "high_change": pt.get("high_change") if pt else None,
            }

            return {
                "revenue_this_year": revenue_this_year,
                "revenue_next_year": revenue_next_year,
                "revenue_next_to_next_year": revenue_next_to_next_year,
                "revenue_growth_this_year_pct": revenue_growth_this_year,
                "revenue_growth_next_year_pct": revenue_growth_next_year,
                "eps_this_year": eps_this_year,
                "eps_next_year": eps_next_year,
                "eps_growth_this_year_pct": eps_growth_this_year,
                "eps_growth_next_year_pct": eps_growth_next_year,
                "price_targets": price_targets,
                "analyst_ratings": analyst_ratings
            }
        except Exception as e:
            print(f"Error extracting fields in analyst_stock_forecast: {e}")
            return {
                "revenue_this_year": None,
                "revenue_next_year": None,
                "revenue_next_to_next_year": None,
                "revenue_growth_this_year_pct": None,
                "revenue_growth_next_year_pct": None,
                "eps_this_year": None,
                "eps_next_year": None,
                "eps_growth_this_year_pct": None,
                "eps_growth_next_year_pct": None,
                "price_targets": None
            }
    except Exception as e:
        print(f"Error in analyst_stock_forecast: {e}")
        return {
            "revenue_this_year": None,
            "revenue_next_year": None,
            "revenue_next_to_next_year": None,
            "revenue_growth_this_year_pct": None,
            "revenue_growth_next_year_pct": None,
            "eps_this_year": None,
            "eps_next_year": None,
            "eps_growth_this_year_pct": None,
            "eps_growth_next_year_pct": None,
            "price_targets": None
        }


def fear_and_greed():
    import datetime
    try:
        import requests

        def fetch_fear_greed_data(date: str):
            url = f"https://production.dataviz.cnn.io/index/fearandgreed/graphdata/{date}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Referer": "https://edition.cnn.com/markets/fear-and-greed",
                "Accept-Language": "en-US,en;q=0.9"
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 418:
                print("Blocked by bot detection. Try using a proxy or different headers.")
            return None
        # Get today's and yesterday's date in YYYY-MM-DD format
        today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        yesterday = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        data = fetch_fear_greed_data(today) or fetch_fear_greed_data(yesterday)
        if not data or "fear_and_greed" not in data:
            print("Error in fear_and_greed: Failed to retrieve Fear & Greed Index data.")
            return {
                "current_index": None,
                "past_week_index": None,
                "past_month_index": None,
                "past_year_index": None
            }
        fg = data["fear_and_greed"]
        return {
            "current_index": fg.get("score"),
            "past_week_index": fg.get("previous_1_week"),
            "past_month_index": fg.get("previous_1_month"),
            "past_year_index": fg.get("previous_1_year")
        }
    except Exception as e:
        print(f"Error in fear_and_greed: {e}")
        return {
            "current_index": None,
            "past_week_index": None,
            "past_month_index": None,
            "past_year_index": None
        }


def cot_report():
    """
    Scrapes the Commitment of Traders (COT) data from Tradingster and Market Bulls.

    Returns:
        dict: { "cot_insights": <string or None> }
    """
    # --- COT Report Pydantic Models (top-level) ---
    class LegacyFutures(BaseModel):
        open_interest: int = Field(..., description="Total open interest for the asset.")
        change_in_open_interest: int = Field(..., description="Change in open interest.")
        non_commercial_long: int = Field(..., description="Non-commercial traders holding long positions.")
        non_commercial_short: int = Field(..., description="Non-commercial traders holding short positions.")
        commercial_long: int = Field(..., description="Commercial traders holding long positions.")
        commercial_short: int = Field(..., description="Commercial traders holding short positions.")
        total_long: int = Field(..., description="Total long positions (Commercial + Non-Commercial).")
        total_short: int = Field(..., description="Total short positions (Commercial + Non-Commercial).")
        non_reportable_long: int = Field(..., description="Non-reportable traders' long positions.")
        non_reportable_short: int = Field(..., description="Non-reportable traders' short positions.")
        percent_open_interest: dict = Field(..., description="Percentage of open interest by category.")
        traders_count: dict = Field(..., description="Number of traders in each category.")

    class COTMarketBulls(BaseModel):
        date: str = Field(..., description="Date of the COT report.")
        commercial_long: int = Field(..., description="Long positions held by commercial traders.")
        commercial_short: int = Field(..., description="Short positions held by commercial traders.")
        large_speculators_long: int = Field(..., description="Long positions held by large speculators.")
        large_speculators_short: int = Field(..., description="Short positions held by large speculators.")
        small_traders_long: int = Field(..., description="Long positions held by small traders.")
        small_traders_short: int = Field(..., description="Short positions held by small traders.")
        net_positions: int = Field(..., description="Net positions (Long - Short).")
        percent_open_interest: dict = Field(..., description="Percentage of open interest by category.")
        trader_sentiment: dict = Field(..., description="Trader sentiment for different trader categories.")


    Crawller = CrawlScraper()

    tradingster_url = "https://www.tradingster.com/cot/legacy-futures/20974"
    market_bulls_url = "http://market-bulls.com/cot-report-nasdaq-100/"

    instruction_tradingster = """Extract the following data from Tradingster's COT Legacy Futures Report:
    - Open Interest & Change in Open Interest.
    - Long, Short, Spread positions for Non-Commercial, Commercial, Total, and Non-Reportable Traders.
    - Percentage of Open Interest for each category.
    - Number of Traders in each category."""

    instruction_market_bulls = """Extract the following data from Market Bulls' Nasdaq 100 COT Report:
    - Commercial, Large Speculators, and Small Traders positions.
    - Net Positions & Percentage of Open Interest.
    - Sentiment analysis based on trader categories:
        - Dealer Intermediary, Asset Manager, Leveraged Funds, Other Reportables, Non-Reportable Traders.
    """

    try:
        result_tradingster = Crawller.run(tradingster_url, LegacyFutures, instruction_tradingster)
        print(f"COT Tradingster Data (raw): {result_tradingster}")
        if isinstance(result_tradingster, list):
            if len(result_tradingster) > 0 and isinstance(result_tradingster[0], dict):
                result_tradingster = result_tradingster[0]
            else:
                result_tradingster = {}
        result_market_bulls = Crawller.run(market_bulls_url, COTMarketBulls, instruction_market_bulls, markdown=True)
        print(f"COT Market Bulls Data (raw): {result_market_bulls}")
        if isinstance(result_market_bulls, list):
            if len(result_market_bulls) > 0 and isinstance(result_market_bulls[0], dict):
                result_market_bulls = result_market_bulls[0]
            else:
                result_market_bulls = {}
        tradingster = result_tradingster
        market_bulls = result_market_bulls
        cot_data = {
            "tradingster_cot_report": tradingster,
            "market_bulls_cot_report": market_bulls
        }

        prompt = (
            "Based on the following Commitment of Traders (COT) data, generate a concise, actionable insight (max 500 words) "
            "summarizing the current market sentiment, key trader positioning, and any notable shifts or risks. "
            "Focus on what the data means for market direction and trader behavior. "
            "Do not repeat the raw data, but synthesize the implications for investors and traders."
        )

        cot_insights = None
        try:
            cot_insights = gpt_engine.generate_analysis(prompt=prompt, data=cot_data)
        except Exception as e:
            print(f"Error in cot_report insights generation: {e}")
            cot_insights = None

        return {"cot_insights": cot_insights}
    except Exception as e:
        print(f"Error in cot_report: {e}")
        return {"cot_insights": None}

def put_call_ratios(ticker: str):
    """
    Scrapes option chain data from OptionCharts.io for a given stock ticker.

    Extracts:
    - **Implied Volatility Data**:
      - 30-day IV, IV Rank, IV Percentile, Historical Volatility, IV High/Low.
    - **Open Interest Data**:
      - Today's Open Interest, Put-Call Ratio, Put Open Interest, Call Open Interest, 30-day Open Interest Average.
    - **Option Volume Data**:
      - Today's Volume, Put-Call Ratio, Put Volume, Call Volume, 30-day Volume Average.
    
    Parameters:
        ticker (str): Stock ticker symbol (e.g., "AAPL").

    Returns:
        dict: JSON with extracted option chain data.
    """

    class OptionChainData(BaseModel):
        # Implied Volatility
        option_overview: str = Field(..., description="Option Overview")
        implied_volatility_30d: float = Field(..., description="30-day Implied Volatility (%)")
        iv_rank: float = Field(..., description="IV Rank")
        iv_percentile: float = Field(..., description="IV Percentile (%)")
        historical_volatility: float = Field(..., description="Historical Volatility (%)")
        iv_high: float = Field(..., description="Highest IV recorded (%)")
        iv_high_date: str = Field(..., description="Date of highest IV recorded")
        iv_low: float = Field(..., description="Lowest IV recorded (%)")
        iv_low_date: str = Field(..., description="Date of lowest IV recorded")

        # Open Interest
        open_interest_today: int = Field(..., description="Total Open Interest for today")
        put_call_open_interest_ratio: float = Field(..., description="Put/Call Open Interest Ratio")
        put_open_interest: int = Field(..., description="Total Put Open Interest")
        call_open_interest: int = Field(..., description="Total Call Open Interest")
        open_interest_avg_30d: int = Field(..., description="30-day Average Open Interest")
        open_interest_vs_30d_avg: float = Field(..., description="Today's Open Interest as % of 30-day Average")

        # Option Volume
        volume_today: int = Field(..., description="Total Option Volume for today")
        put_call_volume_ratio: float = Field(..., description="Put/Call Volume Ratio")
        put_volume: int = Field(..., description="Total Put Option Volume")
        call_volume: int = Field(..., description="Total Call Option Volume")
        volume_avg_30d: int = Field(..., description="30-day Average Volume")
        volume_vs_30d_avg: float = Field(..., description="Today's Volume as % of 30-day Average")

    Crawller = CrawlScraper()
    url = f"https://optioncharts.io/options/{ticker}"

    instruction = """Extract the following data from the page:
    
    1. **Implied Volatility Data**:
       - 30-day Implied Volatility (%)
       - IV Rank
       - IV Percentile (%)
       - Historical Volatility (%)
       - IV High (Value & Date)
       - IV Low (Value & Date)

    2. **Open Interest Data**:
       - Today's Open Interest
       - Put-Call Open Interest Ratio
       - Put Open Interest
       - Call Open Interest
       - 30-day Average Open Interest
       - Today's Open Interest vs 30-day Average (%)

    3. **Option Volume Data**:
       - Today's Volume
       - Put-Call Volume Ratio
       - Put Volume
       - Call Volume
       - 30-day Average Volume
       - Today's Volume as % of 30-day Average

    Ensure extracted values are correctly formatted as numbers where applicable.
    """

    # Run scraper and process JSON output
    result = Crawller.run(url, OptionChainData, instruction)
    print(f"Put/Call Ratios Data (raw): {result}")
    # Fallback: if result is a list, take the first dict or build a dict
    if isinstance(result, list):
        if len(result) > 0 and isinstance(result[0], dict):
            result = result[0]
        else:
            result = {}
    structured_result = result

    # Prepare output with error handling
    output = {}
    try:
        put_call_ratio = None
        if "put_call_volume_ratio" in structured_result and structured_result["put_call_volume_ratio"] is not None:
            put_call_ratio = structured_result["put_call_volume_ratio"]
        elif "put_call_open_interest_ratio" in structured_result and structured_result["put_call_open_interest_ratio"] is not None:
            put_call_ratio = structured_result["put_call_open_interest_ratio"]

        output["put_call_ratio"] = put_call_ratio
        output["put_call_ratio_insights"] = structured_result.get("option_overview", None)
    except Exception as e:
        output["put_call_ratio"] = None
        output["put_call_ratio_insights"] = None

    return output

def extract_buzzwords(news_articles, gpt_engine):
    """
    Extract trending buzzwords from news articles using GPTAnalysisEngine.
    Returns a list of buzzwords (strings).
    """
    try:
        buzzword_prompt = (
            "Given the following news articles, extract a concise list of 5-10 trending buzzwords or topics "
            "that are most relevant to the stock's current sentiment and discussion. "
            "Return only a JSON list of buzzwords."
        )
        buzzword_data = {"news_articles": news_articles}
        buzzword_resp = gpt_engine.generate_analysis(
            prompt=buzzword_prompt, data=buzzword_data, output_format="json"
        )
        buzzwords = json.loads(buzzword_resp)
        if isinstance(buzzwords, list):
            return buzzwords
        elif isinstance(buzzwords, dict) and "buzzwords" in buzzwords:
            return buzzwords["buzzwords"]
        return []
    except Exception:
        return []

def analyze_stock_sentiment(ticker: str):
    """
    Scrapes stock sentiment data from news sources, social media, sentiment tracking websites, 
    applies NLP sentiment analysis, and generates AI insights.

    Returns:
        dict: Structured JSON with sentiment analysis results, panic vs confidence scores, 
              trending topics, and a numeric social sentiment score.
    """
    import json
    import requests
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    from pydantic import BaseModel, Field
    from enterprise.financial_agent.tools.scrapers.crawl import CrawlScraper
    from enterprise.financial_agent.tools.gpt import GPTAnalysisEngine

    Crawller = CrawlScraper()
    analyzer = SentimentIntensityAnalyzer()
    gpt_engine = GPTAnalysisEngine()

    # News Sentiment
    class NewsSentiment(BaseModel):
        title: str = Field(..., description="Title of the news article.")
        summary: str = Field(..., description="Summary of the news article.")
        sentiment: str = Field(..., description="Sentiment classification (Positive, Neutral, Negative).")
        source: str = Field(..., description="Source of the news article (e.g., CNBC, Bloomberg).")
        url: str = Field(..., description="URL of the news article.")

    class NewsSentimentList(BaseModel):
        articles: list[NewsSentiment]

    google_news_url = f"https://news.google.com/search?q={ticker}"
    instruction_news = """Extract stock-related news articles:
    - Title
    - Summary
    - Source (CNBC, Bloomberg, MarketWatch, etc.)
    - URL
    - Apply sentiment analysis to classify each article as Positive, Neutral, or Negative."""
    news_results = Crawller.run(google_news_url, NewsSentimentList, instruction_news)
    news_results = json.loads(news_results) if isinstance(news_results, str) else news_results
    if not isinstance(news_results, list):
        news_results = [news_results]

    # Compute numeric news sentiment score (simple average of compound scores)
    news_sentiment_scores = []
    for article in news_results:
        text = f"{article.get('title','')} {article.get('summary','')}"
        score = analyzer.polarity_scores(text)["compound"]
        news_sentiment_scores.append(score)
    avg_news_sentiment = sum(news_sentiment_scores) / len(news_sentiment_scores) if news_sentiment_scores else 0

    # Investor Sentiment Tracking
    class Monthly_Trends_Dict(BaseModel):
        score: int
        month: str
        change: int

    class SentimentTracking(BaseModel):
        sentiment_score: int
        sentiment_status: str
        industry_percentile: int
        monthly_trends: list[Monthly_Trends_Dict]

    sentiment_tracking_url = f"https://altindex.com/ticker/{ticker}/sentiment"
    instruction_sentiment = """Extract the following investor sentiment data:
    - Overall sentiment score (0-100).
    - 30-day sentiment change.
    - Industry percentile ranking.
    - Month-over-month sentiment trend (last 6 months)."""
    sentiment_results = Crawller.run(sentiment_tracking_url, SentimentTracking, instruction_sentiment)
    sentiment_results = json.loads(sentiment_results) if isinstance(sentiment_results, str) else sentiment_results
    if isinstance(sentiment_results, list):
        sentiment_results = sentiment_results[0]

    # Panic vs Confidence Score
    class PanicConfidenceScore(BaseModel):
        score: int
        explanation: str

    panic_confidence_url = f"https://www.macroaxis.com/news/{ticker}"
    instruction_panic = """Extract:
    - Current Panic vs Confidence Score.
    - Explanation of why the score is at its current level.
    - Market conditions influencing investor behavior."""
    panic_confidence_results = Crawller.run(panic_confidence_url, PanicConfidenceScore, instruction_panic)
    panic_confidence_results = json.loads(panic_confidence_results) if isinstance(panic_confidence_results, str) else panic_confidence_results
    if isinstance(panic_confidence_results, list):
        if len(panic_confidence_results) > 0:
            panic_confidence_results = panic_confidence_results[0]
        else:
            panic_confidence_results = {}

    # Social Sentiment (news + investor + panic as proxy, or use GPT for a numeric score)
    social_sentiment_score = None
    try:
        social_sentiment_prompt = (
            f"Given the following data for stock {ticker}, provide a single numeric social sentiment score from -100 (very negative) to +100 (very positive). "
            "Consider news sentiment, investor sentiment, and panic vs confidence. Respond with a JSON object: {\"social_sentiment_score\": <number>}."
        )
        social_sentiment_data = {
            "news_sentiment_avg": avg_news_sentiment,
            "investor_sentiment_score": sentiment_results.get("sentiment_score") if sentiment_results else None,
            "panic_vs_confidence_score": panic_confidence_results.get("score") if panic_confidence_results else None
        }
        social_sentiment_resp = gpt_engine.generate_analysis(
            prompt=social_sentiment_prompt, data=social_sentiment_data, output_format="json"
        )
        social_sentiment_score = json.loads(social_sentiment_resp).get("social_sentiment_score")
    except Exception:
        social_sentiment_score = None

    # AI Insights
    ai_sentiment_insights = None
    try:
        ai_prompt = (
            f"Summarize the overall sentiment for stock {ticker} based on news, investor sentiment, and panic vs confidence. "
            "Highlight the main drivers and give a short actionable summary."
        )
        ai_sentiment_insights = gpt_engine.generate_analysis(
            prompt=ai_prompt,
            data={
                "news_sentiment": news_results,
                "investor_sentiment": sentiment_results,
                "panic_confidence": panic_confidence_results
            }
        )
    except Exception:
        ai_sentiment_insights = None

    # Trending buzzwords extraction
    try:
        news_articles_for_buzz = news_results[:5] if news_results else []
        trending_buzzwords = extract_buzzwords(news_articles_for_buzz, gpt_engine)
    except Exception:
        trending_buzzwords = []

    # Prepare final output with error handling and required fields
    try:
        # News articles: 3-5 articles
        news_articles = []
        if news_results:
            for article in news_results[:5]:
                news_articles.append({
                    "title": article.get("title"),
                    "summary": article.get("summary"),
                    "sentiment": article.get("sentiment"),
                    "source": article.get("source"),
                    "url": article.get("url")
                })
    except Exception:
        news_articles = []

    # Panic confidence: if score is 0 or missing, set to None and no explanation
    panic_confidence = None
    try:
        score = panic_confidence_results.get("score") if panic_confidence_results else None
        explanation = panic_confidence_results.get("explanation") if panic_confidence_results else None
        if score is not None and score != 0:
            panic_confidence = {
                "score": score,
                "explanation": explanation
            }
        else:
            panic_confidence = None
    except Exception:
        panic_confidence = None

    # Social sentiment: use industry_percentile from investor_sentiment
    try:
        industry_percentile = sentiment_results.get("industry_percentile") if sentiment_results else None
    except Exception:
        industry_percentile = None

    # Monthly trends
    try:
        monthly_trends = sentiment_results.get("monthly_trends") if sentiment_results else []
    except Exception:
        monthly_trends = []

    # Overall sentiment score and status
    try:
        overall_sentiment_score = sentiment_results.get("sentiment_score") if sentiment_results else None
        sentiment_status = sentiment_results.get("sentiment_status") if sentiment_results else None
    except Exception:
        overall_sentiment_score = None
        sentiment_status = None

    return {
        "ticker": ticker,
        "news_articles": news_articles,
        "overall_sentiment_score": overall_sentiment_score,
        "sentiment_status": sentiment_status,
        "social_sentiment": industry_percentile,
        "social_sentiment_score": social_sentiment_score,
        "monthly_trends": monthly_trends,
        "ai_sentiment_insights": ai_sentiment_insights,
        "panic_confidence": panic_confidence,
        "trending_buzzwords": trending_buzzwords
    }


def piotroski_score(ticker: str):
    from enterprise.financial_agent.tools.gpt import GPTAnalysisEngine
    from enterprise.financial_agent.tools.FinancialApi import FinancialModelingPrepAPI
    from enterprise.financial_agent.tools.helper_fns.allFns import get_fmp_detail

    gpt_engine = GPTAnalysisEngine()
    fmp = FinancialModelingPrepAPI()

    # 1. Try FMP API (if available)
    try:
        fmp_result = fmp.get_piotroski_score(ticker)
        if isinstance(fmp_result, list) and fmp_result and "score" in fmp_result[0]:
            return {"Piotroski_F_Score": fmp_result[0]["score"]}
        elif isinstance(fmp_result, dict) and "score" in fmp_result:
            return {"Piotroski_F_Score": fmp_result["score"]}
    except Exception:
        pass

    # 2. Try Google Search + GPT fallback
    try:
        from googlesearch import search
        query = f"{ticker} Piotroski F-Score analysis"
        urls = []
        for url in search(query, num_results=5, lang="en"):
            urls.append(url)
        summaries = []
        for url in urls:
            gpt_prompt = f"""
            Visit the following URL and summarize any information about the Piotroski F-Score for stock {ticker}.
            If the exact score is mentioned, extract it. If not, summarize any financial discussion that could help estimate the score.
            URL: {url}
            """
            try:
                summary = gpt_engine.generate_analysis(prompt=gpt_prompt)
                summaries.append(summary)
            except Exception:
                continue
        gpt_final_prompt = f"""
        Based on the following summaries from Google search results, estimate the Piotroski F-Score (0-9) for stock {ticker}.
        If the summaries do not mention the exact score, infer it from the financial discussion and fundamentals.
        Respond as a JSON object: {{"Piotroski_F_Score": <score as integer>}}.
        Summaries:
        {summaries}
        """
        gpt_result = gpt_engine.generate_analysis(prompt=gpt_final_prompt, output_format="json")
        score = json.loads(gpt_result)
        if "Piotroski_F_Score" in score and score["Piotroski_F_Score"] not in [None, 0]:
            return score
    except Exception:
        pass

    # 3. Fallback: Calculate from financials
    try:
        fmp_data = get_fmp_detail(ticker)
        income = fmp_data.get("income_statement", {})
        balance = fmp_data.get("balance_sheet", {})
        cash = fmp_data.get("cash_flow", {})
        if income and balance and cash:
            # Use GPT to calculate based on raw financials if you don't want to hardcode the logic:
            gpt_prompt = f"""
            Estimate the Piotroski F-Score (0-9) for stock {ticker} using the following financials.
            Respond as a JSON object: {{"Piotroski_F_Score": <score as integer>}}.
            Income Statement: {income}
            Balance Sheet: {balance}
            Cash Flow: {cash}
            If you cannot calculate, make a best guess based on profitability, leverage, and efficiency.
            """
            gpt_result = gpt_engine.generate_analysis(prompt=gpt_prompt, model="gpt-4.1",output_format="json")
            score = json.loads(gpt_result)
            if "Piotroski_F_Score" in score:
                return score
    except Exception:
        pass

    return {"Piotroski_F_Score": None}

def pe_ratios(ticker: str, sector: str = None):
    """
    Scrapes P/E ratios for a given stock from Yahoo Finance and compares it with sector & S&P 500 PE ratios.
    Returns a dict with only the required fields and robust error handling.
    """

    class StockPEData(BaseModel):
        pe_ratio: float = Field(..., description="Price-to-Earnings (P/E) ratio of the stock.")
        forward_pe_ratio: float = Field(..., description="Forward P/E ratio based on projected earnings.")
        peg_ratio: float = Field(..., description="Price/Earnings-to-Growth (PEG) ratio.")
        price_to_sales_ratio: float = Field(..., description="Price-to-Sales (P/S) ratio.")
        price_to_book_ratio: float = Field(..., description="Price-to-Book (P/B) ratio.")
        enterprise_value_ebitda: float = Field(..., description="Enterprise Value to EBITDA ratio.")

    class SectorPEData(BaseModel):
        sector: str = Field(..., description="Sector name for the stock.")
        sector_pe: float = Field(..., description="Current PE ratio of the stock's sector.")
        pe_5_year: float = Field(..., description="5-year average PE ratio for the sector.")
        pe_10_year: float = Field(..., description="10-year average PE ratio for the sector.")
        pe_20_year: float = Field(..., description="20-year average PE ratio for the sector.")
        sp500_pe: float = Field(..., description="Current PE ratio of the S&P 500 index.")

    Crawller = CrawlScraper()

    # STEP 1: SCRAPE STOCK P/E FROM YAHOO FINANCE
    yahoo_finance_url = f"https://finance.yahoo.com/quote/{ticker}/key-statistics/"
    instruction_stock_pe = f"""Extract the following valuation metrics for stock {ticker}:
    - Price-to-Earnings (P/E) Ratio
    - Forward P/E Ratio
    - Price/Earnings-to-Growth (PEG) Ratio
    - Price-to-Sales (P/S) Ratio
    - Price-to-Book (P/B) Ratio
    - Enterprise Value / EBITDA"""

    try:
        stock_pe_data = Crawller.run(yahoo_finance_url, StockPEData, instruction_stock_pe)
        stock_pe_data = json.loads(stock_pe_data) if isinstance(stock_pe_data, str) else stock_pe_data
        stock_pe_data = stock_pe_data[0] if isinstance(stock_pe_data, list) else stock_pe_data
    except Exception:
        stock_pe_data = {}

    # STEP 2: IF INDUSTRY IS NOT PROVIDED, PREDICT IT USING AI
    if not sector:
        try:
            gpt_engine = GPTAnalysisEngine()
            industry_prompt = f"""Predict the sector for stock {ticker} based on:
            - Stock name
            - Company description
            - Business model
            - Competitor analysis

            Return only the industry name."""
            sector = gpt_engine.generate_analysis(prompt=industry_prompt, data={"ticker": ticker}).get("industry", "Unknown")
        except Exception:
            sector = "Unknown"

    # STEP 3: SCRAPE INDUSTRY P/E FROM WORLD PE RATIO
    world_pe_url = f"https://worldperatio.com/sp-500-sectors/"
    instruction_sector_pe = f"""Extract the following P/E ratios for the {sector} sector:
    - Current Industry P/E
    - 5-year average P/E
    - 10-year average P/E
    - 20-year average P/E
    - Current S&P 500 P/E Ratio"""

    try:
        sector_pe_data = Crawller.run(world_pe_url, SectorPEData, instruction_sector_pe)
        sector_pe_data = json.loads(sector_pe_data) if isinstance(sector_pe_data, str) else sector_pe_data
        sector_pe_data = sector_pe_data[0] if isinstance(sector_pe_data, list) else sector_pe_data
    except Exception:
        sector_pe_data = {}

    # Extract values with error handling
    def safe_get(d, k):
        try:
            return d.get(k, None) if d else None
        except Exception:
            return None

    stock_pe = safe_get(stock_pe_data, 'pe_ratio')
    sector_pe = safe_get(sector_pe_data, 'sector_pe')
    sector_pe_5 = safe_get(sector_pe_data, 'pe_5_year')
    sector_pe_10 = safe_get(sector_pe_data, 'pe_10_year')
    sector_pe_20 = safe_get(sector_pe_data, 'pe_20_year')
    sp500_pe = safe_get(sector_pe_data, 'sp500_pe')

    # Helper for comparison
    def compare_pe(stock, sector):
        if stock is None or sector is None:
            return None
        if stock > sector * 1.1:
            return "overpriced"
        elif stock < sector * 0.9:
            return "undervalued"
        else:
            return "fair"

    def compare_sector_vs_sp(sector, sp):
        if sector is None or sp is None:
            return None
        if sector > sp * 1.1:
            return "expensive"
        elif sector < sp * 0.9:
            return "cheap"
        else:
            return "fair"

    # Prepare output
    result = {
        "sector": {
            "pe_5_year": sector_pe_5,
            "pe_10_year": sector_pe_10,
            "pe_20_year": sector_pe_20,
            "current_pe": sector_pe
        },
        "stock": {
            "pe_5_year": compare_pe(stock_pe, sector_pe_5),
            "pe_10_year": compare_pe(stock_pe, sector_pe_10),
            "pe_20_year": compare_pe(stock_pe, sector_pe_20),
            "current_pe": stock_pe
        },
        "sp500": {
            "pe": sp500_pe
        },
        "sector_vs_sp500": {
            "pe_5_year": compare_sector_vs_sp(sector_pe_5, sp500_pe),
            "pe_10_year": compare_sector_vs_sp(sector_pe_10, sp500_pe),
            "pe_20_year": compare_sector_vs_sp(sector_pe_20, sp500_pe),
            "current_pe": compare_sector_vs_sp(sector_pe, sp500_pe)
        }
    }
    return result


from pydantic import BaseModel, Field
from enterprise.financial_agent.tools.scrapers.crawl import CrawlScraper
from enterprise.financial_agent.tools.gpt import GPTAnalysisEngine

def debt_equity_ratio(statement: dict, company_profile: dict):
    """
    Retrieves the Debt-to-Equity (D/E) ratio from the company's balance sheet,
    identifies the company's industry, and scrapes the industry-average D/E ratio.

    Parameters:
    - `statement` (dict): Company's financial statement, including the balance sheet.
    - `company_profile` (dict): Contains company name, industry, and sector.

    Returns:
    - A dictionary containing:
    
      - Stock’s D/E Ratio
      - Industry D/E Ratio
      - Comparison insights
    """

    class IndustryDebtEquityData(BaseModel):
        industry_name: str = Field(..., description="Industry name from the FullRatio website.")
        avg_debt_equity_ratio: float = Field(..., description="Industry-average Debt-to-Equity (D/E) Ratio.")

    # **STEP 1: EXTRACT STOCK'S D/E RATIO FROM BALANCE SHEET**
    stock_de_ratio = statement.get("debtToEquity", None)
    
    if stock_de_ratio is None:
        return {"error": "Debt-to-Equity Ratio not found in the balance sheet data."}

    # **STEP 2: IDENTIFY COMPANY INDUSTRY**
    industry = company_profile.get("industry", None)

    if not industry:
        # Use AI to predict the industry if not explicitly provided
        gpt_engine = GPTAnalysisEngine()
        industry_prompt = f"""Predict the most relevant industry for the company based on:
        - Business description
        - Competitor analysis
        - Sector classification
        
        Return only the industry name."""
        
        industry = gpt_engine.generate_analysis(prompt=industry_prompt, data={"company_profile": company_profile}).get("industry", "Unknown")

    # **STEP 3: SCRAPE INDUSTRY-AVERAGE D/E RATIO FROM FULLRATIO**
    full_ratio_url = "https://fullratio.com/debt-to-equity-by-industry"
    instruction = f"""Extract the Debt-to-Equity Ratio for the {industry} industry or the closest related industry."""
    
    Crawller = CrawlScraper()
    industry_de_ratio_data = Crawller.run(full_ratio_url, IndustryDebtEquityData, instruction)
    industry_de_ratio_data = json.loads(industry_de_ratio_data) if isinstance(industry_de_ratio_data, str) else industry_de_ratio_data
    if isinstance(industry_de_ratio_data, list):
        industry_de_ratio_data = industry_de_ratio_data[0] if industry_de_ratio_data else {}
    elif not isinstance(industry_de_ratio_data, dict):
        industry_de_ratio_data = {}

    # **STEP 4: COMPARE STOCK VS. INDUSTRY D/E RATIO**
    industry_de_ratio = industry_de_ratio_data.get("avg_debt_equity_ratio", None)

    if industry_de_ratio is None:
        comparison = {
            "Industry Name": industry,
            "Stock Debt-to-Equity Ratio": stock_de_ratio,
            "Industry Average D/E Ratio": None,
            "Leverage Analysis": None,
            "Risk Assessment": None
        }
    comparison = {
        "Industry Name": industry,
        "Stock Debt-to-Equity Ratio": stock_de_ratio,
        "Industry Average D/E Ratio": industry_de_ratio,
        "Leverage Analysis": "Higher Leverage" if stock_de_ratio > industry_de_ratio else "Lower Leverage",
        "Risk Assessment": "Risky" if stock_de_ratio > (industry_de_ratio * 1.5) else "Moderate" if stock_de_ratio > industry_de_ratio else "Safe"
    }

    return {
        "Stock D/E Ratio": stock_de_ratio,
        "Industry D/E Ratio": industry_de_ratio,
        "Comparison": comparison
    }