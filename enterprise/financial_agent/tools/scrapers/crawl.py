import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
import os
import asyncio
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy

class CrawlScraper:
    def __init__(self, provider: str="openai/gpt-4o", api_token: str =os.getenv("OPENAI_API_KEY"), extra_headers: dict[str, str] = None):
            self.provider = provider
            self.api_token = api_token 
            self.extra_headers = extra_headers

    async def scrape(self, url: str, schema: dict, instruction: str):
            if self.api_token is None and self.provider != "ollama":
                raise ValueError(f"API token is required for {self.provider}.")

            browser_config = BrowserConfig(headless=True)
            extra_args = {"temperature": 0, "top_p": 0.9, "max_tokens": 2000}
            if self.extra_headers:
                extra_args["extra_headers"] = self.extra_headers

            try:
                llm_config = LLMConfig(
                provider=self.provider,
                api_token=self.api_token
                )
                crawler_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                word_count_threshold=1,
                page_timeout=80000,
                extraction_strategy=LLMExtractionStrategy(
                    llm_config=llm_config,
                    schema=schema,
                    extraction_type="schema",
                    instruction=instruction,
                    extra_args=extra_args,
                ),
                )

                async with AsyncWebCrawler(config=browser_config) as crawler:
                    result = await crawler.arun(url=url, config=crawler_config)
                    return result.extracted_content
            except Exception as e:
                print(f"Error configuring or running crawler: {e}")
                return None

    def run(self, url: str, schema_class: BaseModel, instruction: str):
            schema = schema_class.model_json_schema()
            return asyncio.run(self.scrape(url, schema, instruction))
