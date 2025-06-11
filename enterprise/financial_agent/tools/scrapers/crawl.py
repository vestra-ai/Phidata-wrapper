import os
from firecrawl import FirecrawlApp, JsonConfig
from pydantic import BaseModel

from enterprise.financial_agent.tools.gpt import GPTAnalysisEngine

class CrawlScraper:
    def __init__(self, api_key: str = os.getenv("FIRECRAWL_API_KEY"), extra_headers: dict[str, str] = None):
        self.api_key = api_key
        self.extra_headers = extra_headers
        self.app = FirecrawlApp(api_key=self.api_key)
    
    def format_json_with_schema(self, json_data: dict, schema: dict):
        """
        Format the JSON data according to the provided schema.
        """
        import json

        prompt = (
            "You are an expert data formatter and validator. "
            "Your task is to take the provided JSON data and transform it so that it strictly matches the given schema. "
            "Ensure that:\n"
            "- All required fields in the schema are present in the output.\n"
            "- The data types of each field match the schema (e.g., string, integer, boolean, array, object).\n"
            "- If a field is missing in the input but required by the schema, fill it with null if appropriate.\n"
            "- Remove any fields from the input data that are not defined in the schema.\n"
            "- If the schema specifies nested objects or arrays, ensure the structure and types are correct.\n"
            "- Do not include any explanations or extra text, only return the formatted JSON object.\n\n"
            f"Schema (in JSON Schema format):\n{schema}\n\n"
            f"Input Data:\n{json_data}\n\n"
            "Return ONLY the formatted JSON object that matches the schema."
        )

        try:
            gpt_engine = GPTAnalysisEngine()
            output_data = gpt_engine.generate_analysis(prompt, output_format="json")
            output_data = json.loads(output_data)
            return output_data
        except Exception as e:
            print(f"Error formatting JSON with schema: {e}")
            return json_data

    def scrape(self, url: str, schema: dict, instruction: str):
        json_config = JsonConfig(
            extractionSchema=schema,
            mode="llm-extraction",
            pageOptions={"onlyMainContent": True},
            prompt=instruction
        )
        try:
            result = self.app.scrape_url(
                url,
                formats=["json"],
                json_options=json_config
            )
            if result.json:
                print("Data extracted successfully.")
                # Pass the extracted JSON and schema to GPT engine for formatting/validation
                try:
                    formatted_json = self.format_json_with_schema(result.json, schema)
                    return formatted_json
                except Exception as gpt_error:
                    print(f"GPT engine error: {gpt_error}")
                    return result.json
            
            if result.error:
                print("Error extracting data:", result.error)
                if result.json:
                    return result.json
                return None
        except Exception as e:
            print(f"Error running Firecrawl: {e}")
            return None

    def run(self, url: str, schema_class: BaseModel, instruction: str):
        schema = schema_class.model_json_schema()
        return self.scrape(url, schema, instruction)

