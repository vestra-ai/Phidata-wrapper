from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.yfinance import YFinanceTools

# 🔹 Map tool names from JSON to actual PhiData tools
TOOL_MAPPING = {
    "DuckDuckGo": DuckDuckGo,
    "YFinanceTools": lambda: YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True),
}

def get_tool(tool_name):
    """Fetch the tool class from the mapping and return an instance."""
    if tool_name in TOOL_MAPPING:
        return TOOL_MAPPING[tool_name]()
    raise ValueError(f"Tool {tool_name} is not available.")

# from phi.tools.duckduckgo import DuckDuckGo
# from phi.tools.yfinance import YFinanceTools
# from phi.tools.wikipedia import Wikipedia
# from phi.tools.weather import Weather
# from phi.tools.openweathermap import OpenWeatherMap
# from phi.tools.wikipedia_summary import WikipediaSummary
# from phi.tools.translation import Translation
# from phi.tools.sentiment_analysis import SentimentAnalysis
# from phi.tools.image_generation import ImageGeneration
# from phi.tools.text_to_speech import TextToSpeech
# from phi.tools.speech_to_text import SpeechToText
# from phi.tools.currency_exchange import CurrencyExchange
# from phi.tools.pdf_reader import PDFReader
# from phi.tools.youtube_search import YouTubeSearch
# from phi.tools.wikipedia_advanced import WikipediaAdvanced
# from phi.tools.newsapi import NewsAPI
# from phi.tools.github_trending import GitHubTrending
# from phi.tools.crypto_prices import CryptoPrices
# from phi.tools.stock_market_news import StockMarketNews
# from phi.tools.wikipedia_image import WikipediaImage

# # 🔹 Map tool names from JSON to actual PhiData tools
# TOOL_MAPPING = {
#     "DuckDuckGo": DuckDuckGo,
#     "YFinanceTools": lambda: YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True),
#     "Wikipedia": Wikipedia,
#     "Weather": Weather,
#     "OpenWeatherMap": OpenWeatherMap,
#     "WikipediaSummary": WikipediaSummary,
#     "Translation": Translation,
#     "SentimentAnalysis": SentimentAnalysis,
#     "ImageGeneration": ImageGeneration,
#     "TextToSpeech": TextToSpeech,
#     "SpeechToText": SpeechToText,
#     "CurrencyExchange": CurrencyExchange,
#     "PDFReader": PDFReader,
#     "YouTubeSearch": YouTubeSearch,
#     "WikipediaAdvanced": WikipediaAdvanced,
#     "NewsAPI": NewsAPI,
#     "GitHubTrending": GitHubTrending,
#     "CryptoPrices": CryptoPrices,
#     "StockMarketNews": StockMarketNews,
#     "WikipediaImage": WikipediaImage,
# }

# def get_tool(tool_name):
#     """Fetch the tool class from the mapping and return an instance."""
#     if tool_name in TOOL_MAPPING:
#         return TOOL_MAPPING[tool_name]()
#     raise ValueError(f"Tool {tool_name} is not available.")
