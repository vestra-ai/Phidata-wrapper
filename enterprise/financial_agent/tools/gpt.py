from enum import Enum
from typing import Optional, Dict, Any
import os
import openai
from openai import OpenAI

class GPTAnalysisEngine:
    def __init__(self, default_model: str = "gpt-4o"):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.client = OpenAI(api_key=self.api_key)
        self.default_model = default_model
        
    def generate_analysis(
        self,
        prompt: str,
        data: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        output_format: Optional[str] = None,
        max_tokens: int = 3000
    ) -> str:
        """
        Generate GPT analysis based on prompt and data.
        
        Args:
            prompt: The input prompt for analysis
            data: Optional additional data to include
            model: GPT model to use (defaults to instance default_model)
            max_tokens: Maximum tokens in response
            
        Returns:
            str: Generated analysis response
        """
        analysis_prompt = self._prepare_prompt(prompt, data)

        if output_format=="json":
            response = self.client.chat.completions.create(
            model=model or self.default_model,
            messages=[
                {"role": "user", "content": analysis_prompt}
            ],
            max_tokens=max_tokens,
            response_format={"type":"json_object"}
            )
        else:
            response = self.client.chat.completions.create(
            model=model or self.default_model,
            messages=[
                {"role": "user", "content": analysis_prompt}
            ],
            max_tokens=max_tokens,
            )      

        
        return response.choices[0].message.content
    
    def _prepare_prompt(self, prompt: str, data: Optional[Dict[str, Any]] = None) -> str:
        """Prepare the final prompt by combining the input prompt and data"""
        if data:
            return f"{prompt}\n\nContext:\n{data}"
        return prompt
