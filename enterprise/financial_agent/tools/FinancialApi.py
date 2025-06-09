import requests
import json
import os

class FinancialModelingPrepAPI:
    """
    Python wrapper for Financial Modeling Prep (FMP) API.
    """
    BASE_URL = "https://financialmodelingprep.com/api/v3"
    BASE_URL_V4 = "https://financialmodelingprep.com/api/v4"

    def __init__(self):
        """Initialize with API key from environment variable or parameter."""
        self.api_key = os.getenv('FMP_API_KEY')
        if not self.api_key:
            raise ValueError("API key must be provided")

    def _make_request(self, endpoint: str, params: dict = {}, version: str = "v3") -> dict:
        base_url = self.BASE_URL if version == "v3" else self.BASE_URL_V4
        url = f"{base_url}/{endpoint}"
        params["apikey"] = self.api_key
        response = requests.get(url, params=params)
        return response.json()

    # ✅ Company Data
    def get_company_profile(self, symbol: str) -> dict:
        return self._make_request(f"profile/{symbol}")

    def get_competitors(self, symbol: str) -> dict:
        return self._make_request(f"stock_peers?symbol={symbol}", version="v4")

    def get_stock_peers(self, symbol: str) -> dict:
        return self._make_request(f"stock_peers?symbol={symbol}", version="v4")

    def get_insider_trading(self, symbol: str) -> dict:
        return self._make_request(f"insider-trading?symbol={symbol}", version="v4")

    # ✅ Stock Market Data
    def get_historical_stock_data(self, symbol: str) -> dict:
        return self._make_request(f"historical-price-full/{symbol}")

    def get_real_time_price(self, symbol: str) -> dict:
        return self._make_request(f"quote/{symbol}")

    def get_market_indices(self) -> dict:
        return self._make_request(f"quotes/%5EDJBGIE")

    # ✅ Financial Statements
    def get_income_statement(self, symbol: str) -> dict:
        return self._make_request(f"income-statement/{symbol}")

    def get_balance_sheet(self, symbol: str) -> dict:
        return self._make_request(f"balance-sheet-statement/{symbol}")

    def get_cash_flow_statement(self, symbol: str) -> dict:
        return self._make_request(f"cash-flow-statement/{symbol}")

    # ✅ Earnings & Dividends
    def get_earnings_reports(self, symbol: str) -> dict:
        return self._make_request(f"historical/earning_calendar/{symbol}")
    # https://financialmodelingprep.com/api/v3/historical/earning_calendar/AAPL

    def get_dividend_history(self, symbol: str) -> dict:
        return self._make_request(f"historical-price-full/stock_dividend/{symbol}")

    # ✅ SEC Filings & Analysis
    def get_sec_filings(self, symbol: str) -> dict:
        return self._make_request(f"sec_filings/{symbol}")

    def get_statement_analysis(self, symbol: str) -> dict:
        return self._make_request(f"ratios/{symbol}")

    # ✅ Analyst Ratings & Price Targets
    def get_analyst_ratings(self, symbol: str) -> dict:
        return self._make_request(f"rating/{symbol}")

    def get_price_targets(self, symbol: str) -> dict:
        return self._make_request(f"price-target?symbol={symbol}", version="v4")

    # # ✅ Market Sentiment
    # def get_fear_greed_index(self) -> dict:
    #     return self._make_request("fear-and-greed-index")
    # ratios/{symbol}

    # def get_put_call_ratio(self) -> dict:
    #     return self._make_request("put-call-ratio")
    # ratios/{symbol}

    # ✅ Valuation Metrics
    def get_fair_value(self, symbol: str) -> dict:
        return self._make_request(f"discounted-cash-flow/{symbol}")
    
    # https://financialmodelingprep.com/api/v3/quote/AAPL

    def get_pe_ratio(self, symbol: str) -> dict:
        return self._make_request(f"ratios-ttm/{symbol}")

    # Add new methods for forecasts
    def get_forecast(self, symbol: str) -> dict:
        return self._make_request(f"analyst-estimates/{symbol}")

    # ✅ EPS Data
    # def get_eps_history(self, symbol: str) -> dict:
    #     """Fetch historical EPS data (earning surprises)."""
    #     return self._make_request(f"historical/earning_surprises/{symbol}")

    # def get_eps_estimates(self, symbol: str) -> dict:
    #     """Fetch EPS forecast by analysts."""
    #     return self._make_request(f"analyst-estimates/{symbol}")

    # ✅ Additional Endpoints
    def get_revenue_product_segmentation(self, symbol: str) -> dict:
        return self._make_request(f"revenue-product-segmentation?symbol={symbol}", version="v4")

    def get_key_metrics(self, symbol: str) -> dict:
        return self._make_request(f"key-metrics/{symbol}")

    def get_piotroski_score(self, symbol: str) -> dict:
        return self._make_request(f"score?symbol={symbol}", version="v4")

    def get_stock_news(self, symbol: str) -> dict:
        return self._make_request(f"stock_news/{symbol}")


# def main():
#     fmp = FinancialModelingPrepAPI()

#     data = {
#         "company_profile": fmp.get_company_profile("AAPL"),
#         "competitors": fmp.get_competitors("AAPL"),
#         "insider_trading": fmp.get_insider_trading("AAPL"),
#         "historical_stock_data": fmp.get_historical_stock_data("AAPL"),
#         "real_time_price": fmp.get_real_time_price("AAPL"),
#         "market_indices": fmp.get_market_indices(),
#         "income_statement": fmp.get_income_statement("AAPL"),
#         "balance_sheet": fmp.get_balance_sheet("AAPL"),
#         "cash_flow_statement": fmp.get_cash_flow_statement("AAPL"),
#         "earnings_reports": fmp.get_earnings_reports("AAPL"),
#         "dividend_history": fmp.get_dividend_history("AAPL"),
#         "sec_filings": fmp.get_sec_filings("AAPL"),
#         "statement_analysis": fmp.get_statement_analysis("AAPL"),
#         "analyst_ratings": fmp.get_analyst_ratings("AAPL"),
#         "price_targets": fmp.get_price_targets("AAPL"),
#         # "fear_greed_index": fmp.get_fear_greed_index(),
#         # "put_call_ratio": fmp.get_put_call_ratio(),
#         "fair_value": fmp.get_fair_value("AAPL"),
#         "pe_ratio": fmp.get_pe_ratio("AAPL"),
#         "forecast": fmp.get_forecast("AAPL"),
#         # "eps_history": fmp.get_eps_history("AAPL"),
#         # "eps_estimates": fmp.get_eps_estimates("AAPL"),
#         "revenue_product_segmentation": fmp.get_revenue_product_segmentation("AAPL"),
#         "key_metrics": fmp.get_key_metrics("AAPL"),
#         "piotroski_score": fmp.get_piotroski_score("AAPL"),
#         "stock_news": fmp.get_stock_news("AAPL")
#     }

#     with open("financial_data_4.json", "w") as json_file:
#         json.dump(data, json_file, indent=4)
#         print("Data saved to financial_data_4.json")

# if __name__ == "__main__":
#     main()
