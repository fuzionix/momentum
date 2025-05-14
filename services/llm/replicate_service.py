import os
import re
import replicate
from typing import Tuple, Dict, Any
from services.llm.prompts.prompt_stock_analysis import StockAnalysisPrompt

class ReplicateService:
    def __init__(self):
        self.client = replicate.Client(api_token=os.getenv('REPLICATE_API_TOKEN'))

    def get_financial_insight(self, stock_data: Dict) -> Tuple[str, str]:
        try:
            if 'error' in stock_data:
                return f'Error retrieving stock data: {stock_data["error"]}'
                                
            # Build prompt with stock data
            prompt = StockAnalysisPrompt.build_prompt(stock_data)

            prediction = self.client.predictions.create(
                'meta/llama-4-maverick-instruct',
                input={
                    'prompt': prompt,
                    'max_tokens': 4096,
                    'top_p': 0.9,
                    'temperature': 0.75,
                }
            )

            prediction.wait()

            if prediction.status == 'failed':
                return f'Error generating insight: {prediction.error}', 'error_id'
            
            prediction_id = prediction.id
            output = prediction.output

            # For streaming output, combine all output
            if isinstance(output, list):
                full_output = ''.join(output)
            else:
                full_output = str(output)

            # Remove <think> blocks
            cleaned_output = self.remove_think_blocks(full_output)

            # Sanitize for Telegram HTML parsing
            sanitized_output = self.sanitize_telegram_html(cleaned_output)

            return sanitized_output, prediction_id
        except Exception as e:
            return f'Error generating insight: {str(e)}', 'error_id'
    
    def remove_think_blocks(self, text: str) -> str:
        '''Remove content between <think> and </think> tags'''
        pattern = r'<think>.*?</think>'
        cleaned_text = re.sub(pattern, '', text, flags=re.DOTALL)
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        return cleaned_text.strip()
    
    def sanitize_telegram_html(self, text: str) -> str:
        '''Sanitize text for Telegram HTML parsing to prevent parsing issues with < and > characters'''
        # Replace standalone < symbols that might cause HTML parsing issues
        text = re.sub(r'<(\d|\s|\.)', r'&lt;\1', text)
        text = re.sub(r'(\d|\s)>', r'\1&gt;', text)
        
        # Handle comparison operators like <= and >=
        text = text.replace('<=', '&lt;=')
        text = text.replace('>=', '&gt;=')
        
        # Preserve legitimate HTML tags that Telegram supports
        # Telegram supports <b>, <strong>, <i>, <em>, <u>, <ins>, <s>, <strike>, <del>, <a>, <code>, <pre>
        allowed_tags = r'</?(?:b|strong|i|em|u|ins|s|strike|del|a|code|pre)(?:\s+[^>]*)?>'
        
        # Function to replace matches with placeholders
        def preserve_tag(match):
            return match.group(0)
        
        # Preserve allowed HTML tags
        text = re.sub(allowed_tags, preserve_tag, text, flags=re.IGNORECASE)
        
        return text
