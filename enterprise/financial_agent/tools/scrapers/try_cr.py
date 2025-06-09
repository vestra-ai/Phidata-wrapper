from pydantic import BaseModel, Field
from enterprise.financial_agent.tools.scrapers.crawl import CrawlScraper
# from enterprise.financial_agent import stock_bp


class OpenAIModelFee(BaseModel):
    model_name: str = Field(..., description="Name of the OpenAI model.")
    input_fee: str = Field(..., description="Fee for input token for the OpenAI model.")
    output_fee: str = Field(
        ..., description="Fee for output token for the OpenAI model."
    )
    
# @stock_bp.route('/try', methods=['GET'])
def try_crawling():
    Crawller = CrawlScraper()
    instruction = """From the crawled content, extract all mentioned model names along with their fees for input and output tokens. 
             Do not miss any models in the entire content."""
    result=Crawller.run("https://openai.com/api/pricing/", OpenAIModelFee,instruction )

    return(result)
# Crawller = CrawlScraper()
# instruction = """From the crawled content, extract all mentioned model names along with their fees for input and output tokens. 
#              Do not miss any models in the entire content."""
# result=Crawller.run("https://openai.com/api/pricing/", OpenAIModelFee,instruction )

# print(result)